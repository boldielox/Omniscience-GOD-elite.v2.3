import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd
from typing import List, Dict, Optional

# ======================
# CONFIGURATION (WITH FIXED MARKET NAMES)
# ======================
class Config:
    API_URL = "https://api.the-odds-api.com/v4"
    API_KEY = "17e75d302045aed4532e57f97d6609e3"  # Your actual key here
    
    # App Settings
    TIMEZONE = pytz.timezone('US/Eastern')
    SPORTSBOOKS = ["fanduel", "draftkings", "betmgm", "pointsbet"]
    
    # CORRECTED market names (fixed typos that caused 422 errors)
    MARKETS = {
        "game": ["h2h", "spreads", "totals"],
        "batter": [
            "batter_hits",
            "batter_total_bases", 
            "batter_home_runs",
            "batter_rbis",  # Fixed from "rhis"
            "batter_runs",
            "batter_strikeouts"
        ],
        "pitcher": [
            "pitcher_strikeouts",
            "pitcher_earned_runs"  # Fixed from "earn_ed_runs"
        ]
    }

# ======================
# DATA MODELS (ORIGINAL STRUCTURE)
# ======================
class PlayerProp:
    def __init__(self, data: Dict):
        self.player = data.get("player_name", "Unknown")
        self.market = data.get("market_key", "unknown")
        self.line = data.get("point", "N/A")
        self.odds = data.get("price", "N/A")
        self.book = data.get("bookmaker", "Unknown")

class Game:
    def __init__(self, data: Dict):
        self.id = data["id"]
        self.sport_key = data["sport_key"]
        self.home = data["home_team"]
        self.away = data["away_team"]
        self.start_time = self._parse_time(data["commence_time"])
        self.odds = self._parse_odds(data["bookmakers"])
        self.props = self._parse_props(data["bookmakers"])

    def _parse_time(self, time_str: str) -> datetime:
        try:
            dt = datetime.fromisoformat(time_str[:-1]).astimezone(pytz.UTC)
            return dt.astimezone(Config.TIMEZONE)
        except:
            return datetime.now()

    def _parse_odds(self, bookmakers: List) -> Dict:
        odds_data = {}
        for book in bookmakers:
            if book["key"] in Config.SPORTSBOOKS:
                odds_data[book["key"]] = {
                    "moneyline": next((m for m in book["markets"] if m["key"] == "h2h"), None),
                    "spread": next((m for m in book["markets"] if m["key"] == "spreads"), None),
                    "total": next((m for m in book["markets"] if m["key"] == "totals"), None)
                }
        return odds_data

    def _parse_props(self, bookmakers: List) -> List[PlayerProp]:
        props = []
        for book in bookmakers:
            if book["key"] in Config.SPORTSBOOKS:
                for market in book["markets"]:
                    if market["key"] in Config.MARKETS["batter"] + Config.MARKETS["pitcher"]:
                        for outcome in market["outcomes"]:
                            props.append(PlayerProp({
                                "player_name": outcome.get("description", outcome.get("name")),
                                "market_key": market["key"],
                                "point": outcome.get("point"),
                                "price": outcome.get("price"),
                                "bookmaker": book["key"]
                            }))
        return props

# ======================
# API SERVICE (WITH ERROR HANDLING)
# ======================
def fetch_games() -> Optional[List[Game]]:
    """Original fetch function with 422 fixes"""
    try:
        all_markets = Config.MARKETS["game"] + Config.MARKETS["batter"] + Config.MARKETS["pitcher"]
        
        response = requests.get(
            f"{Config.API_URL}/sports/baseball_mlb/odds",
            params={
                "apiKey": Config.API_KEY,
                "regions": "us",
                "markets": ",".join(all_markets),
                "oddsFormat": "american",
                "bookmakers": ",".join(Config.SPORTSBOOKS)
            },
            timeout=15
        )

        if response.status_code == 422:
            error_detail = response.json().get("detail", "Invalid market names")
            st.error(f"API Validation Error: {error_detail}")
            st.error("Please check your market names in Config.MARKETS")
            return None
            
        response.raise_for_status()
        return [Game(game) for game in response.json()]
        
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed: {str(e)}")
        return None

# ======================
# STREAMLIT UI (ORIGINAL LAYOUT)
# ======================
def main():
    st.set_page_config(
        layout="wide",
        page_title="MLB Odds Tracker",
        page_icon="⚾",
        initial_sidebar_state="expanded"
    )
    
    st.title("MLB Odds Tracker")
    st.markdown("---")
    
    # File upload section (original)
    with st.expander("📁 Upload Custom Data", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload your own odds data (CSV/JSON)",
            type=["csv", "json"],
            key="file_uploader"
        )
        if uploaded_file:
            st.success(f"Successfully uploaded {uploaded_file.name}")
            # Add your file processing logic here
    
    # Live odds section (original)
    with st.expander("⚾ Live MLB Odds", expanded=True):
        if st.button("🔄 Refresh Odds", key="refresh_button"):
            with st.spinner("Fetching latest odds..."):
                games = fetch_games()
                
                if games:
                    for game in games:
                        render_game(game)
                else:
                    st.warning("No games available or failed to load data")

def render_game(game: Game):
    """Original game display logic"""
    with st.expander(f"{game.away} @ {game.home} | {game.start_time.strftime('%m/%d %I:%M %p ET')}"):
        # Game lines table (original)
        st.subheader("Game Lines")
        lines_data = []
        for book, odds in game.odds.items():
            lines_data.append({
                "Sportsbook": book.title(),
                "Away ML": next((o["price"] for o in odds["moneyline"]["outcomes"] if o["name"] == game.away), "N/A"),
                "Home ML": next((o["price"] for o in odds["moneyline"]["outcomes"] if o["name"] == game.home), "N/A"),
                "Spread": f"{next((o['point'] for o in odds['spread']['outcomes'] if o['name'] == game.away), 'N/A')} ({next((o['price'] for o in odds['spread']['outcomes'] if o['name'] == game.away), 'N/A')})",
                "Total": f"O {next((o['point'] for o in odds['total']['outcomes'] if o['name'] == 'Over'), 'N/A')} ({next((o['price'] for o in odds['total']['outcomes'] if o['name'] == 'Over'), 'N/A')})"
            })
        st.dataframe(pd.DataFrame(lines_data))
        
        # Player props table (original)
        st.subheader("Player Props")
        if game.props:
            prop_data = []
            for prop in game.props:
                prop_data.append({
                    "Player": prop.player,
                    "Prop": Config.MARKETS["batter" if prop.market.startswith("batter") else "pitcher"][prop.market],
                    "Line": prop.line,
                    "Odds": prop.odds,
                    "Book": prop.book.title()
                })
            st.dataframe(pd.DataFrame(prop_data))
        else:
            st.warning("No player props available for this game")

if __name__ == "__main__":
    main()
