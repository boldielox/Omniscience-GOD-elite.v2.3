import requests
from typing import Dict, List, Optional, Union
import pandas as pd

class SportsGameOddsClient:
    """
    Comprehensive client for SportsGameOdds API covering all market types:
    - Player props (runs, points, rebounds, assists)
    - Team totals (over/under)
    - Moneyline
    - Point spreads
    """
    
    BASE_URL = "https://api.sportsgameodds.com/v1/"
    SUPPORTED_LEAGUES = {
        'baseball': ['MLB', 'NPB', 'KBO', 'CPBL', 'LIDOM', 'LMP', 'LVBP', 'MLB_MINORS'],
        'basketball': ['NBA', 'WNBA', 'NCAAB'],
        'football': ['NFL', 'CFL', 'NCAAF', 'USFL', 'XFL']
    }

    def __init__(self, api_key: str):
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": api_key,
            "Content-Type": "application/json"
        })

    def get_player_props(
        self,
        league: str,
        stat_type: str,
        player_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get player prop odds (over/under)
        
        Args:
            league: e.g. MLB, NBA, NFL
            stat_type: 'points', 'runs', 'rebounds', 'assists', etc.
            player_id: Specific player ID or None for all players
            
        Returns:
            List of player prop odds with bookmakers
        """
        endpoint = f"markets/{league.lower()}/player/{stat_type}"
        params = {
            "betTypeID": "ou",
            "periodID": "game",
            "statID": stat_type,
            "statEntityID": player_id if player_id else "all"
        }
        
        try:
            response = self.session.get(
                self.BASE_URL + endpoint,
                params=params
            )
            response.raise_for_status()
            return response.json()['markets']
        except Exception as e:
            print(f"Error fetching player props: {e}")
            return []

    def get_team_totals(
        self,
        league: str,
        game_id: str,
        side: Optional[str] = None
    ) -> List[Dict]:
        """
        Get team total odds (over/under)
        
        Args:
            league: e.g. MLB, NBA
            game_id: ID of the specific game
            side: 'home', 'away', or None for both
            
        Returns:
            List of team total odds
        """
        endpoint = f"markets/{league.lower()}/game/{game_id}/totals"
        params = {
            "betTypeID": "ou",
            "periodID": "game",
            "statID": "points",
            "statEntityIDs": "home,away" if not side else side
        }
        
        try:
            response = self.session.get(
                self.BASE_URL + endpoint,
                params=params
            )
            response.raise_for_status()
            return response.json()['markets']
        except Exception as e:
            print(f"Error fetching team totals: {e}")
            return []

    def get_moneyline(
        self,
        league: str,
        game_id: str
    ) -> List[Dict]:
        """
        Get moneyline odds for a game
        
        Args:
            league: e.g. MLB, NBA
            game_id: ID of the specific game
            
        Returns:
            Moneyline odds for home and away teams
        """
        endpoint = f"markets/{league.lower()}/game/{game_id}/moneyline"
        params = {
            "betTypeID": "ml",
            "periodID": "game",
            "statID": "points",
            "statEntityIDs": "home,away"
        }
        
        try:
            response = self.session.get(
                self.BASE_URL + endpoint,
                params=params
            )
            response.raise_for_status()
            return response.json()['markets']
        except Exception as e:
            print(f"Error fetching moneyline: {e}")
            return []

    def get_spreads(
        self,
        league: str,
        game_id: str
    ) -> List[Dict]:
        """
        Get point spread odds for a game
        
        Args:
            league: e.g. NBA, NFL
            game_id: ID of the specific game
            
        Returns:
            Point spread odds for home and away teams
        """
        endpoint = f"markets/{league.lower()}/game/{game_id}/spread"
        params = {
            "betTypeID": "sp",
            "periodID": "game",
            "statID": "points",
            "statEntityIDs": "home,away"
        }
        
        try:
            response = self.session.get(
                self.BASE_URL + endpoint,
                params=params
            )
            response.raise_for_status()
            return response.json()['markets']
        except Exception as e:
            print(f"Error fetching spreads: {e}")
            return []

    def get_all_game_markets(
        self,
        league: str,
        game_id: str
    ) -> Dict[str, List[Dict]]:
        """
        Get all market types for a specific game
        
        Args:
            league: e.g. MLB, NBA
            game_id: ID of the specific game
            
        Returns:
            Dictionary containing all market types
        """
        return {
            "moneyline": self.get_moneyline(league, game_id),
            "spreads": self.get_spreads(league, game_id),
            "team_totals": self.get_team_totals(league, game_id),
            "player_props": self.get_player_props(league, "points")  # Default to points
        }

# Example Usage
if __name__ == "__main__":
    API_KEY = "your_api_key_here"
    client = SportsGameOddsClient(API_KEY)
    
    # Get MLB player run props
    mlb_run_props = client.get_player_props("MLB", "runs")
    print(f"Found {len(mlb_run_props)} MLB run props")
    
    # Get NBA game markets
    nba_game_markets = client.get_all_game_markets("NBA", "12345")
    print(f"NBA Game Markets: {nba_game_markets.keys()}")
