import streamlit as st
import base64

def set_background(image_file_path: str):
    with open(image_file_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    st.markdown(f"""
    <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-attachment: fixed;
        }}
    </style>
    """, unsafe_allow_html=True)

def render_matchup_card(game: dict):
    st.markdown(f"""
        <div style='background-color:#1e1e1e;padding:10px;margin-bottom:10px;border-radius:8px'>
            <h4 style='color:gold'>{game['away_team']} @ {game['home_team']}</h4>
            <p style='color:white'>Start: {game['commence_time']}</p>
        </div>
    """, unsafe_allow_html=True)
