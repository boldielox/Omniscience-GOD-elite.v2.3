import streamlit as st

def render_matchup_card(game):
    col1, col2, col3 = st.columns([2,1,2])
    
    with col1:
        st.write(f"**{game['home_team']['full_name']}**")
    with col2:
        st.write("VS")
    with col3:
        st.write(f"**{game['visitor_team']['full_name']}**")
