import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

# ======================
# CONFIGURATION
# ======================
class Config:
    # API Settings
    API_URL = "https://api.the-odds-api.com/v4"
    API_KEY = st.secrets.get("ODDS_API_KEY", "demo")  # Use GitHub Secrets in production

    # App Settings
    MAX_GAMES = 50
    TIMEZONE = pytz.timezone('US/Eastern')

    # Sports Configuration
    SPORTS = {
        "MLB": "baseball_mlb",
        "NBA": "basketball_nba",
        "NFL": "americanfootball_nfl",
        "NHL": "icehockey_nhl",
        "Tennis": "tennis_atp"
    }

    SPORTSBOOKS = ["FanDuel", "DraftKings", "BetMGM", "Caesars", "PointsBet"]
    MARKETS = ["h2h", "totals", "spreads"]

# ======================
# DATA MODELS
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
                    'spreads': next((m for m in book['markets'] if m['key'] == 'spreads'), None)
                }
        return odds_data

# ======================
# API SERVICE
# ======================
class OddsAPI:
    @staticmethod
    def verify_key():
        """Verify API key validity"""
        try:
            url = f"{Config.API_URL}/sports"
            response = requests.get(url, params={'apiKey': Config.API_KEY})

            if response.status_code == 200:
                remaining = response.headers.get('x-requests-remaining', 'Unknown')
                st.success(f"✅ API Key Valid (Remaining requests: {remaining})")
                return True
            elif response.status_code == 401:
                st.error("❌ Invalid API Key - Check your GitHub Secrets")
                return False
            else:
                st.warning(f"⚠️ API Response: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            st.error(f"🚨 Connection Error: {str(e)}")
            return False

    @staticmethod
    def fetch_games(sport_key):
        """Fetch live odds for a specific sport"""
        try:
            url = f"{Config.API_URL}/sports/{sport_key}/odds"
            params = {
                'apiKey': Config.API_KEY,
                'regions': 'us',
                'markets': ','.join(Config.MARKETS),
                'oddsFormat': 'american',
                'dateFormat': 'iso'
            }

            response = requests.get(url, params=params)

            if response.ok:
                games = response.json()
                if not games:
                    st.warning(f"No current games for {sport_key}")
                return [Game(game) for game in games[:Config.MAX_GAMES]]

            st.error(f"API Error: {response.status_code} - {response.text}")
            return []

        except Exception as e:
            st.error(f"API Connection Failed: {str(e)}")
            return []

# ======================
# CORE APP FUNCTIONALITY
# ======================
class OddsApp:
    def __init__(self):
        self._setup_ui()
        self._init_session()
        self._verify_api()

    def _setup_ui(self):
        """Configure Streamlit UI settings"""
        st.set_page_config(
            layout="wide",
            page_title="Odds Tracker Pro",
            page_icon="📊",
            initial_sidebar_state="expanded"
        )

        self._apply_custom_styles()

    def _apply_custom_styles(self):
        """Add custom CSS styling"""
        st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(rgba(10,10,30,0.95), rgba(5,5,20,0.95)), 
                        url('https://images.unsplash.com/photo-1631635589499-afd87d52b244');
            background-size: cover;
            background-attachment: fixed;
        }
        .game-card {
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background: rgba(0,15,30,0.85);
            border-left: 4px solid #00ffe7;
        }
        .odds-table {
            width: 100%;
            border-collapse: collapse;
        }
        .odds-table th {
            background: rgba(0,50,100,0.7);
            padding: 8px;
            text-align: center;
        }
        .odds-table td {
            padding: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        </style>
        """, unsafe_allow_html=True)

    def _init_session(self):
        """Initialize session state variables"""
        if 'games' not in st.session_state:
            st.session_state.games = {sport: [] for sport in Config.SPORTS.keys()}
        if 'selected_sports' not in st.session_state:
            st.session_state.selected_sports = ["NBA", "NFL"]
        if 'markets_select' not in st.session_state:
            st.session_state.markets_select = Config.MARKETS
        if 'omniscience_chat' not in st.session_state:
            st.session_state.omniscience_chat = []

    def _verify_api(self):
        """Verify API key and show status"""
        if Config.API_KEY == "demo":
            st.warning("⚠️ Using DEMO MODE - Limited data only")
        elif 'api_verified' not in st.session_state:
            if OddsAPI.verify_key():
                st.session_state.api_verified = True

    def _render_sidebar(self):
        """Render the control sidebar"""
        with st.sidebar:
            st.title("⚙️ Controls")
            st.markdown("---")

            # League selection
            selected_sports = st.multiselect(
                "SELECT LEAGUES",
                list(Config.SPORTS.keys()),
                default=st.session_state.selected_sports,
                key="league_select"
            )
            st.session_state.selected_sports = selected_sports

            # Display options
            st.markdown("### 📊 Display Options")
            show_markets = st.multiselect(
                "MARKETS TO SHOW",
                Config.MARKETS,
                default=Config.MARKETS,
                key="markets_select"
            )
            st.session_state.markets_select = show_markets

            # Refresh info
            if 'last_refresh' in st.session_state:
                st.markdown(f"🔄 Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
            if st.button("🔄 Manual Refresh"):
                self._force_refresh()

            # API status
            st.markdown("---")
            st.markdown("### 🔌 API Status")
            if Config.API_KEY == "demo":
                st.error("DEMO MODE ACTIVE")
            else:
                st.success("LIVE DATA CONNECTED")

    def _force_refresh(self):
        """Force immediate data refresh for selected sports"""
        st.session_state.last_refresh = datetime.now()
        for sport in st.session_state.selected_sports:
            sport_key = Config.SPORTS[sport]
            st.session_state.games[sport] = OddsAPI.fetch_games(sport_key)
        st.rerun()

    def _render_game_card(self, game, show_markets):
        """Render an individual game card"""
        with st.container():
            st.markdown(f"""
            <div class="game-card">
                <h3>{game.away} @ {game.home}</h3>
                <p>⏰ {game.start_time.strftime('%a %m/%d %I:%M %p ET')}</p>
            """, unsafe_allow_html=True)

            # Create odds tables for each sportsbook
            for book in Config.SPORTSBOOKS:
                if book in game.odds:
                    self._render_odds_table(book, game.odds[book], show_markets, game)

            st.markdown("</div>", unsafe_allow_html=True)

    def _render_odds_table(self, book_name, odds_data, show_markets, game):
        """Render odds table for a specific sportsbook"""
        st.markdown(f"**{book_name}**")

        # Prepare table data
        headers = ["Market"] + [game.away, game.home] if 'h2h' in show_markets else ["Market", "Line", "Odds"]
        rows = []

        if 'h2h' in show_markets and odds_data['moneyline']:
            ml = odds_data['moneyline']
            rows.append(["Moneyline",
                         f"{next((o['price'] for o in ml['outcomes'] if o['name'] == game.away), 'N/A')}",
                         f"{next((o['price'] for o in ml['outcomes'] if o['name'] == game.home), 'N/A')}"])

        if 'totals' in show_markets and odds_data['totals']:
            total = odds_data['totals']
            over = next((o for o in total['outcomes'] if o['name'] == 'Over'), None)
            under = next((o for o in total['outcomes'] if o['name'] == 'Under'), None)
            if over and under:
                rows.append(["Over", over['point'], over['price']])
                rows.append(["Under", under['point'], under['price']])

        if 'spreads' in show_markets and odds_data['spreads']:
            spread = odds_data['spreads']
            away_spread = next((o for o in spread['outcomes'] if o['name'] == game.away), None)
            home_spread = next((o for o in spread['outcomes'] if o['name'] == game.home), None)
            if away_spread and home_spread:
                rows.append(["Spread",
                            f"{away_spread['point']} ({away_spread['price']})",
                            f"{home_spread['point']} ({home_spread['price']})"])

        # Display the table
        if rows:
            st.table(pd.DataFrame(rows, columns=headers))
        else:
            st.warning("No odds data available for selected markets")

    def _render_omniscience_chat(self):
        """Chat interface to ask Omniscience model for insights/explanations."""
        st.markdown("---")
        st.subheader("🤖 Omniscience Model Chat")
        with st.form("omniscience_chat_form", clear_on_submit=True):
            user_query = st.text_input("Ask Omniscience about a flagged player, team, or any model insight:")
            submitted = st.form_submit_button("Ask")
            if submitted and user_query:
                # Replace this with your actual model call
                model_response = self._ask_omniscience(user_query)
                st.session_state.omniscience_chat.append(("You", user_query))
                st.session_state.omniscience_chat.append(("Omniscience", model_response))
        for sender, message in st.session_state.omniscience_chat:
            st.markdown(f"**{sender}:** {message}")

    def _ask_omniscience(self, query):
        """
        Replace this stub with your actual Omniscience model logic or API call.
        For now, it returns a placeholder response.
        """
        # Example: return omniscience_api.ask(query)
        # You can also use OpenAI, Gemini, or your own backend here.
        return f"Omniscience explanation for: '{query}' (replace this with real model output)"

    def run(self):
        """Main app execution"""
        self._render_sidebar()

        st.title("📊 Live Odds Dashboard")
        st.markdown("---")

        selected_sports = st.session_state.get("selected_sports", ["NBA", "NFL"])
        show_markets = st.session_state.get("markets_select", Config.MARKETS)

        for sport in selected_sports:
            st.header(f"🏟️ {sport} Games")

            if not st.session_state.games.get(sport, []):
                st.warning(f"No current games found for {sport}")
                continue

            for game in st.session_state.games[sport]:
                self._render_game_card(game, show_markets)

        # Omniscience chat at the bottom
        self._render_omniscience_chat()

# ======================
# APP EXECUTION
# ======================
if __name__ == "__main__":
    app = OddsApp()
    app.run()
