import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
from predict_stats import predict_matchup, get_feature_contributions, get_matchup_context

app = FastAPI()

best_model = joblib.load('tennis_prediction_pipeline.joblib')

# Origins are comma-separated in the ALLOWED_ORIGINS env var (set this to your
# deployed frontend URL, e.g. https://your-app.vercel.app). Falls back to the
# local Vite dev server so `npm run dev` keeps working untouched.
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
df_stats = pd.read_csv("atp_matches_feature_add.csv")
# match_date is stored as a raw YYYYMMDD number (e.g. 20250529.0), not a date string.
# Parsing it without an explicit format makes pandas read it as nanoseconds-since-epoch
# (landing near 1970), which silently breaks every date comparison predict_stats.py does
# against it (players' Elo decaying to the 1500 baseline on every request). Parse it once,
# correctly, here -- every downstream pd.to_datetime() call on an already-datetime column
# is a harmless no-op.
df_stats['match_date'] = pd.to_datetime(df_stats['match_date'], format='%Y%m%d')
player_names = sorted(pd.unique(pd.concat([df_stats['winner_name'], df_stats['loser_name']])).tolist())

class MatchRequest(BaseModel):
    p1: str
    p2: str
    target_date: str
    surface: str
    draw_size: int
    best_of: int
    tourney_level: str
    round_idx: int

@app.get("/players")
async def get_players():
    return {"players": player_names}

@app.post("/predict")
async def predict(match: MatchRequest):
    # Call your notebook's logic
    try:
        result = predict_matchup(
            match.p1, match.p2, match.target_date,
            match.surface, match.draw_size, match.best_of,
            match.tourney_level, match.round_idx, df_stats, best_model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    if result is None:
        raise HTTPException(
            status_code=422,
            detail=f"Could not find enough match history for '{match.p1}' or '{match.p2}'. Try picking a name from the player list."
        )

    try:
        contributions = get_feature_contributions(best_model, result['features'], match.p1, match.p2)
    except Exception:
        contributions = None

    try:
        raw_context = get_matchup_context(match.p1, match.p2, match.target_date, match.surface, df_stats)
        context = {
            "p1": _serialize_player_context(raw_context['p1']),
            "p2": _serialize_player_context(raw_context['p2']),
            "h2h": raw_context['h2h'],
        }
    except Exception:
        context = None

    # FIX: Convert NumPy float32 to standard Python floats so they can be JSON-serialized.
    return {
        "winner": result['winner'],
        "p1_prob": float(result['p1_prob']),
        "p2_prob": float(result['p2_prob']),
        "contributions": contributions,
        "context": context,
    }


def _serialize_player_context(player_ctx):
    return {
        "surface_elo": float(player_ctx['surface_elo']) if player_ctx['surface_elo'] is not None else None,
        "surface_elo_is_fallback": player_ctx['surface_elo_is_fallback'],
        "recent_form": player_ctx['recent_form'],
    }