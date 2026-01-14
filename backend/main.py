from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import xgboost as xgb
import pandas as pd
import joblib
from predict_stats import predict_matchup

app = FastAPI()

best_model = joblib.load('tennis_prediction_pipeline.joblib')

# Enable CORS for your React frontend (usually port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
df_stats = pd.read_csv("atp_matches_feature_add.csv")

class MatchRequest(BaseModel):
    p1: str
    p2: str
    target_date: str
    surface: str
    draw_size: int
    best_of: int
    tourney_level: str
    round_idx: int

@app.post("/predict")
async def predict(match: MatchRequest):
    # Call your notebook's logic
    result = predict_matchup(
        match.p1, match.p2, match.target_date, 
        match.surface, match.draw_size, match.best_of, 
        match.tourney_level, match.round_idx, df_stats, best_model
    )
    
    if result is None:
        return {"error": f"Could not build features for {match.p1} or {match.p2}."}
    
    # FIX: Convert NumPy float32 to standard Python floats so they can be JSON-serialized.
    # We also exclude the 'features' DataFrame because it's too complex for a basic JSON response.
    return {
        "winner": result['winner'],
        "p1_prob": float(result['p1_prob']), 
        "p2_prob": float(result['p2_prob'])
    }