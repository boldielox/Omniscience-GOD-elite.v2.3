import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import copy

https://api.sportsgameodds.com/v2/sports/# ---- Paste your SportsGameOddsClient class here (no API key hardcoded) ----

# Example usage:
client = SportsGameOddsClient(st.secrets["SPORTSGAME_API_KEY"])

# --- Helper: List Games (replace with real API call if available) ---
def fetch_games(league: str) -> List[Dict]:
    # TODO: Replace this with a real API call to fetch games for the league
    # Example dummy data for demonstration
    return [
        {"id": "12345", "home_team": "Lakers", "away_team": "Celtics", "start_time": "2025-06-06T19:00:00Z"},
        {"id": "67890", "home_team": "Yankees", "away_team": "Red Sox", "start_time": "2025-06-06T20:00:00Z"}
    ]

# --- Line Movement Tracker ---
def update_line_history(game_id: str, market_type: str, market_data: List[Dict]):
    now = datetime.utcnow().isoformat()
    if 'line_history' not in st.session_state:
        st.session_state.line_history = {}
    if game_id not in st.session_state.line_history:
        st.session_state.line_history[game_id] = {}
    if market_type not in st.session_state.line_history[game_id]:
        st.session_state.line_history[game_id][market_type] = []
    # Store a copy for history
    st.session_state.line_history[game_id][market_type].append({
        "timestamp": now,
        "data": copy.deepcopy(market_data)
    })

def get_line_movement(game_id: str, market_type: str) -> str:
    hist = st.session_state.line_history.get(game_id, {}).get(market_type, [])
    if len(hist) < 2:
        return "No movement"
    prev = hist[-2]["data"]
    curr = hist[-1]["data"]
    changes = []
    for i, (p, c) in enumerate(zip(prev, curr)):
        # Compare first outcome odds/lines for each market
        prev_outcomes = p.get('outcomes', [])
        curr_outcomes = c.get('outcomes', [])
        for po, co in zip(prev_outcomes, curr_outcomes):
            if po.get("price") != co.get("price") or po.get("point") != co.get("point"):
                changes.append(f"{po.get('name')} {po.get('point','')}: {po.get('price')} → {co.get('price')}")
    return "; ".join(changes) if changes else "No movement"

# --- Predictive Model Stub (replace with your logic) ---
def predictive_model(game_id: str, market_type: str, market_data: List[Dict], history: List[Dict]) -> str:
    # Example: If line moved by more than 1.5 or odds shifted by 50+, flag it
    movement = get_line_movement(game_id, market_type)
    if "→" in movement:
        return f"⚡ Model Alert: Significant line/odds movement! ({movement})"
    return "No significant model signal."

# --- Streamlit UI ---
st.set_page_config(page_title="SportsGameOdds Dashboard", layout="wide")
st.title("🏟️ SportsGameOdds Dashboard")

leagues = ["NBA", "MLB", "NFL", "NCAAB", "WNBA"]
league = st.selectbox("Select League", leagues)

games = fetch_games(league)
game_options = {f"{g['home_team']} vs {g['away_team']} ({g['start_time']})": g['id'] for g in games}
game_label = st.selectbox("Select Game", list(game_options.keys()))
game_id = game_options[game_label]

if st.button("Fetch Markets"):
    # --- Moneyline ---
    st.subheader("Moneyline")
    ml = client.get_moneyline(league, game_id)
    update_line_history(game_id, "moneyline", ml)
    st.write(get_line_movement(game_id, "moneyline"))
    st.write(predictive_model(game_id, "moneyline", ml, st.session_state.line_history[game_id]["moneyline"]))
    if ml:
        ml_rows = []
        for m in ml:
            for outcome in m.get('outcomes', []):
                ml_rows.append({
                    "Team": outcome.get("name"),
                    "Odds": outcome.get("price"),
                    "Book": m.get("bookmaker")
                })
        st.table(pd.DataFrame(ml_rows))
    else:
        st.write("No moneyline data.")

    # --- Spread ---
    st.subheader("Spread")
    spreads = client.get_spreads(league, game_id)
    update_line_history(game_id, "spread", spreads)
    st.write(get_line_movement(game_id, "spread"))
    st.write(predictive_model(game_id, "spread", spreads, st.session_state.line_history[game_id]["spread"]))
    if spreads:
        sp_rows = []
        for m in spreads:
            for outcome in m.get('outcomes', []):
                sp_rows.append({
                    "Team": outcome.get("name"),
                    "Line": outcome.get("point"),
                    "Odds": outcome.get("price"),
                    "Book": m.get("bookmaker")
                })
        st.table(pd.DataFrame(sp_rows))
    else:
        st.write("No spread data.")

    # --- Totals ---
    st.subheader("Totals")
    totals = client.get_team_totals(league, game_id)
    update_line_history(game_id, "totals", totals)
    st.write(get_line_movement(game_id, "totals"))
    st.write(predictive_model(game_id, "totals", totals, st.session_state.line_history[game_id]["totals"]))
    if totals:
        tot_rows = []
        for m in totals:
            for outcome in m.get('outcomes', []):
                tot_rows.append({
                    "Team": outcome.get("name"),
                    "Line": outcome.get("point"),
                    "Odds": outcome.get("price"),
                    "Book": m.get("bookmaker")
                })
        st.table(pd.DataFrame(tot_rows))
    else:
        st.write("No totals data.")

    # --- Player Points ---
    st.subheader("Player Points Props")
    points_props = client.get_player_props(league, "points")
    update_line_history(game_id, "player_points", points_props)
    st.write(get_line_movement(game_id, "player_points"))
    st.write(predictive_model(game_id, "player_points", points_props, st.session_state.line_history[game_id]["player_points"]))
    if points_props:
        pt_rows = []
        for m in points_props:
            for outcome in m.get('outcomes', []):
                pt_rows.append({
                    "Player": outcome.get("name"),
                    "Line": outcome.get("point"),
                    "Odds": outcome.get("price"),
                    "Book": m.get("bookmaker")
                })
        st.table(pd.DataFrame(pt_rows))
    else:
        st.write("No player points props.")

    # --- Player Rebounds ---
    st.subheader("Player Rebounds Props")
    reb_props = client.get_player_props(league, "rebounds")
    update_line_history(game_id, "player_rebounds", reb_props)
    st.write(get_line_movement(game_id, "player_rebounds"))
    st.write(predictive_model(game_id, "player_rebounds", reb_props, st.session_state.line_history[game_id]["player_rebounds"]))
    if reb_props:
        reb_rows = []
        for m in reb_props:
            for outcome in m.get('outcomes', []):
                reb_rows.append({
                    "Player": outcome.get("name"),
                    "Line": outcome.get("point"),
                    "Odds": outcome.get("price"),
                    "Book": m.get("bookmaker")
                })
        st.table(pd.DataFrame(reb_rows))
    else:
        st.write("No player rebounds props.")

    # --- Player Assists ---
    st.subheader("Player Assists Props")
    ast_props = client.get_player_props(league, "assists")
    update_line_history(game_id, "player_assists", ast_props)
    st.write(get_line_movement(game_id, "player_assists"))
    st.write(predictive_model(game_id, "player_assists", ast_props, st.session_state.line_history[game_id]["player_assists"]))
    if ast_props:
        ast_rows = []
        for m in ast_props:
            for outcome in m.get('outcomes', []):
                ast_rows.append({
                    "Player": outcome.get("name"),
                    "Line": outcome.get("point"),
                    "Odds": outcome.get("price"),
                    "Book": m.get("bookmaker")
                })
        st.table(pd.DataFrame(ast_rows))
    else:
        st.write("No player assists props.")

st.info("Select a league and game, then click 'Fetch Markets' to view odds, props, line movement, and model signals.")

