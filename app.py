import streamlit as st
from utils.api import fetch_nba_games, fetch_player_stats
from utils.data_manager import DataManager
from utils.visuals import render_matchup_card
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize
st.set_page_config(page_title="NBA Predictions", layout="wide")
data_manager = DataManager()

# Sidebar
st.sidebar.title("NBA Predictions")
selected_date = st.sidebar.date_input(
    "Select Date",
    datetime.now(),
    min_value=datetime.now() - timedelta(days=7),
    max_value=datetime.now() + timedelta(days=7)
)

# Main content
st.title(f"NBA Games - {selected_date.strftime('%B %d, %Y')}")

# Fetch games
games = fetch_nba_games(selected_date)

if games:
    for game in games:
        render_matchup_card(game)
        
        if st.button(f"🏀 Analyze", key=f"analyze_{game['id']}"):
            with st.spinner("Analyzing..."):
                # Get team histories
                home_history = data_manager.get_team_history(
                    game['home_team']['full_name']
                )
                away_history = data_manager.get_team_history(
                    game['visitor_team']['full_name']
                )
                
                # Display analysis
                st.subheader("Team Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**{game['home_team']['full_name']}**")
                    if not home_history.empty:
                        st.dataframe(home_history)
                    else:
                        st.write("No historical data available")
                
                with col2:
                    st.write(f"**{game['visitor_team']['full_name']}**")
                    if not away_history.empty:
                        st.dataframe(away_history)
                    else:
                        st.write("No historical data available")
else:
    st.info("No games found for selected date.")
