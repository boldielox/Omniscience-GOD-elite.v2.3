import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd
import traceback
from typing import List, Dict, Optional

# ======================
# ENHANCED CONFIGURATION
# ======================
class Config:
    # API Settings with detailed validation
    API_URL = "https://api.the-odds-api.com/v4"
    API_KEY = None  # Will be initialized with validation
    
    # App Settings
    MAX_GAMES = 50
    TIMEZONE = pytz.timezone('US/Eastern')
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 10

    # Comprehensive Sports Coverage
    SPORTS = {
        # Professional Leagues
        "MLB": "baseball_mlb",
        "NBA": "basketball_nba", 
        "NFL": "americanfootball_nfl",
        "NHL": "icehockey_nhl",
        "WNBA": "basketball_wnba",
        
        # College Sports
        "NCAA Baseball": "baseball_ncaa",
        "NCAA Football": "americanfootball_ncaaf",
        "NCAA Basketball": "basketball_ncaab",
        
        # International
        "NPB (Japan)": "baseball_japan_central_league",
        "KBO (Korea)": "baseball_korea_league"
    }

    SPORTSBOOKS = ["FanDuel", "DraftKings", "BetMGM", "Caesars", "PointsBet", "BetRivers"]

    # Expanded Baseball Player Props (25+ options)
    BASEBALL_PROPS = {
        "player_hits": "Hits",
        "player_total_bases": "Total Bases",
        "player_home_runs": "Home Runs",
        "player_rbis": "RBIs",
        "player_runs": "Runs Scored",
        "player_stolen_bases": "Stolen Bases",
        "player_walks": "Walks",
        "player_strikeouts": "Strikeouts",
        "player_pitcher_strikeouts": "Pitcher Strikeouts",
        "player_pitcher_earned_runs": "Earned Runs",
        "player_pitcher_hits_allowed": "Hits Allowed",
        "player_pitcher_walks_allowed": "Walks Allowed",
        "player_pitcher_outs": "Outs Recorded",
        "player_to_record_hit": "To Record a Hit",
        "player_to_hit_hr": "To Hit HR",
        "player_alt_total_hits": "Alternate Hit Total",
        "player_alt_total_strikeouts": "Alternate Strikeout Total",
        "player_game_rbis": "Game RBIs",
        "player_game_strikeouts": "Game Strikeouts",
        "player_first_inning_hit": "1st Inning Hit",
        "player_first_pitch_result": "First Pitch Result"
    }

    # Combined markets
    MARKETS = ["h2h", "totals", "spreads"] + list(BASEBALL_PROPS.keys())

    @classmethod
    def initialize(cls):
        """Initialize API key with validation"""
        cls.API_KEY = st.secrets.get("ODDS_API_KEY")
        if not cls.API_KEY:
            st.error("❌ API Key Missing: Add ODDS_API_KEY to Streamlit secrets")
            return False
        return True

# ======================
# ENHANCED API SERVICE
# ======================
class OddsAPI:
    @staticmethod
    def diagnose_key(key: str) -> Dict:
        """Comprehensive API key diagnostics"""
        diagnostics = {
            "valid_length": len(key) in (32, 64),
            "is_alnum": key.isalnum(),
            "test_response": None,
            "remaining_requests": None,
            "error": None
        }

        try:
            response = requests.get(
                f"{Config.API_URL}/sports",
                params={'apiKey': key},
                timeout=Config.REQUEST_TIMEOUT
            )
            
            diagnostics["test_response"] = response.status_code
            diagnostics["remaining_requests"] = response.headers.get('x-requests-remaining')
            
            if response.status_code == 401:
                diagnostics["error"] = "Invalid or unauthorized key"
            elif response.status_code == 429:
                diagnostics["error"] = "Rate limit exceeded"
            elif response.status_code >= 500:
                diagnostics["error"] = "Server error"
                
        except Exception as e:
            diagnostics["error"] = str(e)
            
        return diagnostics

    @staticmethod
    def verify_key() -> bool:
        """Enhanced key verification with diagnostics"""
        if not Config.API_KEY:
            st.error("API key not initialized")
            return False

        diagnostics = OddsAPI.diagnose_key(Config.API_KEY)
        
        if diagnostics["error"]:
            st.error(f"🔍 Key Diagnostics Failed: {diagnostics['error']}")
            st.json(diagnostics)
            return False
            
        if not diagnostics["valid_length"]:
            st.error("❌ Invalid Key Length (expected 32-64 chars)")
            return False
            
        if not diagnostics["is_alnum"]:
            st.error("❌ Key contains invalid characters (letters and numbers only)")
            return False
            
        st.success(f"✅ API Key Valid (Remaining: {diagnostics['remaining_requests']})")
        return True

    @staticmethod
    def fetch_games(sport_key: str) -> List[Dict]:
        """Fetch games with enhanced error handling"""
        try:
            params = {
                'apiKey': Config.API_KEY,
                'regions': 'us',
                'markets': ','.join(Config.MARKETS),
                'oddsFormat': 'american'
            }
            
            response = requests.get(
                f"{Config.API_URL}/sports/{sport_key}/odds",
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            st.error(f"API Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            st.error(f"Connection Error: {str(e)}")
            
        return []

# ======================
# DATA MODELS
# ======================
class PlayerProp:
    def __init__(self, data: Dict):
        self.player = data.get('player_name', 'Unknown')
        self.market = data.get('market_key', 'unknown')
        self.line = data.get('line', 'N/A')
        self.odds = data.get('odds', 'N/A')
        self.sportsbook = data.get('sportsbook', 'Unknown')

class Game:
    def __init__(self, data: Dict):
        self.id = data.get('id')
        self.sport_key = data.get('sport_key')
        self.home_team = data.get('home_team', 'Unknown')
        self.away_team = data.get('away_team', 'Unknown')
        self.start_time = self._parse_time(data.get('commence_time'))
        self.player_props = self._parse_player_props(data.get('bookmakers', []))
        
    def _parse_time(self, time_str: str) -> datetime:
        try:
            dt = datetime.fromisoformat(time_str[:-1]).astimezone(pytz.utc)
            return dt.astimezone(Config.TIMEZONE)
        except:
            return datetime.now(Config.TIMEZONE)
            
    def _parse_player_props(self, bookmakers: List) -> List[PlayerProp]:
        props = []
        for bookmaker in bookmakers:
            for market in bookmaker.get('markets', []):
                if market.get('key') in Config.BASEBALL_PROPS:
                    for outcome in market.get('outcomes', []):
                        props.append(PlayerProp({
                            'player_name': outcome.get('description', outcome.get('name')),
                            'market_key': market['key'],
                            'line': outcome.get('point'),
                            'odds': outcome.get('price'),
                            'sportsbook': bookmaker.get('key')
                        }))
        return props

# ======================
# UI COMPONENTS
# ======================
def render_key_diagnostics():
    if st.button("Run API Key Diagnostics"):
        diagnostics = OddsAPI.diagnose_key(Config.API_KEY)
        
        st.subheader("🔍 API Key Diagnostics")
        cols = st.columns(2)
        
        with cols[0]:
            st.metric("Key Length", len(Config.API_KEY))
            st.metric("Alphanumeric", diagnostics["is_alnum"])
            
        with cols[1]:
            st.metric("Test Response", diagnostics["test_response"])
            st.metric("Remaining Requests", diagnostics["remaining_requests"])
            
        st.json(diagnostics)

def render_player_props_table(props: List[PlayerProp]):
    if not props:
        return
        
    df = pd.DataFrame([{
        'Player': p.player,
        'Prop': Config.BASEBALL_PROPS.get(p.market, p.market),
        'Line': p.line,
        'Odds': p.odds,
        'Sportsbook': p.sportsbook
    } for p in props])
    
    st.dataframe(
        df.style.format({'Odds': '{:+d}'}),
        height=min(600, 35 * len(df)),
        use_container_width=True
    )

# ======================
# MAIN APP
# ======================
def main():
    st.set_page_config(
        layout="wide",
        page_title="Baseball Odds Tracker",
        page_icon="⚾"
    )
    
    # Initialize with key validation
    if not Config.initialize():
        st.stop()
        
    if not OddsAPI.verify_key():
        render_key_diagnostics()
        st.stop()
    
    # Sport selection
    selected_sport = st.selectbox(
        "Select Sport",
        list(Config.SPORTS.keys()),
        index=0
    )
    
    # Fetch and display games
    games_data = OddsAPI.fetch_games(Config.SPORTS[selected_sport])
    games = [Game(g) for g in games_data[:Config.MAX_GAMES]]
    
    for game in games:
        with st.expander(f"{game.away_team} @ {game.home_team}"):
            st.write(f"⏰ {game.start_time.strftime('%m/%d %I:%M %p ET')}")
            
            if game.player_props:
                st.subheader("⚾ Player Props")
                render_player_props_table(game.player_props)
            else:
                st.warning("No player props available for this game")

if __name__ == "__main__":
    main()
