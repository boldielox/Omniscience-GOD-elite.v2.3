import streamlit as st
import re
from utils.models import BettingAnalyzer
import pandas as pd
import pyttsx3

# Initialize text-to-speech
engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('volume', 1.0)

def format_response(message, mode="oracle"):
    if mode == "oracle":
        return f"🧙 OMNISCIENT PROPHECY:\n'{message}'"
    elif mode == "analyst":
        return f"📊 ANALYST INSIGHT:\n{message}"
    return message

def interpret_query(query, analyzer: BettingAnalyzer, sport: str):
    query = query.lower()
    results = []

    if "value play" in query or "edge" in query:
        for vp in analyzer.value_plays:
            if sport in vp.get('prop', ''):
                results.append(vp)
        if not results:
            return "No clear edges detected at this moment."
        return f"Top divine edges: {', '.join(f'{r['player']} ({r['prop']}) +{int(r['edge']*100)}%' for r in results[:3])}"

    if "arbitrage" in query:
        if analyzer.arb_opportunities:
            best = analyzer.arb_opportunities[0]
            return f"Arbitrage found between {best['book1']} and {best['book2']} on {best['player']} ({best['prop']}) for {best['profit']}% return."
        else:
            return "Markets are in balance. No arbitrage today."

    if "who" in query and "recommend" in query:
        if analyzer.value_plays:
            return f"I recommend {analyzer.value_plays[0]['player']} on {analyzer.value_plays[0]['book']} ({analyzer.value_plays[0]['prop']}) with edge of {analyzer.value_plays[0]['edge']*100:.1f}%."
        else:
            return "No player stands out currently."

    return "I cannot divine that meaning. Ask me about props, edges, or matchups."

def ask_omniscience_ui(analyzer: BettingAnalyzer, sport: str):
    st.subheader("💬 Ask Omniscience")
    tone = st.radio("Voice Style", ["oracle", "analyst"], horizontal=True)
    query = st.text_input("Ask a question about today's matchups:", placeholder="e.g. Any good prop bets in MLB today?")

    if query:
        reply = interpret_query(query, analyzer, sport)
        st.write(format_response(reply, tone))

        if st.toggle("🔊 Speak it aloud"):
            engine.say(reply)
            engine.runAndWait()
