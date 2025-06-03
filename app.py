import streamlit as st
import pandas as pd
import zipfile

# --- Custom CSS for your All Seeing Eye background ---
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
menu = st.sidebar.selectbox(
    "Choose Analysis Section",
    ["Overview", "Player Stats", "Advanced Analytics"]
)

# Example: Dropdown for player selection (will populate after file upload)
selected_player = st.sidebar.selectbox("Select Player (after upload)", ["No data loaded"])

# --- File uploader ---
uploaded_files = st.file_uploader(
    "Upload your CSV or ZIP files",
    type=["csv", "zip"],
    accept_multiple_files=True,
    help="Elite data only! ZIPs can contain multiple CSVs."
)

# --- Helper functions ---
def display_omniscience_analytics(df):
    # Tabs for different analytics
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

def load_and_display_csv(file_obj, file_name):
    try:
        df = pd.read_csv(file_obj)
        st.success(f"Loaded: {file_name}")
        st.dataframe(df, use_container_width=True)
        # Update player dropdown in sidebar
        if "name" in df.columns:
            st.session_state['players'] = sorted(df["name"].unique())
        display_omniscience_analytics(df)
        return df
    except Exception as e:
        st.error(f"Could not read {file_name}: {e}")
        return None

def handle_zip(uploaded_file):
    dfs = []
    try:
        with zipfile.ZipFile(uploaded_file) as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if not csv_files:
                st.warning("No CSV files found in ZIP.")
            for file_name in csv_files:
                with z.open(file_name) as f:
                    df = load_and_display_csv(f, file_name)
                    if df is not None:
                        dfs.append(df)
    except Exception as e:
        st.error(f"Could not process ZIP file: {e}")
    return dfs

# --- Main logic ---
all_dfs = []
if uploaded_files:
    st.session_state['players'] = []
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith('.csv'):
            df = load_and_display_csv(uploaded_file, uploaded_file.name)
            if df is not None:
                all_dfs.append(df)
        elif uploaded_file.name.endswith('.zip'):
            dfs = handle_zip(uploaded_file)
            all_dfs.extend(dfs)
        else:
            st.warning(f"Unsupported file type: {uploaded_file.name}")
    # Update player dropdown after loading files
    if all_dfs and 'players' in st.session_state and st.session_state['players']:
        selected_player = st.sidebar.selectbox("Select Player", st.session_state['players'])
        # Show stats for selected player in a tab
        if selected_player != "No data loaded":
            st.markdown("---")
            st.subheader(f"Stats for {selected_player}")
            for df in all_dfs:
                if "name" in df.columns and selected_player in df["name"].values:
                    st.dataframe(df[df["name"] == selected_player])
else:
    st.info("Please upload at least one CSV or ZIP file to view the dashboard.")

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#888;'>Omniscience GM Elite v2.3 &copy; 2025</p>",
    unsafe_allow_html=True
)
