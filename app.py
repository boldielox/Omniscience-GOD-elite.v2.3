import streamlit as st
import pandas as pd
from typing import Optional

# ---- Paste your SportsGameOddsClient class here ----

# Example: from your previous code
# class SportsGameOddsClient: ...

API_KEY = st.secrets.get("SPORTSGAME_API_KEY", "your_api_key_here")
client = SportsGameOddsClient(API_KEY)

st.set_page_config(page_title="SportsGameOdds Dashboard", layout="wide")
st.title("🏟️ SportsGameOdds Dashboard")

# --- League Selection ---
leagues = {
    'MLB': 'MLB',
    'NBA': 'NBA',
    'NFL': 'NFL',
    'NCAAB': 'NCAAB',
    'WNBA': 'WNBA'
}
league = st.selectbox("Select League", list(leagues.keys()))

# --- Fetch Games (you may need to implement this method to get game IDs) ---
def fetch_games(league: str):
    # You must implement this method to list games and their IDs
    # Here is a dummy list for demonstration
    # Replace with a real API call if available!
    return [
        {"id": "12345", "home_team": "Lakers", "away_team": "Celtics", "start_time": "2025-06-06T19:00:00Z"},
        {"id": "67890", "home_team": "Yankees", "away_team": "Red Sox", "start_time": "2025-06-06T20:00:00Z"}
    ]
games = fetch_games(league)
game_options = {f"{g['home_team']} vs {g['away_team']} ({g['start_time']})": g['id'] for g in games}
game_label = st.selectbox("Select Game", list(game_options.keys()))
game_id = game_options[game_label]

# --- Fetch and Display Markets ---
if st.button("Fetch Markets"):
    st.subheader("Moneyline")
    ml = client.get_moneyline(league, game_id)
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

    st.subheader("Spread")
    spreads = client.get_spreads(league, game_id)
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

    st.subheader("Totals")
    totals = client.get_team_totals(league, game_id)
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

    st.subheader("Player Points Props")
    points_props = client.get_player_props(league, "points")
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

    st.subheader("Player Rebounds Props")
    reb_props = client.get_player_props(league, "rebounds")
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

    st.subheader("Player Assists Props")
    ast_props = client.get_player_props(league, "assists")
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

st.info("Select a league and game, then click 'Fetch Markets' to view odds and props.")

