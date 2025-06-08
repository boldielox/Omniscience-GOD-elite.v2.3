import streamlit as st
from utils.api import fetch_nba_games, fetch_player_stats
from utils.models import PlayerProjection, BettingAnalyzer
from utils.visuals import set_background, render_matchup_card
from ask import ask_omniscience_ui
from analytics.tracker import prediction_dashboard, outcome_entry_form
from analytics.autoeval import evaluate_uploaded_results, summarize_accuracy
import pandas as pd
import logging
from datetime import datetime, timedelta
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="NBA Omniscience",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'previous_date' not in st.session_state:
    st.session_state.previous_date = None
if 'current_data' not in st.session_state:
    st.session_state.current_data = None

# Sidebar setup without background image
st.sidebar.title("NBA Omniscience: Divine Basketball Intelligence")
st.sidebar.markdown("---")

selected_tab = st.sidebar.radio("Navigate", ["Games", "Players", "Analysis"])

# Date selector for games
today = datetime.now()
selected_date = st.sidebar.date_input(
    "Select Date",
    value=today,
    min_value=today - timedelta(days=365),
    max_value=today + timedelta(days=7)
)

refresh = st.sidebar.button("⚡ Refresh")

# Main content
if selected_tab == "Games":
    st.title(f"NBA Games - {selected_date.strftime('%B %d, %Y')}")
    
    try:
        # Only fetch new data if necessary
        if (st.session_state.previous_date != selected_date or refresh):
            logger.info(f"Fetching new data for {selected_date}")
            data = fetch_nba_games(selected_date)
            
            st.session_state.previous_date = selected_date
            st.session_state.current_data = data
        else:
            data = st.session_state.current_data

        if data:
            for game in data:
                try:
                    render_matchup_card(game)
                    if st.button(f"🏀 Analyze {game['home_team']['full_name']} vs {game['visitor_team']['full_name']}", 
                               key=game['id']):
                        with st.spinner("Analyzing matchup..."):
                            # Fetch detailed stats for both teams
                            home_stats = fetch_player_stats(game['home_team']['id'])
                            away_stats = fetch_player_stats(game['visitor_team']['id'])
                            
                            # Combine and analyze
                            all_stats = home_stats + away_stats
                            projections = [PlayerProjection(p) for p in all_stats]
                            analyzer = BettingAnalyzer(projections)
                            
                            # Display team analysis
                            st.subheader("📊 Team Analysis")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**{game['home_team']['full_name']}**")
                                home_df = pd.DataFrame(home_stats)
                                if not home_df.empty:
                                    st.dataframe(home_df[['player_name', 'pts', 'reb', 'ast', 'stl', 'blk']], 
                                               use_container_width=True)
                            
                            with col2:
                                st.write(f"**{game['visitor_team']['full_name']}**")
                                away_df = pd.DataFrame(away_stats)
                                if not away_df.empty:
