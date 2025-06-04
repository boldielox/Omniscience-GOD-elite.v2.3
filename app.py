import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd
import traceback
from typing import List, Dict, Optional, Union

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
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 10  # seconds

    # Comprehensive Sports Configuration - Pro and College
    SPORTS = {
        # Professional Sports
        "NFL": "americanfootball_nfl",
        "NBA": "basketball_nba",
        "MLB": "baseball_mlb",
        "NHL": "icehockey_nhl",
        "WNBA": "basketball_wnba",
        "MLS": "soccer_usa_mls",
        "CFL": "americanfootball_cfl",
        
        # College Sports
        "NCAA Football": "americanfootball_ncaaf",
        "NCAA Basketball": "basketball_ncaab",
        "NCAA Baseball": "baseball_ncaa",
        
        # Other Sports with Player Props
        "Tennis (ATP)": "tennis_atp",
        "Tennis (WTA)": "tennis_wta",
        "Golf (PGA)": "golf_pga",
        "UFC": "mma_ufc",
        
        # International Sports
        "Premier League": "soccer_epl",
        "La Liga": "soccer_spain_la_liga",
        "NBA G League": "basketball_nba_g_league"
    }

    SPORTSBOOKS = ["FanDuel", "DraftKings", "BetMGM", "Caesars", "PointsBet", "BetRivers", "Barstool"]
    
    # Expanded Markets including Player Props
    MARKETS = ["h2h", "totals", "spreads", "player_points", "player_assists", 
               "player_rebounds", "player_pass_tds", "player_pass_yds", 
               "player_rush_yds", "player_receptions", "player_hits", 
               "player_strikeouts", "player_goals", "player_shots"]
    
    # Mapping of player props to display names
    PROP_DISPLAY_NAMES = {
        "player_points": "Points",
        "player_assists": "Assists",
        "player_rebounds": "Rebounds",
        "player_pass_tds": "Passing TDs",
        "player_pass_yds": "Passing Yards",
        "player_rush_yds": "Rushing Yards",
        "player_receptions": "Receptions",
        "player_hits": "Hits",
        "player_strikeouts": "Strikeouts",
        "player_goals": "Goals",
        "player_shots": "Shots on Goal"
    }

# ======================
# DATA MODELS
# ======================
class Game:
    def __init__(self, data: dict):
        try:
            self.id = data.get('id', '')
            self.sport_key = data.get('sport_key', '')
            self.home = data.get('home_team', 'Unknown')
            self.away = data.get('away_team', 'Unknown')
            self.start_time = self._parse_time(data.get('commence_time', ''))
            self.odds = self._parse_odds(data.get('bookmakers', []))
            self.players = self._parse_player_props(data.get('bookmakers', []))
        except Exception as e:
            st.error(f"Error initializing Game: {str(e)}")
            raise

    def _parse_time(self, time_str: str) -> datetime:
        try:
            if not time_str:
                return datetime.now(Config.TIMEZONE)
            
            dt = datetime.fromisoformat(time_str[:-1]).astimezone(pytz.utc)
            return dt.astimezone(Config.TIMEZONE)
        except Exception as e:
            st.warning(f"Failed to parse time {time_str}: {str(e)}")
            return datetime.now(Config.TIMEZONE)

    def _parse_odds(self, bookmakers: List[dict]) -> Dict[str, dict]:
        odds_data = {}
        try:
            for book in bookmakers:
                book_key = book.get('key', '')
                if book_key in Config.SPORTSBOOKS:
                    odds_data[book_key] = {
                        'moneyline': next((m for m in book.get('markets', []) if m.get('key') == 'h2h'), None),
                        'totals': next((m for m in book.get('markets', []) if m.get('key') == 'totals'), None),
                        'spreads': next((m for m in book.get('markets', []) if m.get('key') == 'spreads'), None)
                    }
        except Exception as e:
            st.error(f"Error parsing odds: {str(e)}")
        return odds_data
    
    def _parse_player_props(self, bookmakers: List[dict]) -> Dict[str, dict]:
        player_props = {}
        try:
            for book in bookmakers:
                book_key = book.get('key', '')
                if book_key in Config.SPORTSBOOKS:
                    for market in book.get('markets', []):
                        if market.get('key') in Config.MARKETS and market.get('key').startswith('player_'):
                            prop_key = market.get('key')
                            if prop_key not in player_props:
                                player_props[prop_key] = {}
                            
                            for outcome in market.get('outcomes', []):
                                player_name = outcome.get('name', 'Unknown')
                                if player_name not in player_props[prop_key]:
                                    player_props[prop_key][player_name] = []
                                
                                player_props[prop_key][player_name].append({
                                    'book': book_key,
                                    'point': outcome.get('point'),
                                    'price': outcome.get('price')
                                })
        except Exception as e:
            st.error(f"Error parsing player props: {str(e)}")
        return player_props

# ======================
# API SERVICE
# ======================
class OddsAPI:
    @staticmethod
    def verify_key() -> bool:
        """Verify API key validity with retries and error handling"""
        for attempt in range(Config.MAX_RETRIES):
            try:
                url = f"{Config.API_URL}/sports"
                response = requests.get(
                    url,
                    params={'apiKey': Config.API_KEY},
                    timeout=Config.REQUEST_TIMEOUT
                )

                if response.status_code == 200:
                    remaining = response.headers.get('x-requests-remaining', 'Unknown')
                    st.success(f"✅ API Key Valid (Remaining requests: {remaining})")
                    return True
                elif response.status_code == 401:
                    st.error("❌ Invalid API Key - Check your GitHub Secrets")
                    return False
                else:
                    st.warning(f"⚠️ API Response: {response.status_code} - {response.text}")
                    if attempt < Config.MAX_RETRIES - 1:
                        continue
                    return False

            except requests.exceptions.RequestException as e:
                st.error(f"🚨 Connection Error (Attempt {attempt + 1}): {str(e)}")
                if attempt == Config.MAX_RETRIES - 1:
                    return False
                continue

        return False

    @staticmethod
    def fetch_games(sport_key: str) -> List[Game]:
        """Fetch live odds for a specific sport with retries and error handling"""
        games = []
        for attempt in range(Config.MAX_RETRIES):
            try:
                url = f"{Config.API_URL}/sports/{sport_key}/odds"
                params = {
                    'apiKey': Config.API_KEY,
                    'regions': 'us',
                    'markets': ','.join(Config.MARKETS),
                    'oddsFormat': 'american',
                    'dateFormat': 'iso'
                }

                response = requests.get(
                    url,
                    params=params,
                    timeout=Config.REQUEST_TIMEOUT
                )

                if response.ok:
                    games_data = response.json()
                    if not games_data:
                        st.warning(f"No current games for {sport_key}")
                        return []
                    
                    games = [Game(game) for game in games_data[:Config.MAX_GAMES]]
                    return games

                st.error(f"API Error (Attempt {attempt + 1}): {response.status_code} - {response.text}")
                if attempt < Config.MAX_RETRIES - 1:
                    continue
                return []

            except requests.exceptions.RequestException as e:
                st.error(f"API Connection Failed (Attempt {attempt + 1}): {str(e)}")
                if attempt == Config.MAX_RETRIES - 1:
                    return []
                continue
            except Exception as e:
                st.error(f"Unexpected error fetching games: {str(e)}")
                return []

        return games

# ======================
# CORE APP FUNCTIONALITY
# ======================
class OddsApp:
    def __init__(self):
        try:
            self._setup_ui()
            self._init_session()
            self._verify_api()
        except Exception as e:
            st.error(f"Failed to initialize app: {str(e)}")
            st.stop()

    def _setup_ui(self):
        """Configure Streamlit UI settings with error handling"""
        try:
            st.set_page_config(
                layout="wide",
                page_title="Odds Tracker Pro",
                page_icon="📊",
                initial_sidebar_state="expanded"
            )
            self._apply_custom_styles()
        except Exception as e:
            st.error(f"UI setup failed: {str(e)}")

    def _apply_custom_styles(self):
        """Add custom CSS styling with error handling"""
        try:
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
            .prop-card {
                border-radius: 8px;
                padding: 10px;
                margin: 8px 0;
                background: rgba(20,30,50,0.8);
                border-left: 3px solid #ff6b6b;
            }
            .error-message {
                color: #ff4b4b;
                background: rgba(255, 75, 75, 0.1);
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
            .player-prop-header {
                color: #00ffe7;
                font-weight: bold;
                margin-top: 15px;
                border-bottom: 1px solid #00ffe7;
                padding-bottom: 5px;
            }
            </style>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Failed to apply custom styles: {str(e)}")

    def _init_session(self):
        """Initialize session state variables with error handling"""
        try:
            if 'games' not in st.session_state:
                st.session_state.games = {sport: [] for sport in Config.SPORTS.keys()}
            if 'omniscience_chat' not in st.session_state:
                st.session_state.omniscience_chat = []
            if 'last_refresh' not in st.session_state:
                st.session_state.last_refresh = None
            if 'api_verified' not in st.session_state:
                st.session_state.api_verified = False
            if 'selected_props' not in st.session_state:
                st.session_state.selected_props = []
        except Exception as e:
            st.error(f"Session initialization failed: {str(e)}")

    def _verify_api(self):
        """Verify API key and show status with error handling"""
        try:
            if Config.API_KEY == "demo":
                st.warning("⚠️ Using DEMO MODE - Limited data only")
            elif not st.session_state.api_verified:
                st.session_state.api_verified = OddsAPI.verify_key()
        except Exception as e:
            st.error(f"API verification failed: {str(e)}")

    def _render_sidebar(self):
        """Render the control sidebar with error handling"""
        try:
            with st.sidebar:
                st.title("⚙️ Controls")
                st.markdown("---")

                # League selection with categories
                st.markdown("### 🏈 Professional Sports")
                pro_sports = ["NFL", "NBA", "MLB", "NHL", "WNBA", "MLS", "CFL"]
                pro_selected = st.multiselect(
                    "Select Pro Leagues",
                    pro_sports,
                    default=st.session_state.get("pro_select", ["NFL", "NBA"]),
                    key="pro_select"
                )

                st.markdown("### 🎓 College Sports")
                college_sports = ["NCAA Football", "NCAA Basketball", "NCAA Baseball"]
                college_selected = st.multiselect(
                    "Select College Leagues",
                    college_sports,
                    default=st.session_state.get("college_select", ["NCAA Football"]),
                    key="college_select"
                )

                st.markdown("### 🌎 Other Sports")
                other_sports = ["Tennis (ATP)", "Tennis (WTA)", "Golf (PGA)", "UFC", "Premier League", "La Liga", "NBA G League"]
                other_selected = st.multiselect(
                    "Select Other Leagues",
                    other_sports,
                    default=st.session_state.get("other_select", []),
                    key="other_select"
                )

                # Combine all selected sports
                selected_sports = pro_selected + college_selected + other_selected
                st.session_state.league_select = selected_sports

                # Markets to show
                st.markdown("### 📊 Display Options")
                st.multiselect(
                    "STANDARD MARKETS",
                    ["h2h", "totals", "spreads"],
                    default=st.session_state.get("standard_markets", ["h2h", "spreads"]),
                    key="standard_markets"
                )

                # Player props selection
                st.markdown("### 🏅 Player Props")
                st.multiselect(
                    "SELECT PLAYER PROPS",
                    list(Config.PROP_DISPLAY_NAMES.values()),
                    default=st.session_state.get("selected_props", []),
                    key="selected_props"
                )

                # Refresh info
                if st.session_state.last_refresh:
                    st.markdown(f"🔄 Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
                
                if st.button("🔄 Manual Refresh", help="Fetch the latest odds data"):
                    self._force_refresh()

                # API status
                st.markdown("---")
                st.markdown("### 🔌 API Status")
                if Config.API_KEY == "demo":
                    st.error("DEMO MODE ACTIVE")
                elif st.session_state.api_verified:
                    st.success("LIVE DATA CONNECTED")
                else:
                    st.error("API CONNECTION FAILED")
        except Exception as e:
            st.error(f"Sidebar rendering failed: {str(e)}")

    def _force_refresh(self):
        """Force immediate data refresh for selected sports with error handling"""
        try:
            st.session_state.last_refresh = datetime.now(Config.TIMEZONE)
            selected_sports = st.session_state.get("league_select", ["NFL", "NBA"])
            
            if not selected_sports:
                st.warning("Please select at least one league")
                return

            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, sport in enumerate(selected_sports):
                status_text.text(f"Fetching {sport} data...")
                progress_bar.progress((i + 1) / len(selected_sports))
                
                try:
                    sport_key = Config.SPORTS.get(sport)
                    if not sport_key:
                        st.warning(f"Invalid sport: {sport}")
                        continue
                    
                    games = OddsAPI.fetch_games(sport_key)
                    st.session_state.games[sport] = games
                except Exception as e:
                    st.error(f"Failed to fetch {sport} games: {str(e)}")
                    continue

            status_text.text("Refresh complete!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Refresh failed: {str(e)}")
            st.error(traceback.format_exc())

    def _render_game_card(self, game: Game):
        """Render an individual game card with error handling"""
        try:
            with st.container():
                st.markdown(f"""
                <div class="game-card">
                    <h3>{game.away} @ {game.home}</h3>
                    <p>⏰ {game.start_time.strftime('%a %m/%d %I:%M %p ET')}</p>
                """, unsafe_allow_html=True)

                # Render standard markets
                standard_markets = st.session_state.get("standard_markets", ["h2h", "spreads"])
                for book in Config.SPORTSBOOKS:
                    if book in game.odds:
                        self._render_odds_table(book, game.odds[book], standard_markets, game)

                # Render player props if selected
                selected_props = st.session_state.get("selected_props", [])
                if selected_props and game.players:
                    self._render_player_props(game)

                st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Failed to render game card: {str(e)}")

    def _render_odds_table(self, book_name: str, odds_data: dict, show_markets: List[str], game: Game):
        """Render odds table for a specific sportsbook with error handling"""
        try:
            st.markdown(f"**{book_name}**")
            
            # Prepare table data
            headers = ["Market"] + [game.away, game.home] if 'h2h' in show_markets else ["Market", "Line", "Odds"]
            rows = []

            # Moneyline data
            if 'h2h' in show_markets and odds_data.get('moneyline'):
                try:
                    ml = odds_data['moneyline']
                    away_ml = next((o['price'] for o in ml.get('outcomes', []) if o.get('name') == game.away), 'N/A')
                    home_ml = next((o['price'] for o in ml.get('outcomes', []) if o.get('name') == game.home), 'N/A')
                    rows.append(["Moneyline", str(away_ml), str(home_ml)])
                except Exception as e:
                    st.warning(f"Couldn't process moneyline odds: {str(e)}")

            # Totals data
            if 'totals' in show_markets and odds_data.get('totals'):
                try:
                    total = odds_data['totals']
                    over = next((o for o in total.get('outcomes', []) if o.get('name') == 'Over'), None)
                    under = next((o for o in total.get('outcomes', []) if o.get('name') == 'Under'), None)
                    if over and under:
                        rows.append(["Over", str(over.get('point', 'N/A')), str(over.get('price', 'N/A'))])
                        rows.append(["Under", str(under.get('point', 'N/A')), str(under.get('price', 'N/A'))])
                except Exception as e:
                    st.warning(f"Couldn't process totals odds: {str(e)}")

            # Spreads data
            if 'spreads' in show_markets and odds_data.get('spreads'):
                try:
                    spread = odds_data['spreads']
                    away_spread = next((o for o in spread.get('outcomes', []) if o.get('name') == game.away), None)
                    home_spread = next((o for o in spread.get('outcomes', []) if o.get('name') == game.home), None)
                    if away_spread and home_spread:
                        rows.append(["Spread",
                                   f"{away_spread.get('point', 'N/A')} ({away_spread.get('price', 'N/A')})",
                                   f"{home_spread.get('point', 'N/A')} ({home_spread.get('price', 'N/A')})"])
                except Exception as e:
                    st.warning(f"Couldn't process spread odds: {str(e)}")

            # Display the table if we have data
            if rows:
                st.table(pd.DataFrame(rows, columns=headers))
            else:
                st.warning("No odds data available for selected markets")
        except Exception as e:
            st.error(f"Failed to render odds table: {str(e)}")

    def _render_player_props(self, game: Game):
        """Render player props section with error handling"""
        try:
            selected_prop_display = st.session_state.get("selected_props", [])
            if not selected_prop_display:
                return
            
            # Convert display names back to API keys
            prop_display_to_key = {v: k for k, v in Config.PROP_DISPLAY_NAMES.items()}
            selected_props = [prop_display_to_key[display] for display in selected_prop_display 
                            if display in prop_display_to_key]
            
            st.markdown("### 🏅 Player Props")
            
            for prop_key in selected_props:
                if prop_key in game.players:
                    prop_name = Config.PROP_DISPLAY_NAMES.get(prop_key, prop_key)
                    st.markdown(f"<div class='player-prop-header'>{prop_name}</div>", unsafe_allow_html=True)
                    
                    # Collect all player data for this prop
                    all_players = []
                    for player_name, offers in game.players[prop_key].items():
                        for offer in offers:
                            all_players.append({
                                "Player": player_name,
                                "Book": offer['book'],
                                "Line": offer.get('point', 'N/A'),
                                "Odds": offer.get('price', 'N/A')
                            })
                    
                    if all_players:
                        # Create a pivot table to show books as columns
                        df = pd.DataFrame(all_players)
                        pivot_df = df.pivot_table(
                            index='Player',
                            columns='Book',
                            values=['Line', 'Odds'],
                            aggfunc='first'
                        )
                        
                        # Flatten multi-index columns
                        pivot_df.columns = [f"{col[1]} {col[0]}" for col in pivot_df.columns]
                        st.dataframe(pivot_df.style.format("{:.1f}"))
                    else:
                        st.warning(f"No {prop_name} props available for this game")
        except Exception as e:
            st.error(f"Failed to render player props: {str(e)}")

    def _render_omniscience_chat(self):
        """Chat interface with error handling"""
        try:
            st.markdown("---")
            st.subheader("🤖 Omniscience Model Chat")
            
            with st.form("omniscience_chat_form", clear_on_submit=True):
                user_query = st.text_input("Ask Omniscience about a flagged player, team, or any model insight:")
                submitted = st.form_submit_button("Ask")
                
                if submitted and user_query:
                    try:
                        model_response = self._ask_omniscience(user_query)
                        st.session_state.omniscience_chat.append(("You", user_query))
                        st.session_state.omniscience_chat.append(("Omniscience", model_response))
                    except Exception as e:
                        st.error(f"Failed to get model response: {str(e)}")

            for sender, message in st.session_state.omniscience_chat:
                st.markdown(f"**{sender}:** {message}")
        except Exception as e:
            st.error(f"Chat interface failed: {str(e)}")

    def _ask_omniscience(self, query: str) -> str:
        """Get response from Omniscience model with error handling"""
        try:
            # Replace this with your actual model integration
            # Example: return omniscience_api.ask(query)
            return f"Analysis for '{query}':\n\nThe model would provide insights here about betting trends, team performance, or player statistics."
        except Exception as e:
            st.error(f"Model query failed: {str(e)}")
            return "Sorry, I couldn't process that request. Please try again later."

    def run(self):
        """Main app execution with comprehensive error handling"""
        try:
            self._render_sidebar()

            st.title("📊 Live Odds Dashboard")
            st.markdown("---")

            selected_sports = st.session_state.get("league_select", ["NFL", "NBA"])
            
            if not selected_sports:
                st.warning("Please select at least one league in the sidebar")
                return

            for sport in selected_sports:
                try:
                    st.header(f"🏟️ {sport} Games")
                    games = st.session_state.games.get(sport, [])
                    
                    if not games:
                        st.warning(f"No current games found for {sport}")
                        continue

                    for game in games:
                        self._render_game_card(game)

                except Exception as e:
                    st.error(f"Failed to render {sport} section: {str(e)}")

            # Omniscience chat at the bottom
            self._render_omniscience_chat()

        except Exception as e:
            st.error(f"Fatal application error: {str(e)}")
            st.error(traceback.format_exc())

# ======================
# APP EXECUTION
# ======================
if __name__ == "__main__":
    try:
        app = OddsApp()
        app.run()
    except Exception as e:
        st.error(f"Application failed to start: {str(e)}")
        st.error(traceback.format_exc())
