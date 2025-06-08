import streamlit as st
from utils.api import fetch_odds_data, fetch_player_stats
from utils.models import PlayerProjection, BettingAnalyzer
from utils.visuals import set_background, render_matchup_card
from ask import ask_omniscience_ui
from analytics.tracker import prediction_dashboard, outcome_entry_form
from analytics.autoeval import evaluate_uploaded_results, summarize_accuracy
import pandas as pd
import logging
from dotenv import load_dotenv
import os
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Omniscience Sports",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'previous_sport' not in st.session_state:
    st.session_state.previous_sport = None
if 'previous_market' not in st.session_state:
    st.session_state.previous_market = None
if 'current_data' not in st.session_state:
    st.session_state.current_data = None

try:
    set_background("eye_background2.jpg")
except Exception as e:
    logger.error(f"Error setting background: {str(e)}")

# Get API key from environment or secrets
SPORTSGAME_API = os.getenv('SPORTSGAME_API', st.secrets.get("SPORTSGAME_API"))
if not SPORTSGAME_API:
    st.error("API key not found. Please set SPORTSGAME_API in environment or secrets.")
    st.stop()

# Sidebar setup
st.sidebar.image("eye_background.jpg", use_column_width=True)
st.sidebar.title("Omniscience: Divine Sports Intelligence")

selected_tab = st.sidebar.radio("Navigate", ["Dashboard", "Ask", "Tracking"])
selected_sport = st.sidebar.selectbox("Choose Sport", [
    "nba", "nfl", "mlb", "nhl", "soccer", "ncaab", 
    "ncaaf", "wnba", "college_baseball"
])
market = st.sidebar.selectbox("Market", [
    "h2h", "spreads", "totals",
    "player_points", "player_assists", "player_rebounds", "player_blocks",
    "player_steals", "player_touchdowns", "player_passing_yards",
    "player_rushing_yards", "player_hits", "player_home_runs",
    "player_rbis", "player_runs", "player_total_bases", "player_strikeouts",
    "player_walks", "player_singles", "player_doubles", "player_triples"
])
refresh = st.sidebar.button("⚡ Refresh")

# Main content
if selected_tab == "Dashboard":
    st.title(f"Omniscient Matchups - {selected_sport.upper()} [{market}]")
    
    try:
        # Only fetch new data if necessary
        if (st.session_state.previous_sport != selected_sport or 
            st.session_state.previous_market != market or 
            refresh):
            
            logger.info(f"Fetching new data for {selected_sport} - {market}")
            data = fetch_odds_data(selected_sport, market, SPORTSGAME_API)
            
            st.session_state.previous_sport = selected_sport
            st.session_state.previous_market = market
            st.session_state.current_data = data
        else:
            data = st.session_state.current_data

        if data:
            for game in data:
                try:
                    render_matchup_card(game)
                    if st.button(f"🧠 Analyze {game['home_team']} vs {game['away_team']}", 
                               key=game['id']):
                        with st.spinner("Analyzing matchup..."):
                            stats = fetch_player_stats(game, SPORTSGAME_API)
                            projections = [PlayerProjection(p) for p in stats]
                            analyzer = BettingAnalyzer(projections)
                            analyzer.analyze_odds(game['markets'])

                            st.subheader("📊 Divine Value Plays")
                            df = pd.DataFrame(analyzer.value_plays)
                            st.dataframe(df)
                            
                            st.subheader("♾️ Arbitrage Opportunities")
                            st.dataframe(pd.DataFrame(analyzer.arb_opportunities))
                except Exception as e:
                    logger.error(f"Error processing game: {str(e)}")
                    st.error(f"Error processing game data")
        else:
            st.warning("No matchups available for the selected criteria.")
            
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        logger.error(traceback.format_exc())
        st.error("An error occurred while loading the dashboard")

elif selected_tab == "Ask":
    try:
        analyzer = BettingAnalyzer([])
        ask_omniscience_ui(analyzer, selected_sport)
    except Exception as e:
        logger.error(f"Ask tab error: {str(e)}")
        st.error("An error occurred in the Ask section")

elif selected_tab == "Tracking":
    try:
        prediction_dashboard()
        outcome_entry_form()
        
        st.subheader("📤 Upload Outcomes")
        uploaded = st.file_uploader("Upload results CSV", type=["csv"])
        
        if uploaded:
            with st.spinner("Processing results..."):
                inserted, msg = evaluate_uploaded_results(uploaded)
                if inserted:
                    st.success(msg)
                    df, acc = summarize_accuracy()
                    st.metric("Model Accuracy", f"{acc*100:.2f}%")
                    st.dataframe(df.head(20))
                else:
                    st.error(msg)
    except Exception as e:
        logger.error(f"Tracking tab error: {str(e)}")
        st.error("An error occurred in the Tracking section")
