import streamlit as st
import pandas as pd
import zipfile

# --- All Seeing Eye background CSS ---
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://pplx-res.cloudinary.com/image/upload/v1748978611/user_uploads/71937249/fb5461f1-3a0f-4d40-b7ae-b45da0418088/101.jpg');
        background-size: cover;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    .main {{
        background: rgba(10,10,20,0.85);
        border-radius: 18px;
        padding: 2rem;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: #00ffe7 !important;
        text-shadow: 0 0 10px #0ff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    .css-1d391kg, .css-10trblm, .css-1v0mbdj {{
        color: #e0e0e0 !important;
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;'>Omniscience (GM) Elite v2.3</h1>"
    "<h3 style='text-align:center;color:#ff00c8;'>The All Seeing Eye</h3>",
    unsafe_allow_html=True
)
st.markdown("---")

# --- Sidebar with dropdowns ---
st.sidebar.header("Elite Controls")
section = st.sidebar.selectbox(
    "Choose Analysis Section",
    ["Overview", "Player Stats", "Advanced Analytics"]
)

# --- File uploader ---
uploaded_files = st.file_uploader(
    "Upload your CSV or ZIP files",
    type=["csv", "zip"],
    accept_multiple_files=True,
    help="Elite data only! ZIPs can contain multiple CSVs."
)

# --- Helper functions ---
def display_omniscience_analytics(df):
    tab1, tab2, tab3 = st.tabs(["Quick Stats", "Unique Players", "Bat Speed Chart"])
    with tab1:
        st.write("**Quick Stats:**")
        st.write(df.describe())
    with tab2:
        if "name" in df.columns:
            st.write("**Unique Player Names:**")
            st.write(df["name"].unique())
    with tab3:
        if "avg_bat_speed" in df.columns and "name" in df.columns:
            st.write("**Average Bat Speed per Player:**")
            df["avg_bat_speed"] = pd.to_numeric(df["avg_bat_speed"], errors="coerce")
            st.bar_chart(df.groupby("name")["avg_bat_speed"].mean())

def load_and_display_csv(file_obj, file_name, player_filter=None):
    try:
        df = pd.read_csv(file_obj)
        st.success(f"Loaded: {file_name}")
        if player_filter and "name" in df.columns:
            df = df[df["name"] == player_filter]
            st.info(f"Filtered for player: {player_filter}")
        st.dataframe(df, use_container_width=True)
        display_omniscience_analytics(df)
        return df
    except Exception as e:
        st.error(f"Could not read {file_name}: {e}")
        return None

def handle_zip(uploaded_file, player_filter=None):
    dfs = []
    try:
        with zipfile.ZipFile(uploaded_file) as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if not csv_files:
                st.warning("No CSV files found in ZIP.")
            for file_name in csv_files:
                with z.open(file_name) as f:
                    df = load_and_display_csv(f, file_name, player_filter)
                    if df is not None:
                        dfs.append(df)
    except Exception as e:
        st.error(f"Could not process ZIP file: {e}")
    return dfs

# --- Main logic ---
all_dfs = []
all_players = set()
if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            all_dfs.append(df)
            if "name" in df.columns:
                all_players.update(df["name"].unique())
        elif uploaded_file.name.endswith('.zip'):
            try:
                with zipfile.ZipFile(uploaded_file) as z:
                    csv_files = [f for f in z.namelist() if f.endswith('.csv')]
                    for file_name in csv_files:
                        with z.open(file_name) as f:
                            df = pd.read_csv(f)
                            all_dfs.append(df)
                            if "name" in df.columns:
                                all_players.update(df["name"].unique())
            except Exception as e:
                st.error(f"Could not process ZIP file: {e}")
        else:
            st.warning(f"Unsupported file type: {uploaded_file.name}")

    # Player dropdown after data is loaded
    player_list = sorted(list(all_players)) if all_players else ["All"]
    player_choice = st.sidebar.selectbox("Select Player", ["All"] + player_list)

    # Tabs and analytics
    for idx, df in enumerate(all_dfs):
        st.markdown(f"### Data File {idx+1}")
        if player_choice != "All" and "name" in df.columns:
            df = df[df["name"] == player_choice]
            st.info(f"Filtered for player: {player_choice}")
        display_omniscience_analytics(df)
else:
    st.info("Please upload at least one CSV or ZIP file to view and interact with the dashboard.")

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#888;'>Omniscience GM Elite v2.3 &copy; 2025</p>",
    unsafe_allow_html=True
)
