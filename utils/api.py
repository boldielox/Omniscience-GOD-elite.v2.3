import requests
from typing import Dict, List, Optional
import streamlit as st
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

BASE_URL = "https://www.balldontlie.io/api/v1"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_nba_games(date: datetime) -> Optional[List[Dict]]:
    """Fetch NBA games from balldontlie API"""
    try:
        response = requests.get(
            f"{BASE_URL}/games",
            params={
                "start_date": date.strftime("%Y-%m-%d"),
                "end_date": date.strftime("%Y-%m-%d")
            },
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        if not data.get("data"):
            logger.warning("No games available")
            return None
            
        return data["data"]
        
    except requests.Timeout:
        logger.error("API request timed out")
        return None
    except requests.RequestException as e:
        logger.error(f"Network error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in fetch_nba_games: {str(e)}")
        return None

@st.cache_data(ttl=300)
def fetch_player_stats(player_id: Optional[int] = None, player_name: Optional[str] = None) -> List[Dict]:
    """Fetch player statistics from balldontlie API"""
    try:
        # If searching by name, first get player ID
        if player_name and not player_id:
            search_response = requests.get(
                f"{BASE_URL}/players",
                params={"search": player_name},
                timeout=10
            )
            if search_response.status_code != 200:
                logger.error(f"Player search API Error: {search_response.status_code}")
                return []
                
            players = search_response.json().get("data", [])
            if not players:
                return []
            player_id = players[0]["id"]
        
        # Fetch player stats
        if player_id:
            response = requests.get(
                f"{BASE_URL}/stats",
                params={
                    "player_ids[]": player_id,
                    "per_page": 100
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Stats API Error: {response.status_code}")
                return []
                
            data = response.json()
            return data.get("data", [])
            
        return []
        
    except requests.Timeout:
        logger.error("Player stats API request timed out")
        return []
    except requests.RequestException as e:
        logger.error(f"Network error fetching player stats: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in fetch_player_stats: {str(e)}")
        return []
