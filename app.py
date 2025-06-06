import streamlit as st
import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class Config:
    SPORTSBOOKS = ["fanduel", "draftkings", "betmgm", "pointsbet"]
    MARKETS = [
        "h2h", "spreads", "totals",
        "batter_hits", "batter_home_runs",
        "batter_rbis", "batter_runs", "batter_strikeouts"
    ]
    TIMEZONE = pytz.timezone('US/Eastern')

class PlayerProjection:
    def __init__(self, player_data: Dict):
        self.name = player_data['name']
        self.team = player_data['team']
        self.position = player_data['position']
        self.stats = self._calculate_stats(player_data)
        self.value_score = self._compute_value_score()
        self.last_10_trend = player_data.get('last_10_trend', 1.0)
        
    def _calculate_stats(self, data) -> Dict:
        return {
            'hits': (data['avg'] * data['ab']) + (data['bb'] * 0.25),
            'home_runs': data['hr_rate'] * data['ab'],
            'strikeouts': data['k_rate'] * data['ab'],
            'rbis': data['rbi_rate'] * data['pa'],
            'walks': data['bb_rate'] * data['pa']
        }
    
    def _compute_value_score(self) -> float:
        return (self.stats['hits'] * 0.3 + 
                self.stats['home_runs'] * 0.4 +
                self.stats['rbis'] * 0.3) * 1.2

class BettingAnalyzer:
    def __init__(self, projections: List[PlayerProjection]):
        self.projections = projections
        self.value_plays = []
        self.arb_opportunities = []
        
    def analyze_odds(self, odds_data: Dict):
        if not odds_data or 'markets' not in odds_data:
            return
            
        for market in odds_data['markets']:
            self._evaluate_market(market)
            self._check_arbitrage(market)
    
    def _evaluate_market(self, market: Dict):
        player_proj = next((p for p in self.projections 
                          if p.name == market['player']), None)
        if not player_proj:
            return
        
        for book in market['books']:
            implied_prob = self._convert_odds(book['odds'])
            stat_proj = player_proj.stats.get(market['type'], 0) / 100
            
            if stat_proj > implied_prob + 0.05:
                self.value_plays.append({
                    'player': market['player'],
                    'prop': market['type'],
                    'odds': book['odds'],
                    'edge': round(stat_proj - implied_prob, 3),
                    'book': book['bookmaker']
                })
    
    def _check_arbitrage(self, market: Dict):
        if len(market['books']) < 2:
            return
        
        odds = [(b['bookmaker'], b['odds']) for b in market['books']]
        for i, (book1, odds1) in enumerate(odds):
            for book2, odds2 in odds[i+1:]:
                if (odds1 > 0 and odds2 < 0) or (odds1 < 0 and odds2 > 0):
                    arb = self._calculate_arbitrage(odds1, odds2)
                    if arb > 0:
                        self.arb_opportunities.append({
                            'player': market['player'],
                            'prop': market['type'],
                            'book1': book1,
                            'book2': book2,
                            'odds1': odds1,
                            'odds2': odds2,
                            'profit': round(arb * 100, 2)
                        })
    
    @staticmethod
    def _convert_odds(odds: int) -> float:
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    @staticmethod
    def _calculate_arbitrage(odds1: int, odds2: int) -> float:
        prob1 = BettingAnalyzer._convert_odds(odds1)
        prob2 = BettingAnalyzer._convert_odds(odds2)
        return 1 - (prob1 + prob2) if prob1 + prob2 < 1 else 0

def load_sample_data():
    players = [
        {
            'name': 'Mike Trout',
            'team': 'LAA',
            'position': 'OF',
            'avg': 0.280,
            'ab': 4,
            'bb': 0.5,
            'hr_rate': 0.06,
            'k_rate': 0.23,
            'rbi_rate': 0.15,
            'bb_rate': 0.15,
            'pa': 4.5
        },
        {
            'name': 'Shohei Ohtani',
            'team': 'LAD',
            'position': 'DH',
            'avg': 0.300,
            'ab': 4,
            'bb': 0.6,
            'hr_rate': 0.08,
            'k_rate': 0.25,
            'rbi_rate': 0.18,
            'bb_rate': 0.16,
            'pa': 4.5
        }
    ]
    
    odds = {
        'markets': [
            {
                'player': 'Mike Trout',
                'type': 'hits',
                'books': [
                    {'bookmaker': 'fanduel', 'odds': -110},
                    {'bookmaker': 'draftkings', 'odds': +105}
                ]
            },
            {
                'player': 'Shohei Ohtani',
                'type': 'home_runs',
                'books': [
                    {'bookmaker': 'fanduel', 'odds': +400},
                    {'bookmaker': 'draftkings', 'odds': +380}
                ]
            }
        ]
    }
    
    return players, odds

def main():
    st.set_page_config(layout="wide")
    st.title("MLB Betting Analysis Dashboard")
    
    # Load sample data
    player_data, odds_data = load_sample_data()
    
    # Create projections
    projections = [PlayerProjection(p) for p in player_data]
    
    # Analyze odds
    analyzer = BettingAnalyzer(projections)
    analyzer.analyze_odds(odds_data)
    
    # Display results
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Value Plays")
        if analyzer.value_plays:
            st.dataframe(pd.DataFrame(analyzer.value_plays))
        else:
            st.write("No value plays found")
            
        st.subheader("Player Projections")
        proj_data = [{
            'Name': p.name,
            'Team': p.team,
            'Position': p.position,
            'Value Score': round(p.value_score, 2)
        } for p in projections]
        st.dataframe(pd.DataFrame(proj_data))
    
    with col2:
        st.subheader("Arbitrage Opportunities")
        if analyzer.arb_opportunities:
            st.dataframe(pd.DataFrame(analyzer.arb_opportunities))
        else:
            st.write("No arbitrage opportunities found")

if __name__ == "__main__":
    main()
