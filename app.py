import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

# ======================
# CONFIGURATION (WITH ALL MARKET TYPES)
# ======================
class Config:
    API_URL = "https://api.the-odds-api.com/v4"
    API_KEY = "17e75d302045aed4532e57f97d6609e3"  # Your actual key
    
    TIMEZONE = pytz.timezone('US/Eastern')
    SPORTSBOOKS = ["fanduel", "draftkings", "betmgm", "pointsbet"]
    
    # COMPLETE MARKET LIST FROM ALL YOUR IMAGES
    MARKETS = [
        # Core markets (from 525.jpg)
        "h2h", "spreads", "totals",
        
        # Alternate markets (from 526.jpg)
        "alternate_spreads", "alternate_totals", "btts",
        
        # Period-specific markets (from 530.jpg and 532.jpg)
        "spreads_h2", "spreads_p1", "spreads_p2", "spreads_p3",
        "spreads_1st_1_innings", "spreads_1st_3_innings",
        "spreads_1st_5_innings", "spreads_1st_7_innings",
        "alternate_spreads_1st_1_innings",
        "h2h_1st_1_innings", "h2h_1st_3_innings",
        "h2h_1st_5_innings", "h2h_1st_7_innings",
        "h2h_3_way_1st_1_innings", "h2h_3_way_1st_3_innings",
        "h2h_3_way_1st_5_innings", "h2h_3_way_1st_7_innings",
        
        # Player props (from your previous images)
        "batter_home_runs", "batter_first_home_run",
        "batter_hits", "batter_total_bases", "batter_rbis",
        "batter_runs_scored", "batter_hits_runs_rbis",
        "batter_singles", "batter_doubles", "batter_triples",
        "batter_walks", "batter_strikeouts", "batter_stolen_bases",
        "pitcher_strikeouts", "pitcher_record_a_win",
        "pitcher_hits_allowed", "pitcher_walks",
        "pitcher_earned_runs", "pitcher_outs",
        "batter_total_bases_alternate", "batter_home_runs_alternate",
        "batter_hits_alternate", "batter_rbis_alternate",
        "pitcher_hits_allowed_alternate", "pitcher_walks_alternate",
        "pitcher_strikeouts_alternate"
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
                    'spreads': next((m for m in book['markets'] if m['key'] == 'spreads'), None),
                    'totals': next((m for m in book['markets'] if m['key'] == 'totals'), None),
                    'alternates': {
                        m['key']: m for m in book['markets']
                        if m['key'] in ['alternate_spreads', 'alternate_totals']
                    },
                    'periods': {
                        m['key']: m for m in book['markets']
                        if any(m['key'].startswith(prefix) 
                        for prefix in ['spreads_', 'h2h_'])
                    },
                    'player_props': {
                        m['key']: m for m in book['markets']
                        if m['key'] in Config.MARKETS 
                        and m['key'] not in ['h2h', 'spreads', 'totals',
                                            'alternate_spreads', 'alternate_totals']
                        and not any(m['key'].startswith(prefix) 
                        for prefix in ['spreads_', 'h2h_'])
                    }
                }
        return odds_data

# ======================
# ORIGINAL FETCH FUNCTION (ENHANCED)
# ======================
def fetch_games():
    try:
        # Split markets into chunks to avoid URI too long errors
        market_chunks = [Config.MARKETS[i:i+15] for i in range(0, len(Config.MARKETS), 15)]
        
        all_games = []
        for chunk in market_chunks:
            response = requests.get(
                f"{Config.API_URL}/sports/baseball_mlb/odds",
                params={
                    'apiKey': Config.API_KEY,
                    'regions': 'us',
                    'markets': ','.join(chunk),
                    'oddsFormat': 'american',
                    'bookmakers': ','.join(Config.SPORTSBOOKS)
                },
                timeout=20
            )
            
            if response.status_code == 422:
                error_detail = response.json().get('detail', 'Invalid market names')
                st.error(f"API rejected these markets: {chunk}")
                st.error(f"Error: {error_detail}")
                continue
                
            response.raise_for_status()
            all_games.extend(response.json())
        
        return [Game(game) for game in all_games] if all_games else None
        
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")
        return None

# ======================
# YOUR ORIGINAL DASHBOARD (ENHANCED DISPLAY)
# ======================
def main():
    st.set_page_config(layout="wide", page_title="MLB Odds Dashboard")
    st.title("MLB Odds Dashboard")
    
    # Your original file upload section
    with st.expander("📁 Upload Custom Data", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload your data (CSV/JSON)", 
            type=["csv", "json"],
            key="original_file_uploader"
        )
        if uploaded_file:
            st.success(f"Uploaded: {uploaded_file.name}")
    
    # Market type selector
    market_type = st.selectbox(
        "Select Market Type",
        ["Game Lines", "Alternates", "Periods", "Player Props"],
        key="market_type_selector"
    )
    
    if st.button("🔄 Refresh All Data", key="refresh_all_button"):
        games = fetch_games()
        
        if games:
            for game in games:
                with st.expander(f"{game.away} @ {game.home} | {game.start_time.strftime('%m/%d %I:%M %p ET')}"):
                    # Display based on selected market type
                    if market_type == "Game Lines":
                        display_game_lines(game)
                    elif market_type == "Alternates":
                        display_alternates(game)
                    elif market_type == "Periods":
                        display_periods(game)
                    else:
                        display_player_props(game)
        else:
            st.warning("No games available or failed to load data")

def display_game_lines(game):
    st.subheader("Game Lines")
    lines_data = []
    for book, odds in game.odds.items():
        lines_data.append({
            "Sportsbook": book.title(),
            "Moneyline (Away)": get_outcome_price(odds['moneyline'], game.away),
            "Moneyline (Home)": get_outcome_price(odds['moneyline'], game.home),
            "Spread": format_spread(odds['spreads'], game.away),
            "Total": format_total(odds['totals'])
        })
    st.dataframe(pd.DataFrame(lines_data))

def display_alternates(game):
    st.subheader("Alternate Markets")
    alt_data = []
    for book, odds in game.odds.items():
        for market_key, market in odds['alternates'].items():
            for outcome in market.get('outcomes', []):
                alt_data.append({
                    "Sportsbook": book.title(),
                    "Market": market_key.replace('_', ' ').title(),
                    "Selection": outcome.get('name'),
                    "Line": outcome.get('point', 'N/A'),
                    "Odds": outcome.get('price', 'N/A')
                })
    if alt_data:
        st.dataframe(pd.DataFrame(alt_data))
    else:
        st.warning("No alternate markets available")

def display_periods(game):
    st.subheader("Period-Specific Markets")
    period_data = []
    for book, odds in game.odds.items():
        for market_key, market in odds['periods'].items():
            for outcome in market.get('outcomes', []):
                period_data.append({
                    "Sportsbook": book.title(),
                    "Period": market_key.split('_')[0].upper(),
                    "Market": ' '.join(market_key.split('_')[1:]).title(),
                    "Selection": outcome.get('name'),
                    "Line": outcome.get('point', 'N/A'),
                    "Odds": outcome.get('price', 'N/A')
                })
    if period_data:
        st.dataframe(pd.DataFrame(period_data))
    else:
        st.warning("No period markets available")

def display_player_props(game):
    st.subheader("Player Props")
    prop_data = []
    for book, odds in game.odds.items():
        for prop_name, market in odds['player_props'].items():
            if market:
                for outcome in market.get('outcomes', []):
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

# Helper functions
def get_outcome_price(market, team):
    if not market:
        return "N/A"
    return next((o['price'] for o in market['outcomes'] if o['name'] == team), "N/A")

def format_spread(market, team):
    if not market:
        return "N/A"
    point = next((o['point'] for o in market['outcomes'] if o['name'] == team), "N/A")
    price = next((o['price'] for o in market['outcomes'] if o['name'] == team), "N/A")
    return f"{point} ({price})"

def format_total(market):
    if not market:
        return "N/A"
    over = next((o for o in market['outcomes'] if o['name'] == 'Over'), None)
    if not over:
        return "N/A"
    return f"O {over.get('point', 'N/A')} ({over.get('price', 'N/A')})"

if __name__ == "__main__":
    main()
