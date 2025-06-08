import pandas as pd
import sqlite3
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self):
        self.db_path = 'data/nba_history.db'
        self._init_db()

    def _init_db(self):
        try:
            os.makedirs('data', exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Create tables
            c.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    game_id TEXT PRIMARY KEY,
                    date TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    home_score INTEGER,
                    away_score INTEGER
                )
            ''')
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    game_id TEXT PRIMARY KEY,
                    predicted_home_score REAL,
                    predicted_away_score REAL,
                    actual_home_score INTEGER,
                    actual_away_score INTEGER,
                    timestamp TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def save_game(self, game_data):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO games 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                game_data['id'],
                game_data['date'],
                game_data['home_team'],
                game_data['away_team'],
                game_data['home_score'],
                game_data['away_score']
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving game: {e}")

    def get_team_history(self, team_name, limit=10):
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT * FROM games 
                WHERE home_team = ? OR away_team = ?
                ORDER BY date DESC
                LIMIT ?
            '''
            df = pd.read_sql_query(query, conn, params=(team_name, team_name, limit))
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error getting team history: {e}")
            return pd.DataFrame()
