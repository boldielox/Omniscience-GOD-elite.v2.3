import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz

# ======================
# CONFIGURATION
# ======================
class Config:
    # Replace with your actual API key (use GitHub Secrets in production)
    API_KEY = "your_api_key_here"  # ⚠️ Never commit real keys to GitHub!
    
    API_URL = "https://api.the-odds-api.com/v4"
    TIMEZONE = pytz.timezone('US/Eastern')
    SPORTSBOOKS = ["fanduel", "draftkings", "betmgm", "pointsbet"]
    
    # Validated market names (corrected from your example)
    BASEBALL_MARKETS = {
        "game_lines": ["h2h", "spreads", "totals"],
        "player_props": [
            "batter_hits",
            "batter_total_bases",
            "batter_home_runs",
            "batter_rbis",  # Corrected from "rhis"
            "batter_runs",
            "batter_strikeouts",
            "pitcher_strikeouts",
            "pitcher_earned_runs"
        ]
    }

# ======================
# DATA FETCHING
# ======================
def fetch_odds(sport_key: str, markets: list) -> list:
    """Fetch odds with proper error handling"""
    try:
        response = requests.get(
            f"{Config.API_URL}/sports/{sport_key}/odds",
            params={
                "apiKey": Config.API_KEY,
                "regions": "us",
                "markets": ",".join(markets),
                "oddsFormat": "american",
                "bookmakers": ",".join(Config.SPORTSBOOKS)
            },
            timeout=15
        )
        
        # Check for API errors
        if response.status_code == 422:
            error_detail = response.json().get('detail', 'Unknown validation error')
            raise ValueError(f"API Validation Error: {error_detail}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data: {str(e)}")
        return None

# ======================
# DATA PROCESSING
# ======================
def process_game_data(raw_data: dict) -> dict:
    """Structure the raw API response"""
    game_data = {
        "id": raw_data.get("id"),
        "sport": raw_data.get("sport_key"),
        "home_team": raw_data.get("home_team"),
        "away_team": raw_data.get("away_team"),
        "start_time": parse_time(raw_data.get("commence_time")),
        "bookmakers": []
    }
    
    for bookmaker in raw_data.get("bookmakers", []):
        book = {
            "name": bookmaker.get("key"),
            "markets": {}
        }
        
        for market in bookmaker.get("markets", []):
            market_key = market.get("key")
            book["markets"][market_key] = market.get("outcomes", [])
        
        game_data["bookmakers"].append(book)
    
    return game_data

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
def render_game_card(game: dict):
    """Display game information and odds"""
    with st.expander(f"{game['away_team']} @ {game['home_team']} | {game['start_time']}"):
        # Game lines
        st.subheader("Game Lines")
        game_lines = []
        
        for book in game["bookmakers"]:
            for market in Config.BASEBALL_MARKETS["game_lines"]:
                if market in book["markets"]:
                    outcomes = book["markets"][market]
                    line_data = {
                        "Sportsbook": book["name"].title(),
                        "Market": market.upper(),
                        "Outcomes": " | ".join(
                            f"{o.get('name')} {o.get('price')}" 
                            for o in outcomes
                        )
                    }
                    game_lines.append(line_data)
        
        if game_lines:
            st.dataframe(pd.DataFrame(game_lines))
        else:
            st.warning("No game lines available")
        
        # Player props
        st.subheader("Player Props")
        prop_data = []
        
        for book in game["bookmakers"]:
            for market in Config.BASEBALL_MARKETS["player_props"]:
                if market in book["markets"]:
                    for outcome in book["markets"][market]:
                        prop_data.append({
                            "Sportsbook": book["name"].title(),
                            "Player": outcome.get("description", outcome.get("name")),
                            "Prop": market.replace("_", " ").title(),
                            "Line": outcome.get("point", "N/A"),
                            "Odds": outcome.get("price", "N/A")
                        })
        
        if prop_data:
            st.dataframe(pd.DataFrame(prop_data))
        else:
            st.warning("No player props available")

# ======================
# MAIN APP
# ======================
def main():
    st.set_page_config(
        layout="wide",
        page_title="Sports Odds Tracker",
        page_icon="⚾"
    )
    
    st.title("MLB Odds Tracker")
    
    # Fetch data when button clicked
    if st.button("Refresh Odds"):
        with st.spinner("Loading latest odds..."):
            all_markets = (
                Config.BASEBALL_MARKETS["game_lines"] + 
                Config.BASEBALL_MARKETS["player_props"]
            )
            
            raw_games = fetch_odds("baseball_mlb", all_markets)
            
            if raw_games:
                for raw_game in raw_games:
                    game = process_game_data(raw_game)
                    render_game_card(game)
            else:
                st.error("Failed to load games. Check your API key and connection.")

if __name__ == "__main__":
    main()
