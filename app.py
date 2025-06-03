import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
import threading
import time
import zipfile

# --- Config ---
LEAGUES = ["MLB", "NBA", "WNBA", "NHL", "NCAA Baseball"]
MAX_GAMES = 50
API_INTERVAL = 1800  # 30 minutes
SPORTSBOOKS = ["FanDuel", "DraftKings", "BetMGM", "Caesars"]

# --- API Keys (use secrets in production) ---
API_KEY = st.secrets.get("ODDS_API_KEY", "demo")

# --- Cosmic UI ---
st.set_page_config(layout="wide", page_title="Omniscience Elite v3.0", page_icon="👁️")
st.markdown("""
<style>
.stApp {background-image: url('https://pplx-res.cloudinary.com/image/upload/v1748978611/user_uploads/71937249/fb5461f1-3a0f-4d40-b7ae-b45da0418088/101.jpg');}
.main {background: rgba(10,10,20,0.92) !important;}
.stSidebar {background: rgba(5,5,15,0.97) !important;}
.st-b7 {background-color: rgba(0,20,40,0.85) !important;}
.stAlert {border-left: 4px solid #00ffe7 !important;}
</style>
""", unsafe_allow_html=True)

# --- Data Models ---
class Game:
    def __init__(self, data):
        self.id = data['id']
        self.league = data['sport_key']
        self.home = data['home_team']
        self.away = data['away_team']
        self.start_time = datetime.fromisoformat(data['commence_time'][:-1]).astimezone(pytz.utc)
        self.odds = self._parse_odds(data['bookmakers'])

    def _parse_odds(self, bookmakers):
        return {
            book['key']: {
                'moneyline': next((m for m in book['markets'] if m['key'] == 'h2h'), None),
                'totals': next((m for m in book['markets'] if m['key'] == 'totals'), None),
                'vig': book.get('vig', 0)
            }
            for book in bookmakers if book['key'] in SPORTSBOOKS
        }

# --- API Service ---
class OddsAPI:
    @staticmethod
    def fetch_games(league):
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
            params = {
                'apiKey': API_KEY,
                'regions': 'us',
                'markets': 'h2h,totals',
                'oddsFormat': 'american',
                'dateFormat': 'iso'
            }
            response = requests.get(url, params=params)
            return [Game(game) for game in response.json()[:MAX_GAMES]] if response.ok else []
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return []

# --- Data Refresh System ---
def start_background_refresh():
    def refresh_loop():
        while True:
            st.session_state.last_refresh = datetime.now()
            for league in LEAGUES:
                st.session_state.games[league] = OddsAPI.fetch_games(league.lower())
            time.sleep(API_INTERVAL)
    
    if 'refresh_thread' not in st.session_state:
        st.session_state.refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        st.session_state.refresh_thread.start()

# --- Initialize Session ---
if 'games' not in st.session_state:
    st.session_state.games = {league: [] for league in LEAGUES}
    start_background_refresh()

# --- Header ---
st.markdown("""
<div style="text-align:center">
<h1 style="color:#00ffe7;text-shadow:0 0 10px #0ff">Omniscience Elite v3.0</h1>
<h3 style="color:#ff00c8">The All-Seeing Odds Oracle</h3>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ Oracle Controls")
    selected_leagues = st.multiselect(
        "🏆 Select Leagues", 
        LEAGUES, 
        default=["MLB", "NBA"],
        key="league_select"
    )
    
    st.markdown("### 📊 Display Options")
    show_vig = st.toggle("Show Vig", True, key="vig_toggle")
    show_totals = st.toggle("Show Totals", True, key="totals_toggle")
    
    if 'last_refresh' in st.session_state:
        st.markdown(f"🔄 Last Refresh: {st.session_state.last_refresh.strftime('%H:%M:%S UTC')}")
    st.button("Force Refresh", on_click=lambda: start_background_refresh())

# --- Main Tabs ---
tab1, tab2 = st.tabs(["🎲 Live Odds", "📈 Advanced Analytics"])

# --- Tab 1: Live Odds ---
with tab1:
    for league in selected_leagues:
        st.subheader(f"🏟️ {league} Games")
        
        if not st.session_state.games[league]:
            st.warning(f"No {league} games found")
            continue
            
        for game in st.session_state.games[league]:
            with st.expander(f"{game.away} @ {game.home}", expanded=True):
                cols = st.columns(3)
                
                # Game Info
                cols[0].markdown(f"""
                **⏰ Start Time**  
                {game.start_time.strftime('%m/%d %I:%M %p ET')}  
                **📊 League**  
                {league}
                """)
                
                # Moneyline Odds
                odds_col = cols[1].container()
                odds_col.markdown("**💰 Moneyline**")
                for book in SPORTSBOOKS:
                    if book in game.odds and game.odds[book]['moneyline']:
                        ml = game.odds[book]['moneyline']
                        away_odds = next(o['price'] for o in ml['outcomes'] if o['name'] == game.away)
                        home_odds = next(o['price'] for o in ml['outcomes'] if o['name'] == game.home)
                        
                        odds_col.markdown(f"""
                        **{book}**  
                        {game.away}: {away_odds}  
                        {game.home}: {home_odds}  
                        {f"Vig: {game.odds[book]['vig']}%" if show_vig else ""}
                        """)
                
                # Totals
                if show_totals:
                    totals_col = cols[2].container()
                    totals_col.markdown("**🔢 Totals**")
                    for book in SPORTSBOOKS:
                        if book in game.odds and game.odds[book]['totals']:
                            total = game.odds[book]['totals']
                            over = next(o for o in total['outcomes'] if o['name'] == 'Over')
                            under = next(o for o in total['outcomes'] if o['name'] == 'Under')
                            
                            totals_col.markdown(f"""
                            **{book}**  
                            O {over['point']}: {over['price']}  
                            U {under['point']}: {under['price']}  
                            {f"Vig: {game.odds[book]['vig']}%" if show_vig else ""}
                            """)

# --- Tab 2: Analytics ---
with tab2:
    st.subheader("🔮 Predictive Models")
    selected_model = st.selectbox(
        "Select Model", 
        ["Bat Speed Predictor", "Vig-Adjusted CLV", "Prop Value Finder"],
        key="model_select"
    )
    
    if selected_model == "Bat Speed Predictor":
        st.markdown("### 🏏 Bat Speed Oscillator")
        # [Your existing bat speed analytics here]
        
    elif selected_model == "Vig-Adjusted CLV":
        st.markdown("### 💰 Closing Line Value Calculator")
        # Add vig-adjusted CLV calculations
        
    elif selected_model == "Prop Value Finder":
        st.markdown("### 🔍 Prop Bet Value Scanner")
        # Add prop value analysis

# --- Footer ---
st.markdown("---")
st.markdown("""
<p style="text-align:center;color:#888">
Omniscience Elite v3.0 &copy; 2025 | 
<span style="color:#00ffe7">Real-time odds refresh every 30 minutes</span>
</p>
""", unsafe_allow_html=True)
