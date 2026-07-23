# %%
import pandas as pd
import numpy as np
import math
from datetime import timedelta

# %%
# --- Parameters & Helpers from your logic ---
START_ELO = 1500.0
HALF_LIFE_DAYS = 365.0
TAU = HALF_LIFE_DAYS / math.log(2)
K_SR = 20.0  # serve/return Elo K-factor, mirrors feature_add.ipynb
PRIORS = {
    "ace_rate": 0.06, "df_rate": 0.04, "1stIn_pct": 0.62,
    "1stWon_pct": 0.72, "2ndWon_pct": 0.52, "bp_saved_pct": 0.62, "bp_converted_pct": 0.40,
}

def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** (-(ra - rb) / 400))

def decay_elo(r, days):
    if days <= 0: return r
    return START_ELO + (r - START_ELO) * math.exp(-days / TAU)

def weight_svpt(svpt):
    return min(math.sqrt(svpt / 100.0), 1.5) if svpt > 0 else 0.0

def shrink(rate, n, prior, k=200):
    w = n / (n + k) if n > 0 else 0.0
    return w * rate + (1 - w) * prior

def compute_rolling_stats(player_matches, target_date):
    window_start = pd.to_datetime(target_date) - timedelta(days=365)
    recent = player_matches[pd.to_datetime(player_matches['match_date']) >= window_start]
    
    tot = {'ace':0, 'df':0, 'svpt':0, '1stIn':0, '1stWon':0, '2ndWon':0, 'bpS':0, 'bpF':0, 'bpC':0, 'bpO':0}
    for _, r in recent.iterrows():
        prefix = 'w_' if r['winner_name'] == player_matches.iloc[0]['player_name_identity'] else 'l_'
        opp_prefix = 'l_' if prefix == 'w_' else 'w_'
        tot['ace'] += r[f'{prefix}ace']; tot['df'] += r[f'{prefix}df']; tot['svpt'] += r[f'{prefix}svpt']
        tot['1stIn'] += r[f'{prefix}1stIn']; tot['1stWon'] += r[f'{prefix}1stWon']; tot['2ndWon'] += r[f'{prefix}2ndWon']
        tot['bpS'] += r[f'{prefix}bpSaved']; tot['bpF'] += r[f'{prefix}bpFaced']
        tot['bpC'] += (r[f'{opp_prefix}bpFaced'] - r[f'{opp_prefix}bpSaved'])
        tot['bpO'] += r[f'{opp_prefix}bpFaced']

    k_val = 200
    return {
        'ace_rate': shrink(tot['ace']/tot['svpt'] if tot['svpt']>0 else 0, tot['svpt'], PRIORS['ace_rate'], k_val),
        'df_rate': shrink(tot['df']/tot['svpt'] if tot['svpt']>0 else 0, tot['svpt'], PRIORS['df_rate'], k_val),
        '1stIn_pct': shrink(tot['1stIn']/tot['svpt'] if tot['svpt']>0 else 0, tot['svpt'], PRIORS['1stIn_pct'], k_val),
        '1stWon_pct': shrink(tot['1stWon']/tot['1stIn'] if tot['1stIn']>0 else 0, tot['1stIn'], PRIORS['1stWon_pct'], k_val),
        '2ndWon_pct': shrink(tot['2ndWon']/(tot['svpt']-tot['1stIn']) if (tot['svpt']-tot['1stIn'])>0 else 0, (tot['svpt']-tot['1stIn']), PRIORS['2ndWon_pct'], k_val),
        'bp_saved_pct': shrink(tot['bpS']/tot['bpF'] if tot['bpF']>0 else 0, tot['bpF'], PRIORS['bp_saved_pct'], k_val),
        'bp_converted_pct': shrink(tot['bpC']/tot['bpO'] if tot['bpO']>0 else 0, tot['bpO'], PRIORS['bp_converted_pct'], k_val),
    }

def get_h2h_stats(p1, p2, target_date, df):
    """Calculates H2H wins and matches before the target_date."""
    target_dt = pd.to_datetime(target_date)
    h2h_df = df[
        ((df['winner_name'] == p1) & (df['loser_name'] == p2)) | 
        ((df['winner_name'] == p2) & (df['loser_name'] == p1))
    ]
    h2h_before = h2h_df[pd.to_datetime(h2h_df['match_date']) < target_dt]
    
    p1_wins = len(h2h_before[h2h_before['winner_name'] == p1])
    p2_wins = len(h2h_before[h2h_before['winner_name'] == p2])
    
    return {
        'rel_h2h_win_diff': p1_wins - p2_wins,
        'h2h_matches': len(h2h_before),
        'p1_wins': p1_wins,
        'p2_wins': p2_wins,
    }

def get_surface_match_count(player_name, target_date, surface, df):
    """Career matches `player_name` has played on `surface`, strictly before target_date."""
    target_dt = pd.to_datetime(target_date)
    p_df = df[
        ((df['winner_name'] == player_name) | (df['loser_name'] == player_name)) &
        (df['surface'].str.upper() == str(surface).upper())
    ]
    match_dates = pd.to_datetime(p_df['match_date'])
    return int((match_dates < target_dt).sum())


def get_player_prediction_state(player_name, target_date, surface, df):
    p_df = df[(df['winner_name'] == player_name) | (df['loser_name'] == player_name)].copy()
    p_df['match_date'] = pd.to_datetime(p_df['match_date'])
    p_df['player_name_identity'] = player_name
    p_df = p_df.sort_values('match_date')

    target_dt = pd.to_datetime(target_date)
    after = p_df[p_df['match_date'] >= target_dt]
    surface_matches = get_surface_match_count(player_name, target_date, surface, df)

    if not after.empty:
        m = after.iloc[0]
        prefix = 'w' if m['winner_name'] == player_name else 'l'
        stats = {
            'match_elo': m[f'{prefix}_match_elo_pre'], 'serve_elo': m[f'{prefix}_serve_elo_pre'],
            'return_elo': m[f'{prefix}_return_elo_pre'], 'ace_rate': m[f'{prefix}_ace_rate_52w'],
            'df_rate': m[f'{prefix}_df_rate_52w'], '1stIn_pct': m[f'{prefix}_1stIn_pct_52w'],
            '1stWon_pct': m[f'{prefix}_1stWon_pct_52w'], '2ndWon_pct': m[f'{prefix}_2ndWon_pct_52w'],
            'bp_saved_pct': m[f'{prefix}_bp_saved_pct_52w'], 'bp_converted_pct': m[f'{prefix}_bp_converted_pct_52w'],
            'career_matches': m[f'{prefix}_career_matches'], 'surface_matches': surface_matches,
            'ht': m[f'winner_ht' if prefix == 'w' else 'loser_ht'],
            'age': m[f'winner_age' if prefix == 'w' else 'loser_age'],
            'rank_points': m[f'winner_rank_points' if prefix == 'w' else 'loser_rank_points'],
        }
    else:
        before = p_df[p_df['match_date'] < target_dt]
        if before.empty: return None
        m = before.iloc[-1]
        is_w = m['winner_name'] == player_name
        prefix = 'w' if is_w else 'l'
        days = (target_dt - m['match_date']).days

        # The model's Elo features are trained as global+surface blends, so
        # estimate them for the surface being predicted (via the player's last
        # real match on that surface) rather than just decaying whatever surface
        # their overall most recent match happened to be on.
        surface_ratings = get_surface_ratings(player_name, target_date, surface, df)
        if surface_ratings:
            match_elo, serve_elo, return_elo = (
                surface_ratings['match_elo'], surface_ratings['serve_elo'], surface_ratings['return_elo']
            )
        else:
            K_elo = 40 if m['best_of'] == 5 else 32
            p_win = expected(m['w_match_elo_pre'], m['l_match_elo_pre'])
            delta = K_elo * (1 - p_win)
            match_elo = decay_elo(m[f'{prefix}_match_elo_pre'] + (delta if is_w else -delta), max(0, days))
            serve_elo = m[f'{prefix}_serve_elo_pre']
            return_elo = m[f'{prefix}_return_elo_pre']

        rolling = compute_rolling_stats(p_df, target_dt)
        stats = {
            'match_elo': match_elo, 'serve_elo': serve_elo,
            'return_elo': return_elo, **rolling,
            'career_matches': m[f'{prefix}_career_matches'] + 1,
            'surface_matches': surface_matches,
            'ht': m[f'winner_ht' if is_w else 'loser_ht'],
            'age': m[f'winner_age' if is_w else 'loser_age'] + (days/365.25),
            'rank_points': m[f'winner_rank_points' if is_w else 'loser_rank_points'],
        }
    return stats


def get_surface_ratings(player_name, target_date, surface, df):
    """Best-effort surface-blended match/serve/return Elo, approximated from the
    player's most recent real match on this exact surface: replay that match's
    own Elo update (win/loss for match_elo, serve/return performance for
    serve_elo/return_elo, mirroring feature_add.ipynb's update formulas), then
    decay toward the 1500 baseline for the elapsed days since. Returns None if
    the player has no history on this surface, so callers can fall back to
    overall (any-surface) ratings.

    This is what feeds surface_elo (display) and, via get_player_prediction_state,
    the model's actual rel_match_elo_pre/rel_serve_elo_pre/rel_return_elo_pre
    features -- those are trained as global+surface blends, so at inference time
    they need to be estimated for the surface being predicted, not just carried
    over from whatever surface the player's last real match happened to be on.
    """
    target_dt = pd.to_datetime(target_date)
    p_df = df[
        ((df['winner_name'] == player_name) | (df['loser_name'] == player_name)) &
        (df['surface'].str.upper() == str(surface).upper())
    ].copy()
    p_df['match_date'] = pd.to_datetime(p_df['match_date'])
    before = p_df[p_df['match_date'] < target_dt].sort_values('match_date')

    if before.empty:
        return None

    m = before.iloc[-1]
    is_w = m['winner_name'] == player_name
    prefix = 'w' if is_w else 'l'
    opp_prefix = 'l' if is_w else 'w'
    days = max(0, (target_dt - m['match_date']).days)

    # Match Elo: replay this match's own win/loss update.
    K_elo = 40 if m['best_of'] == 5 else 32
    p_win = expected(m['w_match_elo_pre'], m['l_match_elo_pre'])
    delta = K_elo * (1 - p_win)
    match_elo = decay_elo(m[f'{prefix}_match_elo_pre'] + (delta if is_w else -delta), days)

    # Serve Elo: replay this match's own serving performance.
    serve_elo = m[f'{prefix}_serve_elo_pre']
    svpt = m[f'{prefix}_svpt']
    if svpt > 0:
        O = (m[f'{prefix}_1stWon'] + m[f'{prefix}_2ndWon']) / svpt
        E = expected(m[f'{prefix}_serve_elo_pre'], m[f'{opp_prefix}_return_elo_pre'])
        serve_elo += K_SR * weight_svpt(svpt) * (O - E)
    serve_elo = decay_elo(serve_elo, days)

    # Return Elo: replay this match's opponent-serving performance.
    return_elo = m[f'{prefix}_return_elo_pre']
    opp_svpt = m[f'{opp_prefix}_svpt']
    if opp_svpt > 0:
        O_opp = (m[f'{opp_prefix}_1stWon'] + m[f'{opp_prefix}_2ndWon']) / opp_svpt
        E_opp = expected(m[f'{opp_prefix}_serve_elo_pre'], m[f'{prefix}_return_elo_pre'])
        return_elo -= K_SR * weight_svpt(opp_svpt) * (O_opp - E_opp)
    return_elo = decay_elo(return_elo, days)

    return {'match_elo': match_elo, 'serve_elo': serve_elo, 'return_elo': return_elo}


def get_surface_elo(player_name, target_date, surface, df):
    """Best-effort surface-relevant match Elo for display purposes.
    Thin wrapper around get_surface_ratings() for callers that only need match_elo."""
    ratings = get_surface_ratings(player_name, target_date, surface, df)
    return ratings['match_elo'] if ratings else None


def get_recent_form(player_name, target_date, df, n=10):
    """Last-n match results (newest first) strictly before target_date."""
    target_dt = pd.to_datetime(target_date)
    p_df = df[(df['winner_name'] == player_name) | (df['loser_name'] == player_name)].copy()
    p_df['match_date'] = pd.to_datetime(p_df['match_date'])
    before = p_df[p_df['match_date'] < target_dt].sort_values('match_date', ascending=False).head(n)
    results = ['W' if r['winner_name'] == player_name else 'L' for _, r in before.iterrows()]
    return {'wins': results.count('W'), 'losses': results.count('L'), 'results': results}


def get_matchup_context(p1, p2, target_date, surface, df):
    """Display-only matchup context (surface Elo, recent form, H2H) -- separate from
    and not used by the model feature path in get_matchup_features()."""
    def player_context(player_name):
        surface_elo = get_surface_elo(player_name, target_date, surface, df)
        is_fallback = surface_elo is None
        if is_fallback:
            state = get_player_prediction_state(player_name, target_date, surface, df)
            surface_elo = state['match_elo'] if state else None
        return {
            'surface_elo': surface_elo,
            'surface_elo_is_fallback': is_fallback,
            'recent_form': get_recent_form(player_name, target_date, df),
        }

    h2h = get_h2h_stats(p1, p2, target_date, df)
    return {
        'p1': player_context(p1),
        'p2': player_context(p2),
        'h2h': {'p1_wins': h2h['p1_wins'], 'p2_wins': h2h['p2_wins'], 'matches': h2h['h2h_matches']},
    }


# %%
def get_matchup_features(p1, p2, target_date, surface, draw_size, best_of, tourney_level, round_idx, df, target=0):
    """
    Combines player states and H2H logic into a feature set matching the CSV schema.
    """
    s1 = get_player_prediction_state(p1, target_date, surface, df)
    s2 = get_player_prediction_state(p2, target_date, surface, df)
    if not s1 or not s2: return None

    h2h = get_h2h_stats(p1, p2, target_date, df)

    feat = {
        'draw_size': float(draw_size),
        'best_of': int(best_of),
        'rel_match_elo_pre': s1['match_elo'] - s2['match_elo'],
        'rel_serve_elo_pre': s1['serve_elo'] - s2['serve_elo'],
        'rel_return_elo_pre': s1['return_elo'] - s2['return_elo'],
        'rel_rank_points': s1['rank_points'] - s2['rank_points'],
        'rel_age': s1['age'] - s2['age'],
        'rel_ht': s1['ht'] - s2['ht'],
        'rel_ace_rate_52w': s1['ace_rate'] - s2['ace_rate'],
        'rel_df_rate_52w': s1['df_rate'] - s2['df_rate'],
        'rel_1stIn_pct_52w': s1['1stIn_pct'] - s2['1stIn_pct'],
        'rel_1stWon_pct_52w': s1['1stWon_pct'] - s2['1stWon_pct'],
        'rel_2ndWon_pct_52w': s1['2ndWon_pct'] - s2['2ndWon_pct'],
        'rel_bp_saved_pct_52w': s1['bp_saved_pct'] - s2['bp_saved_pct'],
        'rel_bp_converted_pct_52w': s1['bp_converted_pct'] - s2['bp_converted_pct'],
        'rel_career_matches': s1['career_matches'] - s2['career_matches'],
        'rel_surface_matches': s1['surface_matches'] - s2['surface_matches'],
        'rel_h2h_win_diff': h2h['rel_h2h_win_diff'],
        'h2h_matches': h2h['h2h_matches']
    }

    # Interaction & One-Hots
    surf_up = str(surface).upper()
    feat['rel_return_elo_x_clay'] = feat['rel_return_elo_pre'] if surf_up == 'CLAY' else 0.0
    feat['rel_serve_elo_x_grass'] = feat['rel_serve_elo_pre'] if surf_up == 'GRASS' else 0.0
    feat['surface=CLAY'] = (surf_up == 'CLAY')
    feat['surface=GRASS'] = (surf_up == 'GRASS')
    feat['surface=HARD'] = (surf_up == 'HARD')

    tl_up = str(tourney_level).upper()
    for level in ['A', 'C', 'D', 'F', 'G', 'M', 'O']:
        feat[f'tourney_level={level}'] = (tl_up == level)

    for r in range(8):
        feat[f'round={r}'] = (str(round_idx) == str(r))

    feat['target'] = target

    # Force Exact Column Order
    ordered_columns = [
        'draw_size', 'best_of', 'rel_match_elo_pre', 'rel_serve_elo_pre', 'rel_return_elo_pre', 
        'rel_rank_points', 'rel_age', 'rel_ht', 'rel_ace_rate_52w', 'rel_df_rate_52w', 
        'rel_1stIn_pct_52w', 'rel_1stWon_pct_52w', 'rel_2ndWon_pct_52w', 'rel_bp_saved_pct_52w', 
        'rel_bp_converted_pct_52w', 'rel_career_matches', 'rel_surface_matches', 'rel_h2h_win_diff', 
        'h2h_matches', 'rel_return_elo_x_clay', 'rel_serve_elo_x_grass', 'surface=CLAY',
        'surface=GRASS', 'surface=HARD', 'tourney_level=A', 'tourney_level=C', 'tourney_level=D', 'tourney_level=F',
        'tourney_level=G', 'tourney_level=M', 'tourney_level=O', 'round=0', 'round=1',
        'round=2', 'round=3', 'round=4', 'round=5', 'round=6', 'round=7'
    ]
    return pd.DataFrame([feat])[ordered_columns]

# %%
FEATURE_LABELS = {
    'draw_size': 'Draw size',
    'best_of': 'Best-of format',
    'rel_match_elo_pre': 'Overall rating (Elo)',
    'rel_serve_elo_pre': 'Serve rating',
    'rel_return_elo_pre': 'Return rating',
    'rel_rank_points': 'ATP ranking points',
    'rel_age': 'Age',
    'rel_ht': 'Height',
    'rel_ace_rate_52w': 'Ace rate (last 52 weeks)',
    'rel_df_rate_52w': 'Double-fault rate (last 52 weeks)',
    'rel_1stIn_pct_52w': '1st-serve-in % (last 52 weeks)',
    'rel_1stWon_pct_52w': '1st-serve points won % (last 52 weeks)',
    'rel_2ndWon_pct_52w': '2nd-serve points won % (last 52 weeks)',
    'rel_bp_saved_pct_52w': 'Break points saved % (last 52 weeks)',
    'rel_bp_converted_pct_52w': 'Break points converted % (last 52 weeks)',
    'rel_career_matches': 'Career matches played',
    'rel_surface_matches': 'Matches played on this surface',
    'rel_h2h_win_diff': 'Head-to-head record',
    'h2h_matches': 'Head-to-head matches played',
    'rel_return_elo_x_clay': 'Return rating on clay',
    'rel_serve_elo_x_grass': 'Serve rating on grass',
    'surface=CLAY': 'Playing on clay',
    'surface=GRASS': 'Playing on grass',
    'surface=HARD': 'Playing on hard court',
    'tourney_level=A': 'Tour-level event (250/500)',
    'tourney_level=C': 'Challenger event',
    'tourney_level=D': 'Davis Cup',
    'tourney_level=F': 'Tour Finals',
    'tourney_level=G': 'Grand Slam stage',
    'tourney_level=M': 'Masters 1000 event',
    'tourney_level=O': 'Olympics / other event',
    'round=0': 'Early / unknown round',
    'round=1': 'Round of 128',
    'round=2': 'Round of 64',
    'round=3': 'Round of 32',
    'round=4': 'Round of 16',
    'round=5': 'Quarterfinal',
    'round=6': 'Semifinal',
    'round=7': 'Final',
}

def get_feature_contributions(model, X_input, p1_name, p2_name, top_n=5):
    """Per-prediction SHAP contributions via CatBoost's native TreeExplainer-equivalent.

    Positive SHAP values push the prediction toward target=1 (p1 wins);
    negative values push toward target=0 (p2 wins).
    """
    from catboost import Pool
    shap_row = model.get_feature_importance(Pool(X_input), type='ShapValues')[0]
    values = shap_row[:-1]  # last entry is the bias/expected-value term

    ranked = sorted(zip(X_input.columns, values), key=lambda x: abs(x[1]), reverse=True)[:top_n]
    return [
        {
            'feature': col,
            'label': FEATURE_LABELS.get(col, col),
            'direction': p1_name if val > 0 else p2_name,
            'magnitude': abs(float(val)),
        }
        for col, val in ranked
    ]

# %%
def predict_matchup(p1, p2, target_date, surface, draw_size, best_of, tourney_level, round_idx, df_stats, model):
    """
    Generates features for a specific matchup and uses the trained model to predict a winner.

    The model's "player A vs player B" symmetry (see feature_engineer.ipynb's random
    50%-row target-flip augmentation) is only approximate -- a boosted-tree model isn't
    architecturally guaranteed to satisfy f(swap(x)) == 1 - f(x), so predict_proba(p1, p2)
    and predict_proba(p2, p1) can disagree, most noticeably in close matchups near 50/50
    where that noise can flip the predicted winner. Averaging both directions guarantees
    p1_prob + p2_prob == 1 regardless of which player is passed as p1.
    """
    X_forward = get_matchup_features(
        p1, p2, target_date, surface, draw_size, best_of, tourney_level, round_idx, df_stats
    )
    X_reversed = get_matchup_features(
        p2, p1, target_date, surface, draw_size, best_of, tourney_level, round_idx, df_stats
    )

    if X_forward is None or X_reversed is None:
        return None

    # Convert booleans to ints (as done in step 2 of your model.ipynb)
    bool_cols = X_forward.select_dtypes(include=['bool']).columns
    X_forward[bool_cols] = X_forward[bool_cols].astype(int)
    X_reversed[bool_cols] = X_reversed[bool_cols].astype(int)

    # prob_forward: [P(target=0)=P(p2 wins), P(target=1)=P(p1 wins)]
    # prob_reversed: [P(target=0)=P(p1 wins), P(target=1)=P(p2 wins)] (p1/p2 swapped as input)
    prob_forward = model.predict_proba(X_forward)[0]
    prob_reversed = model.predict_proba(X_reversed)[0]

    p1_prob = (prob_forward[1] + prob_reversed[0]) / 2
    p2_prob = 1 - p1_prob

    winner = p1 if p1_prob >= p2_prob else p2
    confidence = max(p1_prob, p2_prob)

    print(f"--- Prediction: {p1} vs {p2} ---")
    print(f"Surface: {surface} | Date: {target_date}")
    print(f"Predicted Winner: {winner}")
    print(f"Confidence: {confidence:.2%}")
    print(f"Win Probability for {p1}: {p1_prob:.2%}")
    print(f"Win Probability for {p2}: {p2_prob:.2%}")

    return {
        'winner': winner,
        'p1_prob': p1_prob,
        'p2_prob': p2_prob,
        'features': X_forward
    }



