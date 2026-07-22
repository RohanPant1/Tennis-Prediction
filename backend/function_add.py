# %%
import pandas as pd
import math
from collections import defaultdict
from datetime import timedelta

df = pd.read_csv("atp_matches_data_cleaned.csv")


# %%
df["tourney_date"] = pd.to_datetime(
    df["tourney_date"],
    format="%Y%m%d",
    errors="coerce"
)

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
ROLE_TO_NAME_COL = {"w": "winner_name", "l": "loser_name"}

for _, r in df.iterrows():
    date = r["tourney_date"]

    for side in ["w", "l"]:
        pid = r[ROLE_TO_NAME_COL[side]]

        # filter 52-week window
        rows = [
            x for x in history[pid]
            if date - x["date"] <= WINDOW
        ]

        stats = compute_rates(rows)

        for c in cols:
            out[f"{side}_{c}_52w"].append(stats[c])

    # ---------------------------
    # Update history AFTER feature extraction.
    # Both sides must be keyed by *name* to match the lookup above - keying the
    # winner by winner_id here previously meant a player's own wins were stored
    # under a different key than their future lookups used, so their rolling
    # stats only ever reflected their losses.
    # ---------------------------
    history[r["winner_name"]].append({
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
