import requests
import time

def fetch_odds_data(sport: str, market: str, api_key: str):
    url = f"https://api.sportsgameodds.com/v2/odds?sport={sport}&market={market}&region=us&oddsFormat=american"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return parse_odds_response(response.json())
    except Exception as e:
        print(f"Error fetching odds: {e}")
        return []

def parse_odds_response(data):
    games = []
    for event in data.get("data", []):
        games.append({
            "id": event.get("id"),
            "home_team": event.get("home_team"),
            "away_team": event.get("away_team"),
            "commence_time": event.get("commence_time"),
            "markets": event.get("bookmakers", [])
        })
    return games

def fetch_player_stats(game, api_key):
    players = []
    for team in [game.get("home_team"), game.get("away_team")]:
        url = f"https://api.sportsgameodds.com/v2/players?sport={game.get('sport')}&team={team}"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            players += response.json().get("data", [])
            time.sleep(0.25)
        except Exception as e:
            print(f"Error fetching player stats for {team}: {e}")
    return players
