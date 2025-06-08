import requests
from typing import Dict, List, Optional
import streamlit as st
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

BASE_URL = "https://www.balldontlie.io/api/v1"

@st.cache_data(ttl=300)
def fetch_nba_games(date: datetime) -> Optional[List[Dict]]:
    """Fetch NBA games from balldontlie API"""
    try:
        formatted_date = date.strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/games",
            params={"dates[]": formatted_date},
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"API Error: {response.status_code}")
            return None
            
        return response.json().get("data")
        
    except Exception as e:
        logger.error(f"Error fetching games: {str(e)}")
        return None

@st.cache_data(ttl=300)
def fetch_player_stats(player_id: Optional[int] = None, 
                      player_name: Optional[str] = None) -> List[Dict]:
    """Fetch player statistics"""
    try:
        if player_name and not player_id:
            # Search for player first
            search_response = requests.get(
                f"{BASE_URL}/players",
                params={"search": player_name}
            )
            players = search_response.json().get("data", [])
            if not players:
                return []
            player_id = players[0]["id"]
        
        if player_id:
            response = requests.get(
                f"{BASE_URL}/stats",
                params={"player_ids[]": [player_id]}
            )
            return response.json().get("data", [])
            
        return []
        
    except Exception as e:
        logger.error(f"Error fetching player stats: {str(e)}")
        return []
