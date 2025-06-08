import requests
import streamlit as st
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
BASE_URL = "https://www.balldontlie.io/api/v1"

@st.cache_data(ttl=300)
def fetch_nba_games(date: datetime):
    try:
        formatted_date = date.strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/games",
            params={"dates[]": formatted_date},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            logger.error(f"API Error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching games: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_player_stats(player_id=None, player_name=None):
    try:
        if player_name:
            search_response = requests.get(
                f"{BASE_URL}/players",
                params={"search": player_name}
            )
            players = search_response.json().get("data", [])
            if players:
                player_id = players[0]["id"]
            
        if player_id:
            response = requests.get(
                f"{BASE_URL}/stats",
                params={"player_ids[]": [player_id]}
            )
            return response.json().get("data", [])
        return []
    except Exception as e:
        logger.error(f"Error fetching player stats: {e}")
        return []
