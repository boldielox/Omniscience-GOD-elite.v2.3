import pandas as pd
import sqlite3
from datetime import datetime

DB_PATH = "omniscience.db"

def evaluate_uploaded_results(uploaded_file):
    if uploaded_file is None:
        return None, "No file uploaded"

    df = pd.read_csv(uploaded_file)
    required = {"player", "prop", "result"}
    if not required.issubset(df.columns):
        return None, "CSV must contain: player, prop, result"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO outcomes (player, prop, result, resolved_at)
            VALUES (?, ?, ?, ?)
        """, (row['player'], row['prop'], row['result'].lower(), datetime.utcnow()))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted, f"Recorded {inserted} results"

def summarize_accuracy():
    conn = sqlite3.connect(DB_PATH)
    preds = pd.read_sql("SELECT * FROM predictions", conn)
    outcomes = pd.read_sql("SELECT * FROM outcomes", conn)
    conn.close()

    merged = pd.merge(preds, outcomes, on=["player", "prop"], how="inner")
    merged["correct"] = merged["result"].str.lower() == "win"
    accuracy = merged["correct"].mean()
    return merged, accuracy
