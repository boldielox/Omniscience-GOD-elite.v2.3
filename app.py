import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

class Config:
    API_URL = "https://api.the-odds-api.com/v4"
    API_KEY = st.secrets.get("ODDS_API_KEY", "your_key_here")  # Proper key handling
    
    # App constants
    TIMEZONE = pytz.timezone('US/Eastern')
    SPORTSBOOKS = ["fanduel", "draftkings", "betmgm", "pointsbet"]
    
    # Validated MLB markets
    MARKETS = {
        "game": ["h2h", "spreads", "totals"],
        "batter": [
            "batter_hits",
            "batter_total_bases",
            "batter_home_runs",
            "batter_rbis",  # Fixed
            "batter_runs",
            "batter_strikeouts"
        ],
        "pitcher": [
            "pitcher_strikeouts",
            "pitcher_earned_runs",  # Fixed
            "pitcher_hits_allowed"
        ]
    }

class Game:
    def __init__(self, data):
        self.id = data['id']
        self.sport_key = data['sport_key']
        self.home = data['home_team']
        self.away = data['away_team']
        self.start_time = datetime.fromisoformat(data['commence_time'][:-1]).astimezone(Config.TIMEZONE)
        self.bookmakers = data['bookmakers']

def fetch_mlb_odds():
    try:
        # First verify API key
        test_response = requests.get(
            f"{Config.API_URL}/sports",
            params={'apiKey': Config.API_KEY},
            timeout=5
        )
        if test_response.status_code == 401:
            st.error("Invalid API Key - Please check your key")
            return None

        # Fetch in chunks to avoid size limits
        all_games = []
        for market_type, markets in Config.MARKETS.items():
            response = requests.get(
                f"{Config.API_URL}/sports/baseball_mlb/odds",
                params={
                    'apiKey': Config.API_KEY,
                    'regions': 'us',
                    'markets': ','.join(markets),
                    'oddsFormat': 'american',
                    'bookmakers': ','.join(Config.SPORTSBOOKS)
                },
                timeout=15
            )
            
            if response.status_code == 422:
                st.warning(f"Some {market_type} markets unavailable")
                continue
                
            response.raise_for_status()
            all_games.extend(response.json())

        return [Game(game) for game in all_games] if all_games else None

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def main():
    st.set_page_config(layout="wide", page_title="MLB Odds Pro")
    st.title("MLB Odds Dashboard")
    
    # Your original file uploader
    with st.expander("📁 Data Upload"):
        uploaded_file = st.file_uploader("Import data", type=["csv", "json"])
        if uploaded_file:
            st.success(f"Loaded {uploaded_file.name}")

    if st.button("🔄 Refresh Odds"):
        with st.spinner("Loading latest odds..."):
            games = fetch_mlb_odds()
            
            if games:
                for game in games:
                    with st.expander(f"{game.away} @ {game.home}"):
                        # Game lines
                        st.write("Game Lines")
                        display_game_lines(game)
                        
                        # Player props
                        st.write("Player Props")
                        display_player_props(game)
            else:
                st.warning("No games available")

def display_game_lines(game):
    lines = []
    for book in game.bookmakers:
        if book['key'] in Config.SPORTSBOOKS:
            entry = {"Sportsbook": book['key'].title()}
            for market in book['markets']:
                if market['key'] in Config.MARKETS['game']:
                    for outcome in market['outcomes']:
                        if market['key'] == 'h2h':
                            entry[f"{outcome['name']} ML"] = outcome['price']
                        elif market['key'] == 'spreads':
                            entry["Spread"] = f"{outcome['point']} ({outcome['price']})"
                        elif market['key'] == 'totals':
                            entry["Total"] = f"{outcome['point']} ({outcome['price']})"
            lines.append(entry)
    st.dataframe(pd.DataFrame(lines))

def display_player_props(game):
    props = []
    for book in game.bookmakers:
        if book['key'] in Config.SPORTSBOOKS:
            for market in book['markets']:
                if market['key'] in Config.MARKETS['batter'] + Config.MARKETS['pitcher']:
                    for outcome in market['outcomes']:
                        props.append({
                            "Sportsbook": book['key'].title(),
                            "Player": outcome.get('description', outcome.get('name')),
                            "Prop": market['key'].replace('_', ' ').title(),
                            "Line": outcome.get('point', 'N/A'),
                            "Odds": outcome.get('price', 'N/A')
                        })
    if props:
        st.dataframe(pd.DataFrame(props))
    else:
        st.info("No player props available")

if __name__ == "__main__":
    main()
