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
PRIORS = {
    "ace_rate": 0.06, "df_rate": 0.04, "1stIn_pct": 0.62,
    "1stWon_pct": 0.72, "2ndWon_pct": 0.52, "bp_saved_pct": 0.62, "bp_converted_pct": 0.40,
}

def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** (-(ra - rb) / 400))

def decay_elo(r, days):
    if days <= 0: return r
    return START_ELO + (r - START_ELO) * math.exp(-days / TAU)

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
        'h2h_matches': len(h2h_before)
    }

def get_player_prediction_state(player_name, target_date, surface, df):
    p_df = df[(df['winner_name'] == player_name) | (df['loser_name'] == player_name)].copy()
    p_df['match_date'] = pd.to_datetime(p_df['match_date'])
    p_df['player_name_identity'] = player_name
    p_df = p_df.sort_values('match_date')
    
    target_dt = pd.to_datetime(target_date)
    after = p_df[p_df['match_date'] >= target_dt]
    
    if not after.empty:
        m = after.iloc[0]
        prefix = 'w' if m['winner_name'] == player_name else 'l'
        stats = {
            'match_elo': m[f'{prefix}_match_elo_pre'], 'serve_elo': m[f'{prefix}_serve_elo_pre'],
            'return_elo': m[f'{prefix}_return_elo_pre'], 'ace_rate': m[f'{prefix}_ace_rate_52w'],
            'df_rate': m[f'{prefix}_df_rate_52w'], '1stIn_pct': m[f'{prefix}_1stIn_pct_52w'],
            '1stWon_pct': m[f'{prefix}_1stWon_pct_52w'], '2ndWon_pct': m[f'{prefix}_2ndWon_pct_52w'],
            'bp_saved_pct': m[f'{prefix}_bp_saved_pct_52w'], 'bp_converted_pct': m[f'{prefix}_bp_converted_pct_52w'],
            'career_matches': m[f'{prefix}_career_matches'], 'surface_matches': m[f'{prefix}_surface_matches'],
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
        K_elo = 40 if m['best_of'] == 5 else 32
        p_win = expected(m['w_match_elo_pre'], m['l_match_elo_pre'])
        delta = K_elo * (1 - p_win)
        post_elo = m[f'{prefix}_match_elo_pre'] + (delta if is_w else -delta)
        days = (target_dt - m['match_date']).days
        current_elo = decay_elo(post_elo, max(0, days))
        rolling = compute_rolling_stats(p_df, target_dt)
        stats = {
            'match_elo': current_elo, 'serve_elo': m[f'{prefix}_serve_elo_pre'],
            'return_elo': m[f'{prefix}_return_elo_pre'], **rolling,
            'career_matches': m[f'{prefix}_career_matches'] + 1,
            'surface_matches': m[f'{prefix}_surface_matches'] + 1,
            'ht': m[f'winner_ht' if is_w else 'loser_ht'],
            'age': m[f'winner_age' if is_w else 'loser_age'] + (days/365.25),
            'rank_points': m[f'winner_rank_points' if is_w else 'loser_rank_points'],
        }
    return stats



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
    for level in ['A', 'D', 'F', 'G', 'M', 'O']:
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
        'surface=GRASS', 'surface=HARD', 'tourney_level=A', 'tourney_level=D', 'tourney_level=F', 
        'tourney_level=G', 'tourney_level=M', 'tourney_level=O', 'round=0', 'round=1', 
        'round=2', 'round=3', 'round=4', 'round=5', 'round=6', 'round=7'
    ]
    return pd.DataFrame([feat])[ordered_columns]

# %%
def predict_matchup(p1, p2, target_date, surface, draw_size, best_of, tourney_level, round_idx, df_stats, model):
    """
    Generates features for a specific matchup and uses the trained model to predict a winner.
    """
    # 1. Generate the features using the function we built
    X_input = get_matchup_features(
        p1, p2, target_date, surface, draw_size, best_of, tourney_level, round_idx, df_stats
    )
    
    # Convert booleans to ints (as done in step 2 of your model.ipynb)
    bool_cols = X_input.select_dtypes(include=['bool']).columns
    X_input[bool_cols] = X_input[bool_cols].astype(int)

    # 3. Predict Probabilities
    # prob[0] is the probability of Target=0 (Player 2 wins)
    # prob[1] is the probability of Target=1 (Player 1 wins)
    prob = model.predict_proba(X_input)[0]
    prediction = model.predict(X_input)[0]

    winner = p1 if prediction == 1 else p2
    confidence = prob[1] if prediction == 1 else prob[0]

    print(f"--- Prediction: {p1} vs {p2} ---")
    print(f"Surface: {surface} | Date: {target_date}")
    print(f"Predicted Winner: {winner}")
    print(f"Confidence: {confidence:.2%}")
    print(f"Win Probability for {p1}: {prob[1]:.2%}")
    print(f"Win Probability for {p2}: {prob[0]:.2%}")
    
    return {
        'winner': winner,
        'p1_prob': prob[1],
        'p2_prob': prob[0],
        'features': X_input
    }



