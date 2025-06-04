import streamlit as st
import requests
import os
import pytz
import pandas as pd
from datetime import datetime
from typing import List, Dict

# ======================
# API KEY MANAGEMENT SYSTEM
# ======================
class APIKeyManager:
    @staticmethod
    def find_api_key():
        """Check all possible key locations with detailed tracing"""
        sources = [
            ("Streamlit secrets", lambda: st.secrets.get("ODDS_API_KEY")),
            ("Environment variable", lambda: os.environ.get("ODDS_API_KEY")),
            ("Local key file", lambda: APIKeyManager._read_key_file()),
            ("Session state", lambda: st.session_state.get("ODDS_API_KEY"))
        ]

        for source_name, getter in sources:
            key = getter()
            if key:
                st.session_state.key_source = source_name
                st.session_state.key_debug = f"Found in {source_name}"
                return key.strip()

        st.session_state.key_debug = "Key not found in any location"
        return None

    @staticmethod
    def _read_key_file():
        try:
            with open('.odds_api_key') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    @staticmethod
    def validate_key(key: str) -> Dict:
        """Comprehensive validation with API test call"""
        validation = {
            'valid': False,
            'error': None,
            'details': {
                'length': len(key) if key else 0,
                'format': 'alphanumeric' if key and key.isalnum() else 'invalid',
                'source': st.session_state.get('key_source')
            }
        }

        # Basic checks
        if not key:
            validation['error'] = "No key provided"
            return validation
        if len(key) not in (32, 64):
            validation['error'] = f"Invalid length ({len(key)} chars, expected 32/64)"
            return validation
        if not key.isalnum():
            validation['error'] = "Key contains special characters (letters/numbers only)"
            return validation

        # API test call
        try:
            response = requests.get(
                "https://api.the-odds-api.com/v4/sports",
                params={"apiKey": key},
                timeout=10
            )
            validation['details']['api_response'] = response.status_code
            validation['details']['remaining'] = response.headers.get("x-requests-remaining")

            if response.status_code == 200:
                validation['valid'] = True
            else:
                validation['error'] = f"API rejected key (HTTP {response.status_code})"
        except Exception as e:
            validation['error'] = f"Connection failed: {str(e)}"

        return validation

# ======================
# DATA MODELS & CONFIG
# ======================
class Config:
    SPORTS = {
        "MLB": "baseball_mlb",
        "NBA": "basketball_nba",
        "NFL": "americanfootball_nfl",
        "NHL": "icehockey_nhl",
        "NCAA Baseball": "baseball_ncaa",
        "NPB (Japan)": "baseball_japan_central_league"
    }

    SPORTSBOOKS = ["FanDuel", "DraftKings", "BetMGM", "Caesars", "PointsBet"]

    BASEBALL_PROPS = {
        # Hitting props
        "batter_hits": "Hits",
        "batter_total_bases": "Total Bases",
        "batter_home_runs": "Home Runs",
        "batter_rbis": "RBIs",
        "batter_runs": "Runs",
        "batter_strikeouts": "Strikeouts",
        "batter_walks": "Walks",
        "batter_stolen_bases": "Stolen Bases",
        "batter_hits_runs_rbis": "Hits+Runs+RBIs",
        "batter_singles": "Singles",
        "batter_doubles": "Doubles",
        "batter_triples": "Triples",
        
        # Pitching props
        "pitcher_strikeouts": "Pitcher Strikeouts",
        "pitcher_earned_runs": "Earned Runs",
        "pitcher_hits_allowed": "Hits Allowed",
        "pitcher_walks_allowed": "Walks Allowed",
        "pitcher_outs_recorded": "Outs Recorded",
        "pitcher_win": "Pitcher Win",
        
        # Game props
        "player_first_inning_hit": "1st Inning Hit",
        "player_to_record_hit": "To Record a Hit",
        "player_to_hit_hr": "To Hit HR",
        "player_alt_total_hits": "Alt Hit Total",
        "player_alt_total_strikeouts": "Alt Strikeout Total"
    }

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
            return dt.astimezone(pytz.timezone('US/Eastern'))
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
                    if market["key"] in Config.BASEBALL_PROPS:
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
# MAIN APPLICATION
# ======================
class OddsApp:
    def __init__(self):
        self._setup_page()
        self._load_api_key()
        self._init_session()

    def _setup_page(self):
        st.set_page_config(
            layout="wide",
            page_title="Odds Tracker Pro",
            page_icon="📊",
            initial_sidebar_state="expanded"
        )
        st.title("⚾ Complete Sports Odds Tracker")

    def _load_api_key(self):
        """Handle API key discovery and validation"""
        st.sidebar.header("API Key Setup")
        
        # Try to find key automatically
        self.api_key = APIKeyManager.find_api_key()
        validation = APIKeyManager.validate_key(self.api_key)

        # Show debug info
        with st.sidebar.expander("Key Diagnostics", expanded=not validation["valid"]):
            if validation["error"]:
                st.error(f"❌ {validation['error']}")
            st.json(validation["details"])

            if not validation["valid"]:
                st.markdown("""
                ### How to provide your API key:
                
                1. **For Production (Recommended):**  
                   Create `.streamlit/secrets.toml` with:  
                   ```toml
                   ODDS_API_KEY = "your_actual_key_here"
                   ```
                
                2. **For Local Development:**  
                   Either:  
                   ```bash
                   export ODDS_API_KEY="your_key_here"
                   ```
                   Or create `.odds_api_key` file:  
                   ```bash
                   echo "your_key_here" > .odds_api_key
                   ```
                """)
                st.stop()

        st.sidebar.success(f"✅ Valid key from {validation['details']['source']}")
        st.session_state.remaining_requests = validation["details"].get("remaining")

    def _init_session(self):
        if "games" not in st.session_state:
            st.session_state.games = {}
        if "selected_sport" not in st.session_state:
            st.session_state.selected_sport = "MLB"
        if "selected_props" not in st.session_state:
            st.session_state.selected_props = list(Config.BASEBALL_PROPS.keys())[:5]

    def _render_controls(self):
        st.sidebar.header("Controls")
        
        st.sidebar.selectbox(
            "Select Sport",
            list(Config.SPORTS.keys()),
            key="selected_sport"
        )
        
        st.sidebar.multiselect(
            "Sportsbooks",
            Config.SPORTSBOOKS,
            default=Config.SPORTSBOOKS,
            key="selected_books"
        )
        
        st.sidebar.multiselect(
            "Player Props to Show",
            list(Config.BASEBALL_PROPS.values()),
            default=[Config.BASEBALL_PROPS[p] for p in st.session_state.selected_props],
            key="selected_props_display"
        )

        if st.sidebar.button("🔄 Refresh Data"):
            self._fetch_games()

    def _fetch_games(self):
        try:
            sport_key = Config.SPORTS[st.session_state.selected_sport]
            response = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
                params={
                    "apiKey": self.api_key,
                    "regions": "us",
                    "markets": ",".join(["h2h", "spreads", "totals"] + st.session_state.selected_props),
                    "oddsFormat": "american"
                },
                timeout=10
            )
            response.raise_for_status()
            st.session_state.games = [Game(game) for game in response.json()]
        except Exception as e:
            st.error(f"Failed to fetch games: {str(e)}")

    def _render_game(self, game: Game):
        with st.expander(f"{game.away} @ {game.home} | {game.start_time:%m/%d %I:%M %p ET}"):
            # Main odds table
            st.subheader("Game Lines")
            odds_rows = []
            for book in st.session_state.selected_books:
                if book in game.odds:
                    odds = game.odds[book]
                    row = {
                        "Sportsbook": book,
                        "Away ML": next((o["price"] for o in odds["moneyline"]["outcomes"] if o["name"] == game.away), "N/A"),
                        "Home ML": next((o["price"] for o in odds["moneyline"]["outcomes"] if o["name"] == game.home), "N/A"),
                        "Spread": f"{next((o['point'] for o in odds['spread']['outcomes'] if o['name'] == game.away), 'N/A')} ({next((o['price'] for o in odds['spread']['outcomes'] if o['name'] == game.away), 'N/A')})",
                        "Total": f"O {next((o['point'] for o in odds['total']['outcomes'] if o['name'] == 'Over'), 'N/A')} ({next((o['price'] for o in odds['total']['outcomes'] if o['name'] == 'Over'), 'N/A')})"
                    }
                    odds_rows.append(row)
            st.dataframe(pd.DataFrame(odds_rows))

            # Player props
            if game.props:
                st.subheader("Player Props")
                prop_display_map = {v: k for k, v in Config.BASEBALL_PROPS.items()}
                selected_prop_keys = [prop_display_map[p] for p in st.session_state.selected_props_display if p in prop_display_map]
                
                for prop_key in selected_prop_keys:
                    prop_name = Config.BASEBALL_PROPS[prop_key]
                    prop_data = [p for p in game.props if p.market == prop_key]
                    
                    if prop_data:
                        st.markdown(f"**{prop_name}**")
                        df = pd.DataFrame([{
                            "Player": p.player,
                            "Line": p.line,
                            "Odds": p.odds,
                            "Book": p.book
                        } for p in prop_data])
                        st.dataframe(df.style.format({"Odds": "{:+d}"}))

    def run(self):
        self._render_controls()
        self._fetch_games()
        
        if not st.session_state.get("games"):
            st.warning("No games found for selected sport")
            return
            
        for game in st.session_state.games:
            self._render_game(game)

if __name__ == "__main__":
    app = OddsApp()
    app.run()
