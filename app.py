import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

# ======================
# CONFIGURATION (ONLY FIXED MARKET NAMES)
# ======================
class Config:
    API_URL = "https://api.the-odds-api.com/v4"
    API_KEY = "17e75d302045aed4532e57f97d6609e3"  # Your actual key
    
    # App Settings (unchanged)
    TIMEZONE = pytz.timezone('US/Eastern')
    SPORTSBOOKS = ["fanduel", "draftkings", "betmgm", "pointsbet"]
    
    # ONLY CHANGE: Fixed typos in these market names
    MARKETS = [
        "h2h", "spreads", "totals",           # Game lines
        "batter_hits",                         # Hitting props
        "batter_total_bases", 
        "batter_home_runs",
        "batter_rbis",                         # WAS "rhis" (fixed)
        "batter_runs",
        "batter_strikeouts",
        "pitcher_strikeouts",                  # Pitching props
        "pitcher_earned_runs"                  # WAS "earn_ed_runs" (fixed)
    ]

# ======================
# ORIGINAL GAME CLASS (UNCHANGED)
# ======================
class Game:
    def __init__(self, data):
        self.id = data['id']
        self.sport_key = data['sport_key']
        self.home = data['home_team']
        self.away = data['away_team']
        self.start_time = self._parse_time(data['commence_time'])
        self.odds = self._parse_odds(data['bookmakers'])

    def _parse_time(self, time_str):
        dt = datetime.fromisoformat(time_str[:-1]).astimezone(pytz.utc)
        return dt.astimezone(Config.TIMEZONE)

    def _parse_odds(self, bookmakers):
        odds_data = {}
        for book in bookmakers:
            if book['key'] in Config.SPORTSBOOKS:
                odds_data[book['key']] = {
                    'moneyline': next((m for m in book['markets'] if m['key'] == 'h2h'), None),
                    'totals': next((m for m in book['markets'] if m['key'] == 'totals'), None),
                    'spreads': next((m for m in book['markets'] if m['key'] == 'spreads'), None),
                    'player_props': {
                        prop: next((m for m in book['markets'] if m['key'] == prop), None)
                        for prop in Config.MARKETS 
                        if prop not in ['h2h', 'totals', 'spreads']
                    }
                }
        return odds_data

# ======================
# ORIGINAL FETCH FUNCTION (WITH 422 FIX)
# ======================
def fetch_games():
    try:
        response = requests.get(
            f"{Config.API_URL}/sports/baseball_mlb/odds",
            params={
                'apiKey': Config.API_KEY,
                'regions': 'us',
                'markets': ','.join(Config.MARKETS),
                'oddsFormat': 'american',
                'bookmakers': ','.join(Config.SPORTSBOOKS)
            },
            timeout=10
        )
        
        if response.status_code == 422:
            st.error("API rejected our request. Please verify:")
            st.error(f"- Market names: {Config.MARKETS}")
            return None
            
        response.raise_for_status()
        return [Game(game) for game in response.json()]
        
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")
        return None

# ======================
# YOUR ORIGINAL DASHBOARD (UNCHANGED)
# ======================
def main():
    st.set_page_config(layout="wide", page_title="MLB Odds Dashboard")
    st.title("MLB Odds Dashboard")
    
    # Your original file upload section
    with st.expander("📁 Upload Custom Data", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload your data (CSV/JSON)", 
            type=["csv", "json"],
            key="file_uploader_original"
        )
        if uploaded_file:
            st.success(f"Uploaded: {uploaded_file.name}")
    
    # Your original odds display
    if st.button("🔄 Refresh Odds", key="original_refresh_button"):
        games = fetch_games()
        
        if games:
            for game in games:
                with st.expander(f"{game.away} @ {game.home} | {game.start_time.strftime('%m/%d %I:%M %p ET')}"):
                    # Game lines table (original)
                    st.subheader("Game Lines")
                    lines_data = []
                    for book, odds in game.odds.items():
                        lines_data.append({
                            "Sportsbook": book.title(),
                            "Away ML": next((o['price'] for o in odds['moneyline']['outcomes'] if o['name'] == game.away), "N/A"),
                            "Home ML": next((o['price'] for o in odds['moneyline']['outcomes'] if o['name'] == game.home), "N/A"),
                            "Spread": f"{next((o['point'] for o in odds['spreads']['outcomes'] if o['name'] == game.away), 'N/A')} ({next((o['price'] for o in odds['spreads']['outcomes'] if o['name'] == game.away), 'N/A')})",
                            "Total": f"O {next((o['point'] for o in odds['totals']['outcomes'] if o['name'] == 'Over'), 'N/A')} ({next((o['price'] for o in odds['totals']['outcomes'] if o['name'] == 'Over'), 'N/A')})"
                        })
                    st.dataframe(pd.DataFrame(lines_data))
                    
                    # Player props table (original)
                    st.subheader("Player Props")
                    prop_data = []
                    for book, odds in game.odds.items():
                        for prop_name, market in odds['player_props'].items():
                            if market:
                                for outcome in market['outcomes']:
                                    prop_data.append({
                                        "Sportsbook": book.title(),
                                        "Player": outcome.get('description', outcome.get('name')),
                                        "Prop": prop_name.replace('_', ' ').title(),
                                        "Line": outcome.get('point', 'N/A'),
                                        "Odds": outcome.get('price', 'N/A')
                                    })
                    if prop_data:
                        st.dataframe(pd.DataFrame(prop_data))
                    else:
                        st.warning("No player props available")

if __name__ == "__main__":
    main()
