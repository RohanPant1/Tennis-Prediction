# %%
import pandas as pd
import math
from collections import defaultdict
import matplotlib.pyplot as plt
from datetime import timedelta
import numpy as np

df = pd.read_csv("atp_matches_data_cleaned.csv")
print(len(df))
print(df["score"].isna())
print(type(df.iloc[0]["tourney_date"]))


# %%
print(df["score"].isna().sum())
df["retired"] = df["score"].str.contains("RET|W|DEF", regex=True).astype(int)
df["tourney_date"] = pd.to_datetime(
    df["tourney_date"],
    format="%Y%m%d",
    errors="coerce"
)
print(df["tourney_date"])

# %%
# ---------------------------
# Elo parameters
# ---------------------------
START_ELO = 1500.0

# Match Elo
K_MATCH_BO3 = 32
K_MATCH_BO5 = 40

# Serve / Return Elo
K_SR = 20.0

# 52-week decay
HALF_LIFE_DAYS = 365.0
TAU = HALF_LIFE_DAYS / math.log(2)

# Surface blending
SURFACE_BLEND_C = 30.0   # shrinkage constant
SURFACES = {"Hard", "Clay", "Grass"}



# %%
def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** (-(ra - rb) / 400))

def decay(r, days):
    if days <= 0:
        return r
    return START_ELO + (r - START_ELO) * math.exp(-days / TAU)

def weight_svpt(svpt):
    return min(math.sqrt(svpt / 100.0), 1.5) if svpt > 0 else 0.0

def blend(global_r, surf_r, n, c=SURFACE_BLEND_C):
    if n <= 0:
        return global_r
    a = n / (n + c)
    return (1 - a) * global_r + a * surf_r


# %%
# -------------------------
# STATE
# -------------------------
match_global = defaultdict(lambda: START_ELO)
match_surface = {s: defaultdict(lambda: START_ELO) for s in SURFACES}
match_surface_n = {s: defaultdict(int) for s in SURFACES}

serve_global = defaultdict(lambda: START_ELO)
return_global = defaultdict(lambda: START_ELO)
serve_surface = {s: defaultdict(lambda: START_ELO) for s in SURFACES}
return_surface = {s: defaultdict(lambda: START_ELO) for s in SURFACES}
sr_surface_n = {s: defaultdict(int) for s in SURFACES}

last_played = {}

# -------------------------
# OUTPUT COLS
# -------------------------
out = {
    "w_match_elo_pre": [],
    "l_match_elo_pre": [],
    "w_serve_elo_pre": [],
    "l_serve_elo_pre": [],
    "w_return_elo_pre": [],
    "l_return_elo_pre": [],
}



# %%
# -------------------------
# MAIN LOOP
# -------------------------
for _, r in df.iterrows():
    w, l = r["winner_name"], r["loser_name"]
    d = r["tourney_date"]
    s = r["surface"]
    bo = int(r["best_of"])

    # ---- DECAY ----
    for p in (w, l):
        if p in last_played:
            days = (d - last_played[p]).days
            match_global[p] = decay(match_global[p], days)
            serve_global[p] = decay(serve_global[p], days)
            return_global[p] = decay(return_global[p], days)
            if s in SURFACES:
                match_surface[s][p] = decay(match_surface[s][p], days)
                serve_surface[s][p] = decay(serve_surface[s][p], days)
                return_surface[s][p] = decay(return_surface[s][p], days)

    # ---- PRE-MATCH BLENDED ----
    if s in SURFACES:
        w_match = blend(match_global[w], match_surface[s][w], match_surface_n[s][w])
        l_match = blend(match_global[l], match_surface[s][l], match_surface_n[s][l])

        w_serve = blend(serve_global[w], serve_surface[s][w], sr_surface_n[s][w])
        l_serve = blend(serve_global[l], serve_surface[s][l], sr_surface_n[s][l])

        w_return = blend(return_global[w], return_surface[s][w], sr_surface_n[s][w])
        l_return = blend(return_global[l], return_surface[s][l], sr_surface_n[s][l])
    else:
        w_match, l_match = match_global[w], match_global[l]
        w_serve, l_serve = serve_global[w], serve_global[l]
        w_return, l_return = return_global[w], return_global[l]

    out["w_match_elo_pre"].append(w_match)
    out["l_match_elo_pre"].append(l_match)
    out["w_serve_elo_pre"].append(w_serve)
    out["l_serve_elo_pre"].append(l_serve)
    out["w_return_elo_pre"].append(w_return)
    out["l_return_elo_pre"].append(l_return)

    # -------------------------
    # UPDATE MATCH ELO
    # -------------------------
    K = K_MATCH_BO5 if bo == 5 else K_MATCH_BO3
    p_win = expected(match_global[w], match_global[l])
    delta = K * (1 - p_win)

    match_global[w] += delta
    match_global[l] -= delta

    if s in SURFACES:
        p_surf = expected(match_surface[s][w], match_surface[s][l])
        delta_s = K * (1 - p_surf)
        match_surface[s][w] += delta_s
        match_surface[s][l] -= delta_s
        match_surface_n[s][w] += 1
        match_surface_n[s][l] += 1

    # -------------------------
    # UPDATE SERVE / RETURN ELO
    # -------------------------
    # winner serving
    if r["w_svpt"] > 0:
        O = (r["w_1stWon"] + r["w_2ndWon"]) / r["w_svpt"]
        E = expected(serve_global[w], return_global[l])
        d_sr = K_SR * weight_svpt(r["w_svpt"]) * (O - E)
        serve_global[w] += d_sr
        return_global[l] -= d_sr

        if s in SURFACES:
            serve_surface[s][w] += d_sr
            return_surface[s][l] -= d_sr
            sr_surface_n[s][w] += 1
            sr_surface_n[s][l] += 1

    # loser serving
    if r["l_svpt"] > 0:
        O = (r["l_1stWon"] + r["l_2ndWon"]) / r["l_svpt"]
        E = expected(serve_global[l], return_global[w])
        d_sr = K_SR * weight_svpt(r["l_svpt"]) * (O - E)
        serve_global[l] += d_sr
        return_global[w] -= d_sr

        if s in SURFACES:
            serve_surface[s][l] += d_sr
            return_surface[s][w] -= d_sr
            sr_surface_n[s][l] += 1
            sr_surface_n[s][w] += 1

    last_played[w] = d
    last_played[l] = d

# -------------------------
# SAVE
# -------------------------
for k, v in out.items():
    df[k] = v


# %%
df[[
  "w_match_elo_pre", "l_match_elo_pre",
  "w_serve_elo_pre", "l_serve_elo_pre",
  "w_return_elo_pre", "l_return_elo_pre"
]].describe()

# %%
(df["w_return_elo_pre"] > df["l_return_elo_pre"]).mean()


# %%
df[["w_serve_elo_pre","w_return_elo_pre"]].corr()
df[["l_serve_elo_pre","l_return_elo_pre"]].corr()

# %%
DJOKOVIC_ID = 106043

djoko = df[
    (df["winner_name"] == DJOKOVIC_ID) |
    (df["loser_name"] == DJOKOVIC_ID)
].copy()

# Extract pre-match Elos correctly
djoko["match_elo_pre"] = djoko.apply(
    lambda r: r["w_return_elo_pre"]
    if r["winner_name"] == DJOKOVIC_ID
    else r["l_return_elo_pre"],
    axis=1
)

djoko["match_elo_pre"].describe()


# plt.figure(figsize=(12, 5))
# plt.plot(djoko["tourney_date"], djoko["match_elo_pre"], lw=1.5)
# plt.axhline(1500, color="gray", linestyle="--", alpha=0.5)

# plt.title("Novak Djokovic – 52-Week Match Elo (Pre-Match)")
# plt.xlabel("Year")
# plt.ylabel("Elo")
# plt.tight_layout()
# plt.show()


# %%
WINDOW = timedelta(days=365)

# ---------------------------
# Rolling stores per player
# ---------------------------
history = defaultdict(list)

# Output columns
cols = [
    "ace_rate", "df_rate",
    "1stIn_pct", "1stWon_pct", "2ndWon_pct",
    "bp_saved_pct", "bp_converted_pct"
]

out = {f"w_{c}_52w": [] for c in cols}
out.update({f"l_{c}_52w": [] for c in cols})

# %%
# neutral tour-level priors
PRIORS = {
    "ace_rate": 0.06,
    "df_rate": 0.04,
    "1stIn_pct": 0.62,
    "1stWon_pct": 0.72,
    "2ndWon_pct": 0.52,
    "bp_saved_pct": 0.62,
    "bp_converted_pct": 0.40,
}

def compute_rates(rows, k=200):
    """
    rows: list of past match stat dicts
    k: shrinkage strength (≈ one medium tournament)
    """

    if not rows:
        return {
            "ace_rate": PRIORS["ace_rate"],
            "df_rate": PRIORS["df_rate"],
            "1stIn_pct": PRIORS["1stIn_pct"],
            "1stWon_pct": PRIORS["1stWon_pct"],
            "2ndWon_pct": PRIORS["2ndWon_pct"],
            "bp_saved_pct": PRIORS["bp_saved_pct"],
            "bp_converted_pct": PRIORS["bp_converted_pct"],
            "svpt_reliability": 0.0,
            "bp_reliability": 0.0,
        }

    tot = defaultdict(float)

    for r in rows:
        tot["ace"] += r["ace"]
        tot["df"] += r["df"]
        tot["svpt"] += r["svpt"]
        tot["1stIn"] += r["1stIn"]
        tot["1stWon"] += r["1stWon"]
        tot["2ndWon"] += r["2ndWon"]
        tot["bpSaved"] += r["bpSaved"]
        tot["bpFaced"] += r["bpFaced"]
        tot["bpConv"] += r["bpConv"]
        tot["bpOpp"] += r["bpOpp"]

    def shrink(rate, n, prior):
        w = n / (n + k) if n > 0 else 0.0
        return w * rate + (1 - w) * prior

    ace_rate = tot["ace"] / tot["svpt"] if tot["svpt"] > 0 else PRIORS["ace_rate"]
    df_rate = tot["df"] / tot["svpt"] if tot["svpt"] > 0 else PRIORS["df_rate"]
    first_in = tot["1stIn"] / tot["svpt"] if tot["svpt"] > 0 else PRIORS["1stIn_pct"]
    first_won = tot["1stWon"] / tot["1stIn"] if tot["1stIn"] > 0 else PRIORS["1stWon_pct"]
    second_won = tot["2ndWon"] / (tot["svpt"] - tot["1stIn"]) if tot["svpt"] > tot["1stIn"] else PRIORS["2ndWon_pct"]
    bp_saved = tot["bpSaved"] / tot["bpFaced"] if tot["bpFaced"] > 0 else PRIORS["bp_saved_pct"]
    bp_conv = tot["bpConv"] / tot["bpOpp"] if tot["bpOpp"] > 0 else PRIORS["bp_converted_pct"]

    return {
        "ace_rate": shrink(ace_rate, tot["svpt"], PRIORS["ace_rate"]),
        "df_rate": shrink(df_rate, tot["svpt"], PRIORS["df_rate"]),
        "1stIn_pct": shrink(first_in, tot["svpt"], PRIORS["1stIn_pct"]),
        "1stWon_pct": shrink(first_won, tot["1stIn"], PRIORS["1stWon_pct"]),
        "2ndWon_pct": shrink(second_won, tot["svpt"] - tot["1stIn"], PRIORS["2ndWon_pct"]),
        "bp_saved_pct": shrink(bp_saved, tot["bpFaced"], PRIORS["bp_saved_pct"]),
        "bp_converted_pct": shrink(bp_conv, tot["bpOpp"], PRIORS["bp_converted_pct"]),
        "svpt_reliability": tot["svpt"] / (tot["svpt"] + k),
        "bp_reliability": tot["bpFaced"] / (tot["bpFaced"] + k),
    }


# %%
# ---------------------------
# Main loop
# ---------------------------
for _, r in df.iterrows():
    date = r["tourney_date"]

    for side in ["w", "l"]:
        pid = r[f"{side}inner_name"] if side == "w" else r["loser_name"]

        # filter 52-week window
        rows = [
            x for x in history[pid]
            if date - x["date"] <= WINDOW
        ]

        stats = compute_rates(rows)

        for c in cols:
            out[f"{side}_{c}_52w"].append(stats[c])

    # ---------------------------
    # Update history AFTER feature extraction
    # ---------------------------
    history[r["winner_id"]].append({
        "date": date,
        "ace": r["w_ace"],
        "df": r["w_df"],
        "svpt": r["w_svpt"],
        "1stIn": r["w_1stIn"],
        "1stWon": r["w_1stWon"],
        "2ndWon": r["w_2ndWon"],
        "bpSaved": r["w_bpSaved"],
        "bpFaced": r["w_bpFaced"],
        "bpConv": r["l_bpFaced"] - r["l_bpSaved"],
        "bpOpp": r["l_bpFaced"]
    })

    history[r["loser_name"]].append({
        "date": date,
        "ace": r["l_ace"],
        "df": r["l_df"],
        "svpt": r["l_svpt"],
        "1stIn": r["l_1stIn"],
        "1stWon": r["l_1stWon"],
        "2ndWon": r["l_2ndWon"],
        "bpSaved": r["l_bpSaved"],
        "bpFaced": r["l_bpFaced"],
        "bpConv": r["w_bpFaced"] - r["w_bpSaved"],
        "bpOpp": r["w_bpFaced"]
    })

# ---------------------------
# Save
# ---------------------------
for k, v in out.items():
    df[k] = v

# %%
df[[
  "w_ace_rate_52w", "w_df_rate_52w",
  "w_1stIn_pct_52w", "w_1stWon_pct_52w", "w_2ndWon_pct_52w",
  "w_bp_saved_pct_52w", "w_bp_converted_pct_52w"
]].describe()


# %%
df["match_date"] = pd.to_datetime(df["match_date"].astype(str), format="%Y%m%d")

# Sort for deterministic history (important)
df = df.sort_values(["match_date", "tourney_id", "match_num"]).reset_index(drop=True)

# Create a stable match id
df["match_id"] = np.arange(len(df))

# ---- Build long (player-appearance) table internally
# We attribute "retired" to the LOSER as the injury signal (RET/W-O/DEF usually corresponds to loser withdrawing).
base_cols = ["match_id", "match_date", "tourney_id", "best_of", "minutes", "retired", "winner_name", "loser_name"]

long_w = df[base_cols].copy()
long_w["player_id"] = df["winner_name"]
long_w["opponent_id"] = df["loser_name"]
long_w["role"] = "w"
long_w["player_incomplete"] = 0

long_l = df[base_cols].copy()
long_l["player_id"] = df["loser_name"]
long_l["opponent_id"] = df["winner_name"]
long_l["role"] = "l"
long_l["player_incomplete"] = df["retired"].astype(int)

long = pd.concat([long_w, long_l], ignore_index=True)
long = long.sort_values(["player_id", "match_date", "match_id", "role"]).reset_index(drop=True)

# %%
# # ---- Fatigue computation per player (single pass per player; leakage-safe)
# def add_fatigue_per_player(g: pd.DataFrame) -> pd.DataFrame:
#     g = g.sort_values(["match_date", "match_id"]).copy()
#     ln2 = math.log(2)

#     # Global workload states (decayed minutes)
#     last_date = None
#     s7 = 0.0
#     s28 = 0.0

#     # Tournament grind states (reset when tourney_id changes)
#     last_tourney = None
#     tour_minutes = 0.0
#     tour_matches = 0
#     tour_last_date = None
#     tour_bo5_minutes = 0.0

#     # Injury signal: last date player withdrew/retired (attributed to loser rows)
#     last_injury_date = None

#     RPLI, LSI, TGI, IRF, TS = [], [], [], [], []

#     for _, row in g.iterrows():
#         t = row["match_date"]

#         # --- Decay global sums based on days since last match
#         if last_date is None:
#             rest_days = 30
#         else:
#             delta = max((t - last_date).days, 0)
#             rest_days = delta
#             s7 *= math.exp(-ln2 * delta / 7.0)
#             s28 *= math.exp(-ln2 * delta / 28.0)

#         dMin7, dMin28 = s7, s28

#         # 1) RPLI
#         rpli = dMin7 + 0.5 * dMin28 - 0.75 * rest_days

#         # 2) LSI
#         acwr = dMin7 / (dMin28 + 1e-6)
#         spike = dMin7 - dMin28
#         lsi = acwr + 0.5 * spike

#         # --- Tournament grind states (reset on new tournament)
#         if last_tourney is None or row["tourney_id"] != last_tourney:
#             tour_minutes = 0.0
#             tour_matches = 0
#             tour_last_date = None
#             tour_bo5_minutes = 0.0

#         if tour_last_date is None:
#             tour_rest = 30
#         else:
#             tour_rest = max((t - tour_last_date).days, 0)

#         # 3) TGI (with BO5 grind add-on)
#         tgi = tour_minutes + 0.5 * tour_matches - 0.5 * tour_rest
#         if int(row["best_of"]) == 5:
#             tgi += tour_bo5_minutes

#         # 4) IRF (injury risk flag)
#         if last_injury_date is None:
#             irf = 0
#         else:
#             irf = int((t - last_injury_date).days <= 28)

#         # 5) TravelStress proxy (tourney switch + short rest)
#         travel_stress = int(
#             (last_tourney is not None)
#             and (row["tourney_id"] != last_tourney)
#             and (rest_days <= 2)
#         )

#         RPLI.append(rpli)
#         LSI.append(lsi)
#         TGI.append(tgi)
#         IRF.append(irf)
#         TS.append(travel_stress)

#         # --- Post-match update: add this match minutes into future state
#         mins = row["minutes"]
#         if pd.isna(mins):
#             mins = 0.0

#         s7 += float(mins)
#         s28 += float(mins)
#         last_date = t

#         last_tourney = row["tourney_id"]
#         tour_minutes += float(mins)
#         tour_matches += 1
#         tour_last_date = t
#         if int(row["best_of"]) == 5:
#             tour_bo5_minutes += float(mins)

#         # Injury update if THIS player withdrew/retired (we attribute to loser side)
#         if int(row.get("player_incomplete", 0)) == 1:
#             last_injury_date = t

#     g["RPLI"] = RPLI
#     g["LSI"] = LSI
#     g["TGI"] = TGI
#     g["IRF"] = IRF
#     g["TravelStress"] = TS
#     return g



# def add_fatigue_and_layoff_features(g: pd.DataFrame) -> pd.DataFrame:
#     g = g.sort_values(["match_date", "match_id"]).copy()
#     ln2 = math.log(2)

#     # State Variables
#     last_date, s7, s28 = None, 0.0, 0.0
#     last_tourney, tour_minutes, tour_matches = None, 0.0, 0
#     last_injury_date = None
    
#     # Layoff tracking
#     rust_index = 0.0

#     RPLI_list, LSI_list, TGI_list, IRF_list, RUST_list = [], [], [], [], []

#     for _, row in g.iterrows():
#         t = pd.to_datetime(row["match_date"])
        
#         # 1. GAPS AND LAYOFFS
#         if last_date is None:
#             rest_days = 30
#         else:
#             delta = (t - last_date).days
#             rest_days = max(delta, 0)
            
#             # --- HEURISTIC: Identify an Injury Layoff (> 60 days)
#             if rest_days > 60:
#                 rust_index = 1.0 # Maximum rust upon return
#                 s7, s28 = 0.0, 0.0 # Clear workloads
            
#             # --- Seasonal Reset (> 21 days but < 60 days)
#             elif rest_days > 21:
#                 s7, s28 = 0.0, 0.0
#                 # We don't trigger Rust for a standard 3-week off-season
                
#         # 2. DECAY WORKLOADS
#         s7 *= math.exp(-ln2 * rest_days / 7.0)
#         s28 *= math.exp(-ln2 * rest_days / 28.0)

#         # 3. COMPUTE FEATURES (Before current match)
        
#         # RPLI: Load vs Rest
#         rpli = s7 + (0.5 * s28) - rest_days

#         # LSI: ACWR stabilized with 100min "base"
#         # High LSI + High Rust = Very high risk of second injury or upset
#         acwr = s7 / (s28 + 100)
#         lsi = (acwr * 100) + (s7 - s28)
#         lsi = np.clip(lsi, -100, 500)

#         # TGI: Current Tournament Grind
#         if last_tourney is None or row["tourney_id"] != last_tourney:
#             tour_minutes, tour_matches = 0.0, 0
#         tgi = tour_minutes + (tour_matches * 10)

#         # IRF: Did they retire in the last 28 days?
#         irf = int(last_injury_date is not None and (t - last_injury_date).days <= 28)

#         # 4. APPEND FEATURES
#         RPLI_list.append(rpli)
#         LSI_list.append(lsi)
#         TGI_list.append(tgi)
#         IRF_list.append(irf)
#         RUST_list.append(rust_index)

#         # 5. POST-MATCH UPDATE
#         mins = row["minutes"]
#         score = str(row["score"])
#         is_retirement = "RET" in score or "W/O" in score

#         # Impute minutes (No surface multipliers used here)
#         if pd.isna(mins) or mins < 20 or is_retirement:
#             mins = 110 if int(row["best_of"]) == 3 else 170

#         s7 += float(mins)
#         s28 += float(mins)
#         tour_minutes += float(mins)
#         tour_matches += 1
#         last_date = t
#         last_tourney = row["tourney_id"]
        
#         # Decrease rust for every match successfully completed
#         if rust_index > 0:
#             rust_index = max(0, rust_index - 0.2) # Fully "un-rusted" after 5 matches
            
#         if is_retirement:
#             last_injury_date = t
#             # Optional: A retirement can reset rust if they go back to the sidelines
#             # rust_index = 0.5 

#     g["RPLI"], g["LSI"], g["TGI"], g["IRF"], g["RustIndex"] = RPLI_list, LSI_list, TGI_list, IRF_list, RUST_list
#     return g


# %%
# fat_long = long.groupby("player_id", group_keys=False).apply(add_fatigue_per_player)

# # ---- Merge back to match-level (one row per match)
# w_feats = fat_long[fat_long["role"] == "w"][["match_id", "RPLI", "LSI", "TGI", "IRF", "TravelStress"]].rename(
#     columns={"RPLI": "w_RPLI", "LSI": "w_LSI", "TGI": "w_TGI", "IRF": "w_IRF", "TravelStress": "w_TravelStress"}
# )
# l_feats = fat_long[fat_long["role"] == "l"][["match_id", "RPLI", "LSI", "TGI", "IRF", "TravelStress"]].rename(
#     columns={"RPLI": "l_RPLI", "LSI": "l_LSI", "TGI": "l_TGI", "IRF": "l_IRF", "TravelStress": "l_TravelStress"}
# )

# df = df.merge(w_feats, on="match_id", how="left").merge(l_feats, on="match_id", how="left")

# %%
# # --- 1) Required columns present
# req = [
#     "match_date","tourney_id","match_num","winner_name","loser_name","minutes","retired","best_of",
#     "w_RPLI","w_LSI","w_TGI","w_IRF","w_TravelStress",
#     "l_RPLI","l_LSI","l_TGI","l_IRF","l_TravelStress",
# ]
# missing = [c for c in req if c not in df.columns]
# print("Missing columns:", missing)

# # --- 2) Parse date + sort (ensures diagnostics consistent)
# df["match_date"] = pd.to_datetime(df["match_date"])
# df = df.sort_values(["match_date","tourney_id","match_num"]).reset_index(drop=True)

# # --- 3) Check NaN / inf in fatigue features
# fat_cols = [
#     "w_RPLI","w_LSI","w_TGI","w_IRF","w_TravelStress",
#     "l_RPLI","l_LSI","l_TGI","l_IRF","l_TravelStress",
# ]

# nan_counts = df[fat_cols].isna().sum().sort_values(ascending=False)
# inf_counts = np.isinf(df[fat_cols].to_numpy()).sum(axis=0)
# inf_counts = pd.Series(inf_counts, index=fat_cols).sort_values(ascending=False)

# print("\nNaN counts (fatigue cols):")
# print(nan_counts[nan_counts > 0].head(20) if (nan_counts > 0).any() else "None")

# print("\nInf counts (fatigue cols):")
# print(inf_counts[inf_counts > 0].head(20) if (inf_counts > 0).any() else "None")

# # --- 4) Basic ranges / distribution sanity
# print("\nFatigue feature summary (winner):")
# print(df[["w_RPLI","w_LSI","w_TGI","w_IRF","w_TravelStress"]].describe(percentiles=[.01,.05,.5,.95,.99]))

# print("\nFatigue feature summary (loser):")
# print(df[["l_RPLI","l_LSI","l_TGI","l_IRF","l_TravelStress"]].describe(percentiles=[.01,.05,.5,.95,.99]))

# # --- 5) Sanity: first-ever match for a player should have fatigue ~0
# # We'll check the earliest appearance per player for both roles.
# first_w = df.sort_values("match_date").groupby("winner_name").head(1)
# first_l = df.sort_values("match_date").groupby("loser_name").head(1)

# print("\nEarliest winner appearances: % with |w_RPLI|<=1e-9:", (first_w["w_RPLI"].abs() <= 1e-9).mean())
# print("Earliest loser appearances:  % with |l_RPLI|<=1e-9:", (first_l["l_RPLI"].abs() <= 1e-9).mean())

# # --- 6) TravelStress should be rare-ish and binary
# for col in ["w_TravelStress","l_TravelStress","w_IRF","l_IRF"]:
#     vals = df[col].value_counts(dropna=False).sort_index()
#     print(f"\n{col} value counts:\n{vals}")

# # --- 7) Quick “leakage smell test”:
# # Fatigue should correlate positively with recent minutes played, not with future minutes.
# # (We do a weak check: higher fatigue today tends to have higher minutes in last 28 days proxy;
# # we don't have explicit past-28-minutes here, so we just check that RPLI correlates with minutes
# # *in the match itself* only weakly/moderately, not extremely.)
# print("\nCorr(w_RPLI, minutes):", df["w_RPLI"].corr(df["minutes"]))
# print("Corr(l_RPLI, minutes):", df["l_RPLI"].corr(df["minutes"]))

# # --- 8) Spot-check one player timeline
# def inspect_player(pid, n=55):
#     m = df[(df["winner_name"] == pid) | (df["loser_name"] == pid)].copy()
#     m = m.sort_values(["match_date","tourney_id","match_num"])
#     # Pull role-specific fatigue
#     m["role"] = np.where(m["winner_name"] == pid, "W", "L")
#     m["RPLI"] = np.where(m["winner_name"] == pid, m["w_RPLI"], m["l_RPLI"])
#     m["TGI"]  = np.where(m["winner_name"] == pid, m["w_TGI"],  m["l_TGI"])
#     m["IRF"]  = np.where(m["winner_name"] == pid, m["w_IRF"],  m["l_IRF"])
#     m["TS"]   = np.where(m["winner_name"] == pid, m["w_TravelStress"], m["l_TravelStress"])
#     cols = ["match_date","tourney_id","round","minutes","retired","best_of","role","RPLI","TGI","IRF","TS"]
#     return m[cols].head(n)

# # Pick a player with lots of matches (top 20 by appearances) and inspect
# counts = pd.concat([df["winner_name"], df["loser_name"]]).value_counts()
# pid = counts.index[0]
# print("\nInspecting most frequent player_id:", pid, "matches:", counts.iloc[0])
# print(inspect_player(pid, n=55).to_string(index=False))


# %%
# Storage for career/surface matches
w_career = []
l_career = []
w_surface = []
l_surface = []

# State
career_count = {}
surface_count = {}

for _, row in df.iterrows():
    w = row["winner_name"]
    l = row["loser_name"]
    s = row["surface"]

    # Initialise
    for p in (w, l):
        career_count.setdefault(p, 0)
        surface_count.setdefault((p, s), 0)

    # Pre-match values
    w_career.append(career_count[w])
    l_career.append(career_count[l])

    w_surface.append(surface_count[(w, s)])
    l_surface.append(surface_count[(l, s)])

    # Post-match update
    career_count[w] += 1
    career_count[l] += 1

    surface_count[(w, s)] += 1
    surface_count[(l, s)] += 1

df["w_career_matches"] = w_career
df["l_career_matches"] = l_career
df["w_surface_matches"] = w_surface
df["l_surface_matches"] = l_surface

# %%
# H2H state: (player, opponent) -> wins
h2h_wins = {}

rel_h2h_win_diff = []
h2h_matches = []

for _, row in df.iterrows():
    w = row["winner_name"]
    l = row["loser_name"]

    # Initialise
    h2h_wins.setdefault((w, l), 0)
    h2h_wins.setdefault((l, w), 0)

    # Pre-match H2H
    w_wins = h2h_wins[(w, l)]
    l_wins = h2h_wins[(l, w)]

    rel_h2h_win_diff.append(w_wins - l_wins)
    h2h_matches.append(w_wins + l_wins)

    # Post-match update
    h2h_wins[(w, l)] += 1

df["rel_h2h_win_diff"] = rel_h2h_win_diff
df["h2h_matches"] = h2h_matches

# %%
# -------------------------------------------------
# 2) BUILD RELATIVE DIFFERENCE FEATURES
#    (winner - loser)
# -------------------------------------------------
def is_num(col):
    return pd.api.types.is_numeric_dtype(df[col])

pairs = []

# w_ / l_
for c in df.columns:
    if c.startswith("w_"):
        lc = "l_" + c[2:]
        if lc in df.columns and is_num(c) and is_num(lc):
            pairs.append((c, lc, f"rel_{c[2:]}"))

# winner_ / loser_
for c in df.columns:
    if c.startswith("winner_"):
        lc = "loser_" + c[len("winner_"):]
        if lc in df.columns and is_num(c) and is_num(lc):
            pairs.append((c, lc, f"rel_{c[len('winner_'):]}"))

for a, b, feat in pairs:
    df[feat] = df[a].astype(float) - df[b].astype(float)

# %%
df["rel_serve_elo_x_grass"] = df["rel_serve_elo_pre"] * (df["surface"] == "Grass").astype(int)
df["rel_return_elo_x_clay"] = df["rel_return_elo_pre"] * (df["surface"] == "Clay").astype(int)


# %%
df.to_csv('atp_matches_feature_add.csv', index=False, header=True)
df

# %%



