import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = st.secrets["database"]["path"] if "database" in st.secrets else "omniscience.db"

def save_predictions(predictions):
    if not predictions:
        return
    conn = sqlite3.connect(DB_PATH)
    df = pd.DataFrame(predictions)
    df["timestamp"] = datetime.utcnow()
    df.to_sql("predictions", conn, if_exists="append", index=False)
    conn.close()

def save_outcome(player, prop, result):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO outcomes (player, prop, result, resolved_at)
        VALUES (?, ?, ?, ?)
    """, (player, prop, result, datetime.utcnow()))
    conn.commit()
    conn.close()

def prediction_dashboard():
    st.subheader("📈 Omniscience Daily Tracking")
    conn = sqlite3.connect(DB_PATH)
    preds = pd.read_sql("SELECT * FROM predictions ORDER BY timestamp DESC", conn)
    outcomes = pd.read_sql("SELECT * FROM outcomes ORDER BY resolved_at DESC", conn)
    conn.close()

    st.markdown("### 🔍 Recent Predictions")
    st.dataframe(preds.head(20))

    st.markdown("### ✅ Results")
    if not outcomes.empty:
        st.dataframe(outcomes.head(20))
        win_rate = outcomes["result"].str.lower().value_counts(normalize=True).get("win", 0.0) * 100
        st.success(f"🔮 Accuracy: {win_rate:.1f}%")
    else:
        st.info("No outcomes logged yet.")

def outcome_entry_form():
    st.subheader("📝 Record Outcome")
    with st.form("record_result"):
        player = st.text_input("Player")
        prop = st.text_input("Prop Type")
        result = st.selectbox("Outcome", ["win", "loss", "push"])
        submitted = st.form_submit_button("Submit")
        if submitted:
            save_outcome(player, prop, result)
            st.success("Outcome recorded.")
