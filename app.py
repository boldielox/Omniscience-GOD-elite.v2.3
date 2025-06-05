import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import copy

# ---- SportsGameOddsClient (no API key hardcoded) ----
class SportsGameOddsClient:
    BASE_URL = "https://api.sportsgameodds.com/v2"

    def __init__(self, api_key):
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": api_key})

    def get_sports(self):
        url = f"{self.BASE_URL}/sports/"
        return self.session.get(url).json()

    def get_games(self, league):
        url = f"{self.BASE_URL}/games/{league}/"
        return self.session.get(url).json()

    def get_moneyline(self, league, game_id):
        url = f"{self.BASE_URL}/markets/{league}/game/{game_id}/moneyline"
        params = {
            "statID": "points",
            "betTypeID": "ml",
            "periodID": "reg",
            "statEntityIDs": "home,away"
        }
        resp = self.session.get(url, params=params)
        return resp.json().get("markets", [])

    def get_player_rebounds(self, league, game_id):
        url = f"{self.BASE_URL}/markets/{league}/game/{game_id}/player/rebounds"
        params = {
            "statID": "rebounds",
            "betTypeID": "ou",
            "periodID": "game",
            "statEntityID": "ANY_PLAYER_ID"
        }
        resp = self.session.get(url, params=params)
        return resp.json().get("markets", [])

    def get_player_assists(self, league, game_id):
        url = f"{self.BASE_URL}/markets/{league}/game/{game_id}/player/assists"
        params = {
            "statID": "assists",
            "betTypeID": "ou",
            "periodID": "game",
            "statEntityID": "ANY_PLAYER_ID"
        }
        resp = self.session.get(url, params=params)
        return resp.json().get("markets", [])

# ---- Line Movement Tracker ----
def update_line_history(game_id, market_type, market_data):
    now = datetime.utcnow().isoformat()
    if 'line_history' not in st.session_state:
        st.session_state.line_history = {}
    if game_id not in st.session_state.line_history:
        st.session_state.line_history[game_id] = {}
    if market_type not in st.session_state.line_history[game_id]:
        st.session_state.line_history[game_id][market_type] = []
    st.session_state.line_history[game_id][market_type].append({
        "timestamp": now,
        "data": copy.deepcopy(market_data)
    })

def get_line_movement(game_id, market_type):
    hist = st.session_state.line_history.get(game_id, {}).get(market_type, [])
    if len(hist) < 2:
        return "No movement"
    prev = hist[-2]["data"]
    curr = hist[-1]["data"]
    changes = []
    for i, (p, c) in enumerate(zip(prev, curr)):
        prev_outcomes = p.get('outcomes', [])
        curr_outcomes = c.get('outcomes', [])
        for po, co in zip(prev_outcomes, curr_outcomes):
            if po.get("price") != co.get("price") or po.get("point") != co.get("point"):
                changes.append(f"{po.get('name')} {po.get('point','')}: {po.get('price')} → {co.get('price')}")
    return "; ".join(changes) if changes else "No movement"

# ---- Predictive & Analysis Engines (customize as needed) ----
def predictive_engine(game_id, market_type, market_data):
    movement = get_line_movement(game_id, market_type)
    if "→" in movement:
        return f"⚡ Predictive Alert: {movement}"
    return "No significant predictive signal."

def analysis_engine(game_id, market_type, market_data):
    if not market_data:
        return "No data for analysis."
    avg_odds = []
    for m in market_data:
        for o in m.get('outcomes', []):
            if o.get("price"):
                avg_odds.append(float(o["price"]))
    if avg_odds:
        avg = sum(avg_odds) / len(avg_odds)
        return f"Avg Odds: {avg:.1f}"
    return "No odds to analyze."

# ---- Streamlit UI ----
st.set_page_config(page_title="SportsGameOdds Dashboard", layout="wide")
st.title("🏟️ SportsGameOdds Dashboard")

client = SportsGameOddsClient(st.secrets["SPORTSGAME_API_KEY"])

sports = client.get_sports()
leagues = [s['id'] for s in sports] if isinstance(sports, list) else []
league = st.selectbox("Select League", leagues)

games = client.get_games(league) if league else []
game_options = {f"{g['home_team']} vs {g['away_team']} ({g['start_time']})": g['id'] for g in games} if games else {}
game_label = st.selectbox("Select Game", list(game_options.keys()))
game_id = game_options.get(game_label)

if st.button("Fetch Markets") and game_id:
    # --- Moneyline ---
    st.subheader("Moneyline")
    ml = client.get_moneyline(league, game_id)
    update_line_history(game_id, "moneyline", ml)
    st.write("Line Movement:", get_line_movement(game_id, "moneyline"))
    st.write("Predictive Engine:", predictive_engine(game_id, "moneyline", ml))
    st.write("Analysis Engine:", analysis_engine(game_id, "moneyline", ml))
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

    # --- Player Rebounds ---
    st.subheader("Player Rebounds Props")
    reb_props = client.get_player_rebounds(league, game_id)
    update_line_history(game_id, "player_rebounds", reb_props)
    st.write("Line Movement:", get_line_movement(game_id, "player_rebounds"))
    st.write("Predictive Engine:", predictive_engine(game_id, "player_rebounds", reb_props))
    st.write("Analysis Engine:", analysis_engine(game_id, "player_rebounds", reb_props))
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
    ast_props = client.get_player_assists(league, game_id)
    update_line_history(game_id, "player_assists", ast_props)
    st.write("Line Movement:", get_line_movement(game_id, "player_assists"))
    st.write("Predictive Engine:", predictive_engine(game_id, "player_assists", ast_props))
    st.write("Analysis Engine:", analysis_engine(game_id, "player_assists", ast_props))
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

st.info("Select a league and game, then click 'Fetch Markets' to view odds, props, line movement, and engine signals.")
