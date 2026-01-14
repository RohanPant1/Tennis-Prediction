from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import xgboost as xgb
import pandas as pd
# Import your existing logic from your project files
from predict_stats import predict_matchup

app = FastAPI()

# Enable CORS for your React frontend (usually port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model once at startup
model = xgb.Booster()
model.load_model("tennis_model.json")
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
    # 1. Convert request to model features using your existing code
    features = get_matchup_features(
        match.p1, match.p2, match.target_date, 
        match.surface, match.draw_size, match.best_of, 
        match.tourney_level, match.round_idx, df_stats
    )
    
    # 2. Run Inference
    dmat = xgb.DMatrix(features)
    prob = model.predict(dmat)[0] # Assuming binary classification
    
    winner = match.p1 if prob > 0.5 else match.p2
    confidence = float(prob if prob > 0.5 else 1 - prob)

    return {
        "winner": winner,
        "probability": round(confidence * 100, 2)
    }