import streamlit as st
import requests
import os
import pytz
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

# ======================
# ENHANCED CONFIGURATION
# ======================
class Config:
    # API Settings with multi-source key loading
    API_URL = "https://api.the-odds-api.com/v4"
    
    @classmethod 
    def get_api_key(cls):
        """Check all possible key locations"""
        # 1. Streamlit secrets (recommended)
        if 'ODDS_API_KEY' in st.secrets:
            return st.secrets['ODDS_API_KEY']
        
        # 2. Environment variable
        if 'ODDS_API_KEY' in os.environ:
            return os.environ['ODDS_API_KEY']
            
        # 3. Key file (for local development)
        try:
            with open('.odds_api_key') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    # App Constants
    TIMEZONE = pytz.timezone('US/Eastern')
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 10
    SPORTSBOOKS = ["FanDuel", "DraftKings", "BetMGM", "Caesars", "PointsBet"]

    # Expanded Sports Coverage
    SPORTS = {
        # Professional
        "MLB": "baseball_mlb",
        "NBA": "basketball_nba",
        "NFL": "americanfootball_nfl",
        "NHL": "icehockey_nhl",
        # College
        "NCAA Baseball": "baseball_ncaa", 
        "NCAA Football": "americanfootball_ncaaf",
        # International
        "NPB (Japan)": "baseball_japan_central_league"
    }

    # Comprehensive Baseball Props (25+ options)
    BASEBALL_PROPS = {
        # Hitting
        "batter_hits": "Hits",
        "batter_total_bases": "Total Bases",
        "batter_home_runs": "Home Runs",
        "batter_rbis": "RBIs",
        "batter_runs": "Runs",
        "batter_strikeouts": "Strikeouts",
        "batter_walks": "Walks",
        "batter_stolen_bases": "Stolen Bases",
        # Pitching
        "pitcher_strikeouts": "Pitcher Ks",
        "pitcher_earned_runs": "Earned Runs",
        "pitcher_hits_allowed": "Hits Allowed",
        "pitcher_walks_allowed": "Walks Allowed",
        # Game Specific
        "player_first_inning_hit": "1st Inning Hit",
        "player_to_record_hit": "Will Get a Hit",
        "player_to_hit_hr": "Will Hit HR",
        # Advanced
        "player_alt_total_hits": "Alt Hit Total",
        "player_alt_total_strikeouts": "Alt K Total"
    }

# ======================
# VALIDATION SYSTEM
# ======================
class APIValidator:
    @staticmethod
    def validate_key(key: str) -> dict:
        """Comprehensive API key validation"""
        result = {
            "valid": False,
            "reason": None,
            "remaining": None,
            "response_code": None
        }

        if not key:
            result["reason"] = "No key provided"
            return result

        if len(key) not in (32, 64):
            result["reason"] = f"Invalid length ({len(key)} chars)"
            return result

        if not key.isalnum():
            result["reason"] = "Contains special characters"
            return result

        try:
            response = requests.get(
                f"{Config.API_URL}/sports",
                params={"apiKey": key},
                timeout=Config.REQUEST_TIMEOUT
            )
            
            result["response_code"] = response.status_code
            result["remaining"] = response.headers.get("x-requests-remaining")
            
            if response.status_code == 200:
                result["valid"] = True
            else:
                result["reason"] = f"API rejected key (HTTP {response.status_code})"
                
        except Exception as e:
            result["reason"] = f"Connection failed: {str(e)}"
            
        return result

# ======================
# DATA MODELS
# ======================
class PlayerProp:
    def __init__(self, data: dict):
        self.player = data.get("player", "Unknown")
        self.market = data.get("market", "unknown")
        self.line = data.get("point")
        self.odds = data.get("price")
        self.book = data.get("book")

class Game:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.sport_key = data["sport_key"]
        self.home = data["home_team"]
        self.away = data["away_team"]
        self.start_time = self._parse_time(data["commence_time"])
        self.odds = self._parse_odds(data["bookmakers"])
        self.props = self._parse_props(data["bookmakers"])

    def _parse_time(self, time_str: str) -> datetime:
        dt = datetime.fromisoformat(time_str[:-1]).astimezone(pytz.utc)
        return dt.astimezone(Config.TIMEZONE)

    def _parse_odds(self, bookmakers: List[dict]) -> dict:
        return {
            book["key"]: {
                "moneyline": next((m for m in book["markets"] if m["key"] == "h2h"), None),
                "spread": next((m for m in book["markets"] if m["key"] == "spreads"), None),
                "total": next((m for m in book["markets"] if m["key"] == "totals"), None)
            }
            for book in bookmakers 
            if book["key"] in Config.SPORTSBOOKS
        }

    def _parse_props(self, bookmakers: List[dict]) -> List[PlayerProp]:
        props = []
        for book in bookmakers:
            for market in book["markets"]:
                if market["key"] in Config.BASEBALL_PROPS:
                    for outcome in market["outcomes"]:
                        props.append(PlayerProp({
                            "player": outcome["description"] or outcome["name"],
                            "market": market["key"],
                            "point": outcome.get("point"),
                            "price": outcome.get("price"),
                            "book": book["key"]
                        }))
        return props

# ======================
# CORE FUNCTIONALITY
# ======================
class OddsApp:
    def __init__(self):
        self.api_key = Config.get_api_key()
        self._validate_key()
        self._init_ui()
        self._init_session()

    def _validate_key(self):
        """Validate API key before proceeding"""
        validation = APIValidator.validate_key(self.api_key)
        
        if not validation["valid"]:
            st.error(f"""
            ❌ API Key Validation Failed:
            - Reason: {validation["reason"]}
            - Response Code: {validation.get("response_code", "N/A")}
            """)
            st.stop()
            
        st.session_state.remaining_requests = validation["remaining"]
        st.success(f"✅ API Key Valid (Remaining: {validation['remaining']})")

    def _init_ui(self):
        """Initialize UI components"""
        st.set_page_config(
            layout="wide",
            page_title="Odds Tracker Pro",
            page_icon="📊"
        )
        
        st.title("⚾ Complete Odds Tracker")
        st.sidebar.title("Controls")

    def _init_session(self):
        """Initialize session state"""
        if "games" not in st.session_state:
            st.session_state.games = {}
        if "selected_sport" not in st.session_state:
            st.session_state.selected_sport = "MLB"

    def _render_controls(self):
        """Render sidebar controls"""
        with st.sidebar:
            st.selectbox(
                "Select Sport",
                list(Config.SPORTS.keys()),
                key="selected_sport"
            )
            
            st.multiselect(
                "Sportsbooks",
                Config.SPORTSBOOKS,
                default=Config.SPORTSBOOKS,
                key="selected_books"
            )
            
            if st.button("🔄 Refresh Data"):
                self._fetch_games()

    def _fetch_games(self):
        """Fetch games from API"""
        try:
            sport_key = Config.SPORTS[st.session_state.selected_sport]
            response = requests.get(
                f"{Config.API_URL}/sports/{sport_key}/odds",
                params={
                    "apiKey": self.api_key,
                    "regions": "us",
                    "markets": ",".join(["h2h", "spreads", "totals"] + list(Config.BASEBALL_PROPS.keys())),
                    "oddsFormat": "american"
                },
                timeout=Config.REQUEST_TIMEOUT
            )
            
            response.raise_for_status()
            st.session_state.games = [Game(g) for g in response.json()]
            
        except Exception as e:
            st.error(f"Failed to fetch games: {str(e)}")

    def _render_game(self, game: Game):
        """Render individual game card"""
        with st.expander(f"{game.away} @ {game.home} | {game.start_time:%m/%d %I:%M %p}"):
            # Main odds table
            st.subheader("Game Odds")
            odds_data = []
            
            for book in st.session_state.selected_books:
                if book in game.odds:
                    odds = game.odds[book]
                    odds_data.append({
                        "Sportsbook": book,
                        "Moneyline (Away)": next((o["price"] for o in odds["moneyline"]["outcomes"] if o["name"] == game.away), None),
                        "Moneyline (Home)": next((o["price"] for o in odds["moneyline"]["outcomes"] if o["name"] == game.home), None),
                        "Spread": f"{next((o['point'] for o in odds['spread']['outcomes'] if o['name'] == game.away), '')} ({next((o['price'] for o in odds['spread']['outcomes'] if o['name'] == game.away), '')})",
                        "Total": f"O {next((o['point'] for o in odds['total']['outcomes'] if o['name'] == 'Over'), '')} ({next((o['price'] for o in odds['total']['outcomes'] if o['name'] == 'Over'), '')})"
                    })
            
            st.dataframe(pd.DataFrame(odds_data))
            
            # Player props section
            if game.props:
                st.subheader("⚾ Player Props")
                for prop_type in set(p.market for p in game.props):
                    st.markdown(f"**{Config.BASEBALL_PROPS.get(prop_type, prop_type)}**")
                    prop_data = [
                        {
                            "Player": p.player,
                            "Line": p.line,
                            "Odds": p.odds,
                            "Book": p.book
                        } 
                        for p in game.props 
                        if p.market == prop_type
                    ]
                    st.dataframe(pd.DataFrame(prop_data))

    def run(self):
        """Main app loop"""
        self._render_controls()
        self._fetch_games()
        
        if not st.session_state.games:
            st.warning("No games found for selected sport")
            return
            
        for game in st.session_state.games:
            self._render_game(game)

if __name__ == "__main__":
    app = OddsApp()
    app.run()
