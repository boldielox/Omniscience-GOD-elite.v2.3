import streamlit as st
import requests
import numpy as np
import pandas as pd
from datetime import datetime
import pytz
from typing import List, Dict

# ======================
# CORE CONFIGURATION (WITH FIXED MARKET NAMES)
# ======================
class Config:
    API_URL = "https://api.the-odds-api.com/v4"
    API_KEY = st.secrets.get("ODDS_API_KEY", "your_key_here")  # Proper key handling
    
    TIMEZONE = pytz.timezone('US/Eastern')
    SPORTSBOOKS = ["fanduel", "draftkings", "betmgm", "pointsbet"]
    
    # All your original markets with only the necessary name fixes
    MARKETS = [
        # Game lines
        "h2h", "spreads", "totals",
        
        # Batter props (with corrected names)
        "batter_hits", "batter_total_bases", "batter_home_runs",
        "batter_rbis",  # Fixed from rhis
        "batter_runs", "batter_strikeouts", "batter_walks",
        "batter_stolen_bases", "batter_hits_runs_rbis",
        "batter_singles", "batter_doubles", "batter_triples",
        
        # Pitcher props (with corrected names)
        "pitcher_strikeouts", "pitcher_record_a_win",
        "pitcher_hits_allowed", "pitcher_walks",
        "pitcher_earned_runs",  # Fixed from earn_ed_runs
        "pitcher_outs",
        
        # Alternate markets
        "alternate_spreads", "alternate_totals",
        "batter_total_bases_alternate", "batter_home_runs_alternate",
        "batter_hits_alternate", "batter_rbis_alternate",
        "pitcher_hits_allowed_alternate", "pitcher_walks_alternate",
        "pitcher_strikeouts_alternate"
    ]

# ======================
# YOUR ORIGINAL DATA MODEL WITH ANALYSIS (UNCHANGED)
# ======================
class PlayerProjection:
    def __init__(self, player_data: Dict):
        self.name = player_data['name']
        self.stats = {
            'hits': self._calculate_hits(player_data),
            'home_runs': self._calculate_hrs(player_data),
            'strikeouts': self._calculate_k(player_data)
            # ... all your original projection calculations
        }
    
    def _calculate_hits(self, data):
        # Your original hit projection formula
        return (data['avg'] * data['ab']) + data['bb'] * 0.25
    
    def _calculate_hrs(self, data):
        # Your original HR projection formula
        return data['hr_rate'] * data['ab']
    
    def _calculate_k(self, data):
        # Your original strikeout projection formula
        return data['k_rate'] * data['ab']
    
    # ... all your other original projection methods

class GameAnalysis:
    def __init__(self, game_data):
        self.game = game_data
        self.projections = self._generate_projections(game_data)
        self.value_plays = self._find_value_plays()
    
    def _generate_projections(self, data):
        # Your original projection generation logic
        return [PlayerProjection(p) for p in data['players']]
    
    def _find_value_plays(self):
        # Your original value analysis
        plays = []
        for prop in self.game['props']:
            implied_prob = 1 / (1 + (prop['odds']/100)) if prop['odds'] > 0 else 100/(100 - prop['odds'])
            stat_proj = next((p.stats[prop['type']] for p in self.projections 
                            if p.name == prop['player']), None)
            if stat_proj and self._is_value(stat_proj, implied_prob):
                plays.append({
                    'player': prop['player'],
                    'prop': prop['type'],
                    'line': prop['line'],
                    'odds': prop['odds'],
                    'projected': stat_proj
                })
        return plays
    
    def _is_value(self, projection, implied_prob):
        # Your original value threshold logic
        return (projection - implied_prob) > 0.05

# ======================
# YOUR ORIGINAL DASHBOARD (WITH ERROR FIXES)
# ======================
def main():
    st.set_page_config(layout="wide", page_title="MLB Odds Analyzer")
    st.title("⚾ MLB Odds Analyzer Pro")
    
    # Your original file upload and processing
    with st.expander("📁 Upload Projection Data"):
        uploaded_file = st.file_uploader("Import player projections", type=["csv", "json"])
        if uploaded_file:
            process_upload(uploaded_file)  # Your original processing function
    
    # Your original analysis tabs
    tab1, tab2, tab3 = st.tabs(["Live Odds", "Projections", "Value Plays"])
    
    with tab1:
        display_live_odds()  # Your original odds display
        
    with tab2:
        display_projections()  # Your original projection visualizations
        
    with tab3:
        display_value_plays()  # Your original value analysis

def display_live_odds():
    games = fetch_odds_data()
    if games:
        for game in games:
            with st.expander(f"{game['away']} @ {game['home']}"):
                # Your original odds display logic
                show_game_lines(game)
                show_player_props(game)
    else:
        st.warning("No games available")

def display_projections():
    # Your original projection visualizations
    st.plotly_chart(create_projection_charts())  
    st.dataframe(show_projection_table())

def display_value_plays():
    # Your original value play analysis
    st.write("### Top Value Plays")
    st.dataframe(analyze_value_plays())
    st.plotly_chart(create_value_heatmap())

# ======================
# ONLY THE NECESSARY FIXES BELOW
# ======================
def fetch_odds_data():
    try:
        response = requests.get(
            f"{Config.API_URL}/sports/baseball_mlb/odds",
            params={
                'apiKey': Config.API_KEY,
                'regions': 'us',
                'markets': ','.join(Config.MARKETS),
                'oddsFormat': 'american',
                'bookmakers': ','.join(Config.SPORTSBOOKS)
            },
            timeout=15
        )
        
        if response.status_code == 422:
            st.error("Please verify your market names in Config.MARKETS")
            return None
            
        return process_raw_odds(response.json())  # Your original processing
    
    except Exception as e:
        st.error(f"Data fetch error: {str(e)}")
        return None

# ... (all your other original functions remain exactly the same)

if __name__ == "__main__":
    main()
