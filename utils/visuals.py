import streamlit as st
import plotly.graph_objects as go
from typing import Dict

def render_matchup_card(game: Dict):
    """Render a game matchup card"""
    col1, col2, col3 = st.columns([2,1,2])
    
    with col1:
        st.write(f"**{game['home_team']['full_name']}**")
    
    with col2:
        st.write("VS")
        
    with col3:
        st.write(f"**{game['visitor_team']['full_name']}**")

def create_trend_chart(data, title="Performance Trend"):
    """Create a trend chart using plotly"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data.values,
        mode='lines+markers'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Games",
        yaxis_title="Points",
        showlegend=False
    )
    
    return fig
