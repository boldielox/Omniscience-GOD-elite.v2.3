# ======================
# IMPORTS AND SETUP
# ======================
import streamlit as st
import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional, Tuple, Union, Any
import math
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from dataclasses import dataclass
from enum import Enum
import json
import time
from concurrent.futures import ThreadPoolExecutor

# ======================
# LOGGING SETUP
# ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ======================
# CONSTANTS AND ENUMS
# ======================
class MarketType(Enum):
    H2H = "h2h"
    SPREADS = "spreads"
    TOTALS = "totals"
    BATTER_HITS = "batter_hits"
    BATTER_TOTAL_BASES = "batter_total_bases"
    BATTER_HOME_RUNS = "batter_home_runs"
    BATTER_RBIS = "batter_rbis"
    BATTER_RUNS = "batter_runs"
    BATTER_STRIKEOUTS = "batter_strikeouts"
    BATTER_WALKS = "batter_walks"
    BATTER_STOLEN_BASES = "batter_stolen_bases"
    BATTER_HITS_RUNS_RBIS = "batter_hits_runs_rbis"
    PITCHER_STRIKEOUTS = "pitcher_strikeouts"
    PITCHER_RECORD_A_WIN = "pitcher_record_a_win"
    PITCHER_HITS_ALLOWED = "pitcher_hits_allowed"
    PITCHER_EARNED_RUNS = "pitcher_earned_runs"
    PITCHER_OUTS = "pitcher_outs"

# ======================
# CONFIG AND SETTINGS
# ======================
@dataclass
class Config:
    API_KEY: str
    SPORTSBOOKS: List[str]
    MARKETS: List[str]
    TIMEZONE: pytz.timezone
    CACHE_DURATION: int = 300  # 5 minutes
    MAX_RETRIES: int = 3
    TIMEOUT: int = 10
    MIN_EDGE: float = 0.05
    MIN_ARB_EDGE: float = 0.02

    @classmethod
    def load(cls) -> 'Config':
        try:
            api_key = st.secrets["ODDS_API_KEY"]
        except Exception as e:
            logger.warning(f"Failed to load API key from secrets: {e}")
            api_key = "your_actual_api_key_here"

        return cls(
            API_KEY=api_key,
            SPORTSBOOKS=["fanduel", "draftkings", "betmgm", "pointsbet"],
            MARKETS=[market.value for market in MarketType],
            TIMEZONE=pytz.timezone('US/Eastern')
        )

# ======================
# DATA MODELS
# ======================
@dataclass
class PlayerStats:
    hits: float
    home_runs: float
    strikeouts: float
    rbis: float
    walks: float
    steals: float

@dataclass
class PlayerProjection:
    name: str
    team: str
    position: str
    stats: PlayerStats
    value_score: float
    last_10_trend: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerProjection':
        try:
            stats = PlayerStats(
                hits=(data['avg'] * data['ab']) + (data['bb'] * 0.25),
                home_runs=data['hr_rate'] * data['ab'],
                strikeouts=data['k_rate'] * data['ab'],
                rbis=data['rbi_rate'] * data['pa'],
                walks=data['bb_rate'] * data['pa'],
                steals=data['sb_rate'] * (data['hits'] + data['bb'])
            )
            
            value_score = (stats.hits * 0.3 + 
                          stats.home_runs * 0.4 +
                          stats.rbis * 0.3) * 1.2

            return cls(
                name=data['name'],
                team=data['team'],
                position=data['position'],
                stats=stats,
                value_score=value_score,
                last_10_trend=data.get('last_10_trend', 1.0)
            )
        except KeyError as e:
            logger.error(f"Missing required field in player data: {e}")
            raise ValueError(f"Invalid player data: missing {e}")

# ======================
# BETTING ANALYZER
# ======================
class BettingAnalyzer:
    def __init__(self, projections: List[PlayerProjection], config: Config):
        self.projections = projections
        self.config = config
        self.value_plays: List[Dict] = []
        self.arb_opportunities: List[Dict] = []
        self.steam_plays: List[Dict] = []
        self._cache: Dict = {}
        self._cache_timestamp = time.time()

    def _should_refresh_cache(self) -> bool:
        return time.time() - self._cache_timestamp > self.config.CACHE_DURATION

    def analyze_odds(self, odds_data: Dict[str, Any]) -> None:
        """
        Analyze odds data for value plays and arbitrage opportunities
        """
        try:
            if not odds_data or 'markets' not in odds_data:
                logger.warning("Invalid odds data format")
                return

            self.value_plays.clear()
            self.arb_opportunities.clear()
            self.steam_plays.clear()

            with ThreadPoolExecutor() as executor:
                # Analyze markets in parallel
                executor.map(self._evaluate_market, odds_data['markets'])
                executor.map(self._check_arbitrage, odds_data['markets'])

            self._identify_steam_moves()

        except Exception as e:
            logger.error(f"Error in analyze_odds: {e}")
            raise

    def _evaluate_market(self, market: Dict[str, Any]) -> None:
        """
        Evaluate a single market for value plays
        """
        try:
            player_proj = next((p for p in self.projections 
                              if p.name == market['player']), None)
            if not player_proj:
                return

            for book in market['books']:
                implied_prob = self._convert_odds(book['odds'])
                stat_proj = getattr(player_proj.stats, market['type'], 0) / 100

                if stat_proj > implied_prob + self.config.MIN_EDGE:
                    self.value_plays.append({
                        'player': market['player'],
                        'prop': market['type'],
                        'odds': book['odds'],
                        'edge': round(stat_proj - implied_prob, 3),
                        'book': book['bookmaker'],
                        'projection': round(stat_proj, 3),
                        'timestamp': datetime.now(self.config.TIMEZONE)
                    })

        except Exception as e:
            logger.error(f"Error evaluating market: {e}")

    # ... (continued in next part)
