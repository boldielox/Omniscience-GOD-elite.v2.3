import streamlit as st
import pandas as pd
import zipfile
from datetime import datetime

# --- Cosmic UI Enhancements ---
st.set_page_config(
    layout="wide",
    page_title="Omniscience GM Elite v2.4",
    page_icon="👁️"
)

# --- All-Seeing Eye Theme ---
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://pplx-res.cloudinary.com/image/upload/v1748978611/user_uploads/71937249/fb5461f1-3a0f-4d40-b7ae-b45da0418088/101.jpg');
        background-size: cover;
        background-attachment: fixed;
    }}
    .main {{
        background: rgba(10,10,20,0.9) !important;
        border-radius: 18px;
        padding: 2rem;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: #00ffe7 !important;
        text-shadow: 0 0 10px #0ff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    .st-b7 {{
        background-color: rgba(0,20,40,0.8) !important;
    }}
    .st-cb {{
        background-color: rgba(0,255,231,0.2) !important;
    }}
    .stSidebar {{
        background: rgba(5,5,15,0.95) !important;
        border-right: 1px solid #00ffe7;
        overflow-y: auto;
        max-height: 100vh;
    }}
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown(
    "<h1 style='text-align:center;'>Omniscience (GM) Elite v2.4</h1>"
    "<h3 style='text-align:center;color:#ff00c8;'>The All-Seeing Eye</h3>",
    unsafe_allow_html=True
)
st.markdown("---")

# --- Sidebar with Scrollable Controls ---
with st.sidebar:
    st.header("⚙️ Elite Controls")
    
    # Section selector with icons
    section = st.selectbox(
        "🔮 Analysis Section",
        ["📊 Overview", "🧑‍🤝‍🧑 Player Stats", "📈 Advanced Analytics"],
        key="section_select"
    )
    
    # Date range filter
    date_range = st.date_input(
        "🗓️ Date Range",
        value=[datetime(2025,1,1), datetime.today()],
        key="date_range"
    )
    
    # Toggle switches
    st.markdown("### 🔘 Display Toggles")
    show_raw = st.toggle("Show Raw Data", True, key="raw_toggle")
    show_charts = st.toggle("Interactive Charts", True, key="chart_toggle")
    
    # Multi-select filters
    st.markdown("### 🎚️ Data Filters")
    metric_filters = st.multiselect(
        "Select Metrics to Display",
        ["avg_bat_speed", "batter_run_value", "whiff_per_swing"],
        default=["avg_bat_speed"],
        key="metric_select"
    )

# --- File Upload with Enhanced UI ---
uploaded_files = st.file_uploader(
    "📤 Upload Data Files (CSV/ZIP)",
    type=["csv", "zip"],
    accept_multiple_files=True,
    help="Drag & drop files here",
    key="file_uploader"
)

# --- Main Content Tabs ---
tab1, tab2, tab3 = st.tabs(["📋 Data Explorer", "📊 Visual Analytics", "⚡ Live Insights"])

# --- Data Processing ---
all_dfs = []
all_players = set()

if uploaded_files:
    with st.spinner("🔮 Decrypting cosmic data patterns..."):
        for uploaded_file in uploaded_files:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    all_dfs.append(df)
                    if "name" in df.columns:
                        all_players.update(df["name"].unique())
                elif uploaded_file.name.endswith('.zip'):
                    with zipfile.ZipFile(uploaded_file) as z:
                        for file_name in z.namelist():
                            if file_name.endswith('.csv'):
                                with z.open(file_name) as f:
                                    df = pd.read_csv(f)
                                    all_dfs.append(df)
                                    if "name" in df.columns:
                                        all_players.update(df["name"].unique())
            except Exception as e:
                st.error(f"⚠️ Error processing {uploaded_file.name}: {str(e)}")

# --- Tab 1: Data Explorer ---
with tab1:
    if uploaded_files:
        # Player selector with search
        player_choice = st.selectbox(
            "🧑‍🤝‍🧑 Select Player",
            ["All Players"] + sorted(list(all_players)),
            key="player_select"
        )
        
        # Team selector (if team column exists)
        if all_dfs and any("team" in df.columns for df in all_dfs):
            all_teams = set()
            for df in all_dfs:
                if "team" in df.columns:
                    all_teams.update(df["team"].unique())
            team_choice = st.multiselect(
                "🏟️ Filter by Team",
                sorted(list(all_teams)),
                key="team_select"
            )
        
        # Display filtered data
        for idx, df in enumerate(all_dfs):
            with st.expander(f"📄 {uploaded_files[idx].name}", expanded=True):
                if player_choice != "All Players" and "name" in df.columns:
                    df = df[df["name"] == player_choice]
                if "team" in df.columns and team_choice:
                    df = df[df["team"].isin(team_choice)]
                
                if show_raw:
                    st.dataframe(
                        df[metric_filters] if metric_filters else df,
                        use_container_width=True,
                        height=300
                    )
    else:
        st.info("🌌 Upload data files to begin analysis")

# --- Tab 2: Visual Analytics ---
with tab2:
    if uploaded_files and show_charts:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔥 Bat Speed Distribution")
            if "avg_bat_speed" in df.columns:
                st.vega_lite_chart(df, {
                    "mark": {"type": "bar", "color": "#00ffe7"},
                    "encoding": {
                        "x": {"field": "name", "type": "nominal", "sort": "-y"},
                        "y": {"field": "avg_bat_speed", "type": "quantitative"}
                    }
                })
        
        with col2:
            st.markdown("### 🎯 Performance Matrix")
            if {"batter_run_value", "whiff_per_swing"}.issubset(df.columns):
                st.scatter_chart(
                    df,
                    x="batter_run_value",
                    y="whiff_per_swing",
                    color="#ff00c8",
                    size="avg_bat_speed"
                )
    else:
        st.warning("Enable 'Interactive Charts' toggle to visualize data")

# --- Tab 3: Live Insights ---
with tab3:
    if uploaded_files:
        # Real-time alerts system
        if "cashout_signal" in df.columns:
            alert_players = df[df["cashout_signal"]]["name"].unique()
            if len(alert_players) > 0:
                st.error(f"🚨 CASHOUT ALERT for: {', '.join(alert_players)}")
        
        # Dynamic metrics dashboard
        metrics = st.columns(3)
        with metrics[0]:
            st.metric("Top Bat Speed", f"{df['avg_bat_speed'].max():.1f} mph")
        with metrics[1]:
            st.metric("Elite Performers", len(df[df["batter_run_value"] > 0]))
        with metrics[2]:
            st.metric("Avg Whiff Rate", f"{df['whiff_per_swing'].mean():.1%}")
    else:
        st.info("Upload data to unlock live insights")

# --- Footer ---
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#888;'>Omniscience GM Elite v2.4 &copy; 2025 | "
    "<span style='color:#00ffe7;'>The All-Seeing Eye Never Sleeps</span></p>",
    unsafe_allow_html=True
)
