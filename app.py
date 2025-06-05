import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd
import copy

# ======================
# CONFIGURATION
# ======================
class Config:
    API_URL = "https://api.the-odds-api.com/v4"
    API_KEY = st.secrets.get("ODDS_API_KEY", "demo")
    MAX_GAMES = 50
    TIMEZONE = pytz.timezone('US/Eastern')
    SPORTS = {
        "MLB": "baseball_mlb",
        "NBA": "basketball_nba",
        "NFL": "americanfootball_nfl",
        "NHL": "icehockey_nhl"
    }
    SPORTSBOOKS = ["FanDuel", "DraftKings", "BetMGM", "Caesars", "PointsBet"]
    MAIN_MARKETS = ["h2h", "spreads", "totals"]
    MLB_PLAYER_MARKETS = ["player_home_runs"]
    NBA_PLAYER_MARKETS = ["player_rebounds", "player_points"]

# ======================
# DATA MODELS
# ======================
class Game:
    def __init__(self, data, sport_name):
        self.id = data['id']
        self.sport_key = data['sport_key']
        self.home = data['home_team']
        self.away = data['away_team']
        self.start_time = self._parse_time(data['commence_time'])
        self.bookmakers = data.get('bookmakers', [])
        self.sport_name = sport_name
        self.odds = self._parse_standard_odds()
        self.player_props = []  # Will be filled later by per-event call

    def _parse_time(self, time_str):
        dt = datetime.fromisoformat(time_str[:-1]).astimezone(pytz.utc)
        return dt.astimezone(Config.TIMEZONE)

    def _parse_standard_odds(self):
        odds_data = {}
        for book in self.bookmakers:
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
    def fetch_games(sport_key, sport_name):
        url = f"{Config.API_URL}/sports/{sport_key}/odds"
        params = {
            'apiKey': Config.API_KEY,
            'regions': 'us',
            'markets': ','.join(Config.MAIN_MARKETS),
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }
        response = requests.get(url, params=params)
        if response.ok:
            games = response.json()
            return [Game(game, sport_name) for game in games[:Config.MAX_GAMES]]
        st.error(f"API Error: {response.status_code} - {response.text}")
        return []

    @staticmethod
    def fetch_player_props(event_id, player_markets):
        url = f"{Config.API_URL}/events/{event_id}/odds"
        params = {
            'apiKey': Config.API_KEY,
            'regions': 'us',
            'markets': ','.join(player_markets),
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }
        response = requests.get(url, params=params)
        if response.ok:
            return response.json()
        else:
            return {}

# ======================
# LINE MOVEMENT & SHARP INDICATORS
# ======================
def update_odds_history(games):
    now = datetime.now().isoformat()
    if 'odds_history' not in st.session_state:
        st.session_state.odds_history = {}
    for game in games:
        game_id = game.id
        odds_snapshot = copy.deepcopy(game.odds)
        if game_id not in st.session_state.odds_history:
            st.session_state.odds_history[game_id] = []
        st.session_state.odds_history[game_id].append({'timestamp': now, 'odds': odds_snapshot})

def get_line_movement(game_id):
    history = st.session_state.odds_history.get(game_id, [])
    if len(history) < 2:
        return "No movement"
    last = history[-1]['odds']
    prev = history[-2]['odds']
    movement = []
    for book in last:
        for market in last[book]:
            last_market = last[book][market]
            prev_market = prev[book][market]
            if last_market and prev_market and last_market != prev_market:
                movement.append(f"{book} {market}: {format_market(prev_market)} → {format_market(last_market)}")
    return "; ".join(movement) if movement else "No movement"

def format_market(market):
    if not market:
        return "N/A"
    if 'outcomes' in market:
        return ", ".join([f"{o['name']} {o.get('point','')}: {o['price']}" for o in market['outcomes']])
    return str(market)

def get_sharp_indicator(game_id):
    history = st.session_state.odds_history.get(game_id, [])
    if len(history) < 2:
        return "No sharp moves detected"
    last = history[-1]['odds']
    prev = history[-2]['odds']
    sharp_moves = []
    for book in last:
        last_spread = last[book]['spreads']
        prev_spread = prev[book]['spreads']
        if last_spread and prev_spread:
            try:
                for team in ['Away', 'Home']:
                    last_team = next((o for o in last_spread['outcomes'] if o['name'] == team), None)
                    prev_team = next((o for o in prev_spread['outcomes'] if o['name'] == team), None)
                    if last_team and prev_team:
                        if abs(float(last_team['point']) - float(prev_team['point'])) >= 1.5:
                            sharp_moves.append(f"{book} sharp {team} spread: {prev_team['point']} → {last_team['point']}")
            except Exception:
                continue
    if len(last) > 1:
        lines = []
        for book in last:
            spread = last[book]['spreads']
            if spread and 'outcomes' in spread:
                for o in spread['outcomes']:
                    lines.append(float(o['point']))
        if lines and (max(lines) - min(lines)) >= 1.5:
            sharp_moves.append("Book disagreement: spread difference > 1.5")
    return "; ".join(sharp_moves) if sharp_moves else "No sharp moves detected"

# ======================
# CORE APP FUNCTIONALITY
# ======================
class OddsApp:
    def __init__(self):
        self._setup_ui()
        self._init_session()

    def _setup_ui(self):
        st.set_page_config(
            layout="wide",
            page_title="Odds Tracker Pro",
            page_icon="📊",
            initial_sidebar_state="expanded"
        )
        self._apply_custom_styles()

    def _apply_custom_styles(self):
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
        if 'games' not in st.session_state:
            st.session_state.games = {sport: [] for sport in Config.SPORTS.keys()}
        if 'omniscience_chat' not in st.session_state:
            st.session_state.omniscience_chat = []

    def _render_sidebar(self):
        with st.sidebar:
            st.title("⚙️ Controls")
            st.markdown("---")
            st.multiselect(
                "SELECT LEAGUES",
                list(Config.SPORTS.keys()),
                default=st.session_state.get("league_select", ["NBA", "MLB"]),
                key="league_select"
            )
            if 'last_refresh' in st.session_state:
                st.markdown(f"🔄 Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
            if st.button("🔄 Manual Refresh"):
                self._force_refresh()
            st.markdown("---")
            st.markdown("### 🔌 API Status")
            if Config.API_KEY == "demo":
                st.error("DEMO MODE ACTIVE")
            else:
                st.success("LIVE DATA CONNECTED")

    def _force_refresh(self):
        st.session_state.last_refresh = datetime.now()
        selected_sports = st.session_state.get("league_select", ["NBA", "MLB"])
        for sport in selected_sports:
            sport_key = Config.SPORTS[sport]
            games = OddsAPI.fetch_games(sport_key, sport)
            update_odds_history(games)
            # Player props per event
            player_markets = []
            if sport == "NBA":
                player_markets = Config.NBA_PLAYER_MARKETS
            elif sport == "MLB":
                player_markets = Config.MLB_PLAYER_MARKETS
            for game in games:
                if player_markets:
                    player_props_data = OddsAPI.fetch_player_props(game.id, player_markets)
                    game.player_props = self._parse_player_props_from_event(player_props_data, player_markets)
            st.session_state.games[sport] = games
        st.rerun()

    def _parse_player_props_from_event(self, event_data, player_markets):
        props = []
        if not event_data or 'bookmakers' not in event_data:
            return props
        for book in event_data['bookmakers']:
            if book['key'] not in Config.SPORTSBOOKS:
                continue
            for market in book['markets']:
                if market['key'] in player_markets:
                    for outcome in market['outcomes']:
                        props.append({
                            "book": book['key'],
                            "market": market['key'],
                            "player": outcome.get('description', 'N/A'),
                            "line": outcome.get('point', 'N/A'),
                            "odds": outcome['price']
                        })
        return props

    def _render_game_card(self, game):
        with st.container():
            st.markdown(f"""
            <div class="game-card">
                <h3>{game.away} @ {game.home}</h3>
                <p>⏰ {game.start_time.strftime('%a %m/%d %I:%M %p ET')}</p>
            """, unsafe_allow_html=True)
            # Show line movement
            line_movement = get_line_movement(game.id)
            if line_movement != "No movement":
                st.markdown(f"**Line Movement:** {line_movement}")
            # Sharp indicator
            sharp_indicator = get_sharp_indicator(game.id)
            if sharp_indicator != "No sharp moves detected":
                st.markdown(f"**Sharp Indicator:** {sharp_indicator}")
            for book in Config.SPORTSBOOKS:
                if book in game.odds:
                    self._render_odds_table(book, game.odds[book], game)
            if game.player_props:
                st.markdown("**Player Props:**")
                for prop in game.player_props:
                    st.markdown(f"- {prop['player']} ({prop['market']}): {prop['line']} @ {prop['odds']} [{prop['book']}]")
            st.markdown("</div>", unsafe_allow_html=True)

    def _render_odds_table(self, book_name, odds_data, game):
        st.markdown(f"**{book_name}**")
        headers = ["Market"] + [game.away, game.home]
        rows = []
        if odds_data['moneyline']:
            ml = odds_data['moneyline']
            rows.append(["Moneyline",
                         f"{next((o['price'] for o in ml['outcomes'] if o['name'] == game.away), 'N/A')}",
                         f"{next((o['price'] for o in ml['outcomes'] if o['name'] == game.home), 'N/A')}"])
        if odds_data['totals']:
            total = odds_data['totals']
            over = next((o for o in total['outcomes'] if o['name'] == 'Over'), None)
            under = next((o for o in total['outcomes'] if o['name'] == 'Under'), None)
            if over and under:
                rows.append(["Over", over['point'], over['price']])
                rows.append(["Under", under['point'], under['price']])
        if odds_data['spreads']:
            spread = odds_data['spreads']
            away_spread = next((o for o in spread['outcomes'] if o['name'] == game.away), None)
            home_spread = next((o for o in spread['outcomes'] if o['name'] == game.home), None)
            if away_spread and home_spread:
                rows.append(["Spread",
                            f"{away_spread['point']} ({away_spread['price']})",
                            f"{home_spread['point']} ({home_spread['price']})"])
        if rows:
            st.table(pd.DataFrame(rows, columns=headers))
        else:
            st.warning("No odds data available for selected markets")

    def run(self):
        self._render_sidebar()
        st.title("📊 Live Odds Dashboard")
        st.markdown("---")
        selected_sports = st.session_state.get("league_select", ["NBA", "MLB"])
        for sport in selected_sports:
            st.header(f"🏟️ {sport} Games")
            if not st.session_state.games.get(sport, []):
                st.warning(f"No current games found for {sport}")
                continue
            for game in st.session_state.games[sport]:
                self._render_game_card(game)

if __name__ == "__main__":
    app = OddsApp()
    app.run()
