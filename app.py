# app.py
import streamlit as st
from utils.api import fetch_odds_data, fetch_player_stats
from utils.models import PlayerProjection, BettingAnalyzer
from utils.visuals import set_background, render_matchup_card
from ask import ask_omniscience_ui
from analytics.tracker import prediction_dashboard, outcome_entry_form
from analytics.autoeval import evaluate_uploaded_results, summarize_accuracy
import pandas as pd

set_background("eye_background2.jpg")
SPORTGAMEODDS_API_KEY = st.secrets["SPORTGAMEODDS_API_KEY"]

st.sidebar.image("eye_background.jpg", use_column_width=True)
st.sidebar.title("Omniscience: Divine Sports Intelligence")

selected_tab = st.sidebar.radio("Navigate", ["Dashboard", "Ask", "Tracking"])
selected_sport = st.sidebar.selectbox("Choose Sport", ["nba", "nfl", "mlb", "nhl", "soccer", "ncaab", "ncaaf", "wnba", "college_baseball"])
market = st.sidebar.selectbox("Market", [
    "h2h", "spreads", "totals",
    "player_points", "player_assists", "player_rebounds", "player_blocks",
    "player_steals", "player_touchdowns", "player_passing_yards",
    "player_rushing_yards", "player_hits", "player_home_runs",
    "player_rbis", "player_runs", "player_total_bases", "player_strikeouts",
    "player_walks", "player_singles", "player_doubles", "player_triples"
])
refresh = st.sidebar.button("⚡ Refresh")

if selected_tab == "Dashboard":
    st.title(f"Omniscient Matchups - {selected_sport.upper()} [{market}]")
    data = fetch_odds_data(selected_sport, market, SPORTGAMEODDS_API_KEY)
    if data:
        for game in data:
            render_matchup_card(game)
            if st.button(f"🧠 Analyze {game['home_team']} vs {game['away_team']}", key=game['id']):
                stats = fetch_player_stats(game, SPORTGAMEODDS_API_KEY)
                projections = [PlayerProjection(p) for p in stats]
                analyzer = BettingAnalyzer(projections)
                analyzer.analyze_odds(game['markets'])

                st.subheader("📊 Divine Value Plays")
                df = pd.DataFrame(analyzer.value_plays)
                st.dataframe(df)
                st.subheader("♾️ Arbitrage Opportunities")
                st.dataframe(pd.DataFrame(analyzer.arb_opportunities))
    else:
        st.error("No matchups found.")

elif selected_tab == "Ask":
    analyzer = BettingAnalyzer([])  # Fallback
    ask_omniscience_ui(analyzer, selected_sport)

elif selected_tab == "Tracking":
    prediction_dashboard()
    outcome_entry_form()
    st.subheader("📤 Upload Outcomes")
    uploaded = st.file_uploader("Upload results CSV", type=["csv"])
    if uploaded:
        inserted, msg = evaluate_uploaded_results(uploaded)
        st.success(msg)
        df, acc = summarize_accuracy()
        st.metric("Model Accuracy", f"{acc*100:.2f}%")
        st.dataframe(df.head(20))
