import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz

# ======================
# CONFIGURATION
# ======================
class Config:
    # API Key - Replace with your actual key or use Streamlit secrets
    API_KEY = "17e75d302045aed4532e57f97d6609e3"  # Example key - use your real one
    
    API_URL = "https://api.the-odds-api.com/v4"
    TIMEZONE = pytz.timezone('US/Eastern')
    SPORTSBOOKS = ["fanduel", "draftkings", "betmgm", "pointsbet"]
    
    # Validated market names
    MARKETS = {
        "game": ["h2h", "spreads", "totals"],
        "batter": [
            "batter_hits",
            "batter_total_bases",
            "batter_home_runs",
            "batter_rbis",  # RBIs
            "batter_runs",
            "batter_strikeouts"
        ],
        "pitcher": [
            "pitcher_strikeouts",
            "pitcher_earned_runs"
        ]
    }

# ======================
# DATA FETCHING
# ======================
def fetch_mlb_odds():
    """Fetch MLB odds with proper error handling"""
    try:
        # Combine all markets
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
            timeout=10
        )
        
        # Special handling for 401 errors
        if response.status_code == 401:
            st.error("Invalid API Key - Please check your key and try again")
            return None
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
        return None

# ======================
# DATA PROCESSING
# ======================
def process_game(game_data: dict) -> dict:
    """Structure the game data for display"""
    return {
        "id": game_data.get("id"),
        "home": game_data.get("home_team"),
        "away": game_data.get("away_team"),
        "start": parse_time(game_data.get("commence_time")),
        "bookmakers": process_bookmakers(game_data.get("bookmakers", []))
    }

def process_bookmakers(bookmakers: list) -> list:
    """Extract data from each bookmaker"""
    processed = []
    for book in bookmakers:
        if book.get("key") in Config.SPORTSBOOKS:
            processed.append({
                "name": book.get("key"),
                "markets": process_markets(book.get("markets", []))
            })
    return processed

def process_markets(markets: list) -> dict:
    """Organize markets by type"""
    result = {"game": {}, "props": {}}
    for market in markets:
        key = market.get("key")
        if key in Config.MARKETS["game"]:
            result["game"][key] = market.get("outcomes", [])
        elif key in Config.MARKETS["batter"] + Config.MARKETS["pitcher"]:
            result["props"][key] = market.get("outcomes", [])
    return result

def parse_time(time_str: str) -> str:
    """Convert ISO time to readable format"""
    try:
        dt = datetime.fromisoformat(time_str[:-1]).astimezone(Config.TIMEZONE)
        return dt.strftime("%m/%d %I:%M %p ET")
    except:
        return "Time not available"

# ======================
# STREAMLIT UI
# ======================
def main():
    st.set_page_config(
        layout="wide",
        page_title="MLB Odds Tracker",
        page_icon="⚾"
    )
    
    st.title("MLB Odds Tracker")
    st.markdown("---")
    
    # File uploader section
    with st.expander("📁 Upload Custom Data", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload your own odds data (CSV/JSON)",
            type=["csv", "json"]
        )
        if uploaded_file:
            st.success(f"Uploaded {uploaded_file.name}")
            # Add your file processing logic here
    
    # API data section
    with st.expander("⚾ Live MLB Odds", expanded=True):
        if st.button("🔄 Refresh Odds"):
            with st.spinner("Fetching latest odds..."):
                games_data = fetch_mlb_odds()
                
                if games_data:
                    for game_data in games_data:
                        game = process_game(game_data)
                        render_game(game)
                else:
                    st.warning("No game data available")

def render_game(game: dict):
    """Display game information"""
    with st.expander(f"{game['away']} @ {game['home']} | {game['start']}", expanded=False):
        # Game lines
        st.subheader("Game Lines")
        game_lines = []
        for book in game["bookmakers"]:
            for market, outcomes in book["markets"]["game"].items():
                for outcome in outcomes:
                    game_lines.append({
                        "Sportsbook": book["name"].title(),
                        "Market": market.upper(),
                        "Selection": outcome.get("name"),
                        "Odds": outcome.get("price")
                    })
        
        if game_lines:
            st.dataframe(pd.DataFrame(game_lines))
        else:
            st.warning("No game lines available")
        
        # Player props
        st.subheader("Player Props")
        prop_data = []
        for book in game["bookmakers"]:
            for prop, outcomes in book["markets"]["props"].items():
                for outcome in outcomes:
                    prop_data.append({
                        "Sportsbook": book["name"].title(),
                        "Player": outcome.get("description", outcome.get("name")),
                        "Prop": prop.replace("_", " ").title(),
                        "Line": outcome.get("point", "N/A"),
                        "Odds": outcome.get("price", "N/A")
                    })
        
        if prop_data:
            st.dataframe(pd.DataFrame(prop_data))
        else:
            st.warning("No player props available")

if __name__ == "__main__":
    main()
