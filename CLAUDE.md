# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack app that predicts ATP tennis match outcomes. A FastAPI backend serves predictions from a trained XGBoost model (via a joblib pipeline) to a React/Vite frontend. All ML code, notebooks, and data live under `backend/` and `data/`.

## Common Commands

**Backend** (from `backend/`):
```bash
pip install -r requirements.txt
uvicorn main:app --reload   # serves http://localhost:8000
```

**Frontend** (from `frontend/`):
```bash
npm install
npm run dev       # http://localhost:5173
npm run build
npm run lint
```

There is no automated test suite in this repo (no pytest/unit tests) — verify backend changes by running the server and calling `POST /predict`, and verify model changes by re-running the relevant notebook end-to-end.

## Architecture

### Data pipeline (backend/, run in this order)

Each stage is a Jupyter notebook that reads the previous stage's CSV and writes a new one. **They must be re-run in sequence** if upstream logic changes — there is no single pipeline script.

1. **`data_clean.ipynb`** — reads `atp_matches_git.csv` (main tour) + `atp_qual.csv` (qualifying/challenger), concatenates, coerces numeric columns, fills missing rank/age/height/serve-stat values, normalizes `surface` (`Carpet` → `Hard`). Writes `atp_matches_data_cleaned.csv`.
2. **`feature_add.ipynb`** (logic mirrored in `function_add.py`) — computes, match by match in chronological order:
   - Elo ratings: overall **match Elo**, plus **serve/return Elo**, each with a global rating and a surface-blended rating (shrunk toward global by sample count), decayed toward the 1500 baseline between matches using a 365-day half-life.
   - Rolling 52-week serve/return rate stats (ace rate, double-fault rate, 1st-in %, 1st/2nd-serve-won %, break-point saved/converted %), shrunk toward tour-average priors (`PRIORS` dict) by sample size.
   - Career/surface match counts and head-to-head win differential, all computed **pre-match** (no leakage from the match being predicted).
   Writes `atp_matches_feature_add.csv`.
3. **`feature_engineer.ipynb`** — drops retirement/walkover/default matches and all of 2017, keeps only `rel_*` (winner − loser) difference features plus context columns (`surface`, `tourney_level`, `draw_size`, `round`, `best_of`), one-hot encodes categoricals, and **builds a symmetric training target**: for a random 50% of rows it negates every `rel_*` column and flips `target` to 0, so the model learns a direction-agnostic "player A vs player B" relationship instead of always predicting "the winner." Writes `atp_matches_feature_engineer.csv`.
4. **`model.ipynb`** — trains an `XGBClassifier` inside a `Pipeline`, tuned with `RandomizedSearchCV` over `TimeSeriesSplit` (chronological CV, since this is match-outcome data), scored on ROC-AUC. Saves the fitted pipeline to `tennis_prediction_pipeline.joblib`.

`predict_stats.ipynb` / `tennis.ipynb` are exploratory notebooks for the same logic.

### Inference path (must stay schema-compatible with training)

- **`predict_stats.py`** reimplements the feature-construction logic from `function_add.py`/`feature_engineer.ipynb` for a *live* matchup: given a player name and a `target_date`, it walks that player's match history in `atp_matches_feature_add.csv` to find their pre-match Elo/rolling stats at (or decayed forward to) that date, then assembles the same `rel_*`/one-hot feature vector the model was trained on. The `ordered_columns` list in `get_matchup_features()` **must exactly match the training feature schema** — if the feature-engineering notebooks change columns, this list and the one-hot branches above it need matching updates.
- **`main.py`** is the FastAPI app: loads `tennis_prediction_pipeline.joblib` and `atp_matches_feature_add.csv` once at startup, exposes a single `POST /predict` endpoint (`MatchRequest` → winner + win probabilities), and restricts CORS to `http://localhost:5173`.
- **`frontend/src/App.jsx`** is a single-component React app (no routing/state library) that posts match parameters to `http://localhost:8000/predict` via axios and renders the winner/probabilities.

### Data sources

- `data/` holds raw yearly ATP match CSVs (main tour + qualifying/challenger, 2017–2026), which feed into `backend/atp_matches_git.csv` and `backend/atp_qual.csv`.
- `backend/tournament_ids.py` is a standalone scraper (requests + BeautifulSoup) that pulls tournament IDs from the ATP Tour results archive — unrelated to the prediction pipeline itself.
- `atp_scraper/` is a **Python virtualenv** (fully gitignored), not a source directory — ignore its contents.

### Key invariant

Any change to the feature set (new/renamed/reordered columns) has a **three-way dependency**: `feature_add.ipynb`/`function_add.py` (feature computation) → `feature_engineer.ipynb` (column selection/encoding, must match `keep_cols`) → `predict_stats.py`'s `ordered_columns` (must match what the saved model was trained on). Changing one without the others will silently break inference or retrain a model on a different schema than production expects.
