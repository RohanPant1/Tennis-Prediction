# 🎾 ATP Tennis Match Predictor

A full-stack app that predicts the outcome of ATP tennis matches using a machine learning model trained on historical match data.

**Live app:** https://rohanpant1.github.io/Tennis-Prediction/


---

## What it does

Give it two player names and match context (surface, tournament level, round, best-of), and it returns a predicted winner with win probabilities for each player — based on pre-match Elo ratings, rolling serve/return stats, and head-to-head history, fed into a trained XGBoost classifier.

## How it works

```
React frontend  →  FastAPI backend  →  XGBoost pipeline (joblib)
(GitHub Pages)     (Azure App Service)   trained on ATP match history
```

1. The frontend collects the matchup details and posts them to the backend's `/predict` endpoint.
2. The backend walks each player's match history to compute their *pre-match* Elo ratings and rolling stats as of the target date — the same feature logic used during training, reimplemented for a live single matchup.
3. Those features go through the trained scikit-learn `Pipeline` (XGBoost classifier) to produce a win probability, plus a breakdown of which features drove the prediction.

## Tech stack

**Frontend** — React 19, Vite, Tailwind CSS, Axios
**Backend** — FastAPI, Uvicorn, Pandas, NumPy, scikit-learn, XGBoost (+ CatBoost/LightGBM used during model experimentation)
**ML / data pipeline** — Jupyter notebooks, chronological Elo-rating system, `RandomizedSearchCV` with `TimeSeriesSplit` cross-validation
**Deployment** — Azure App Service (backend), GitHub Pages (frontend), GitHub Actions (CI/CD for the frontend build)

## How the model was built

The pipeline runs as a sequence of notebooks in `backend/pipeline/`, each reading the previous stage's output:

1. **`data_clean.ipynb`** — merges main-tour and qualifying/challenger match data, coerces types, fills missing values, normalizes surfaces.
2. **`feature_add.ipynb`** — computes, match-by-match in chronological order: Elo ratings (overall + serve/return, global and surface-blended, with time-decay), rolling 52-week serve/return stats shrunk toward tour-average priors, and head-to-head/career-count features — all calculated *before* each match to avoid leakage.
3. **`feature_engineer.ipynb`** — selects and encodes final features, and builds a symmetric training target (randomly flips winner/loser framing for half the rows) so the model learns "player A vs player B," not just "predict the winner."
4. **`model.ipynb`** — trains an XGBoost classifier inside a `Pipeline`, tuned via `RandomizedSearchCV` over `TimeSeriesSplit`, scored on ROC-AUC. The fitted pipeline is saved as `tennis_prediction_pipeline.joblib`.

## Deployment

- **Backend** runs on Azure App Service (Linux, Python 3.12, F1 free tier), deployed via `az webapp up` from `backend/`. CORS-allowed origins are set via the `ALLOWED_ORIGINS` app setting.
- **Frontend** is built and deployed automatically to GitHub Pages by a GitHub Actions workflow (`.github/workflows/deploy-pages.yml`) on every push to `main`. The backend URL is injected at build time via the `VITE_API_URL` repository variable.
- **Keep-alive**: the F1 tier doesn't support Always On, so `.github/workflows/keep-alive.yml` pings `GET /health` every 10 minutes to stop the app from idling out and cold-starting. Only fires on the default branch and stops firing automatically if the repo goes 60+ days without a commit (a GitHub Actions limitation, not something this workflow controls).

## Project structure

```
backend/
  app/            FastAPI serving code (main.py, predict_stats.py)
  pipeline/       Data pipeline notebooks + function_add.py
  artifacts/      Generated CSVs + trained joblib model
  scraper/        Standalone ATP tournament-ID scraper (unrelated to prediction)
frontend/
  src/            React components, API client
data/             Raw yearly ATP match CSVs (feeds backend/artifacts/)
```
