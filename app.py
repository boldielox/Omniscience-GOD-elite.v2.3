import streamlit as st
from utils.data_manager import DataManager, BettingAnalyzer
from utils.api import fetch_nba_games, fetch_player_stats
from utils.visuals import render_matchup_card, create_trend_chart
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize data manager and analyzer
data_manager = DataManager()
analyzer = BettingAnalyzer()

# Streamlit page config
st.set_page_config(page_title="NBA Predictions", layout="wide")

# Sidebar
st.sidebar.title("NBA Predictions")
selected_date = st.sidebar.date_input("Select Date", datetime.now())

# Main content
st.title(f"NBA Games - {selected_date.strftime('%B %d, %Y')}")

# Fetch games
games = fetch_nba_games(selected_date)

if games:
    for game in games:
        render_matchup_card(game)
        
        if st.button(f"🏀 Analyze", key=f"analyze_{game['id']}"):
            with st.spinner("Analyzing..."):
                # Get prediction
                prediction = analyzer.analyze_game(
                    game['home_team']['full_name'],
                    game['visitor_team']['full_name']
                )
                
                # Display prediction
                st.subheader("Game Prediction")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Predicted Home Score",
                        prediction['predicted_home_score']
                    )
                
                with col2:
                    st.metric(
                        "Predicted Away Score",
                        prediction['predicted_away_score']
                    )
                
                # Display betting analysis
                st.subheader("Betting Analysis")
                st.write(f"**Spread:** {prediction['spread']} points")
                st.write(f"**Total:** {prediction['total']} points")
                st.write(f"**Confidence:** {prediction['confidence']}")
                
                # Display trends
                st.subheader("Trends")
                for trend in prediction['trends']:
                    st.write(f"• {trend}")
else:
    st.info("No games found for selected date.")
