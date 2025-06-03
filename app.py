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

uploaded_files = st.file_uploader(
    "Upload your CSV or ZIP files",
    type=["csv", "zip"],
    accept_multiple_files=True,
    help="Elite data only! ZIPs can contain multiple CSVs."
)

def display_omniscience_analytics(df):
    st.subheader("Omniscience (GM) v2.3: Core Analytics")
    # Quick Stats
    st.write("**Quick Stats:**")
    st.write(df.describe())
    # Unique Player Names (if column exists)
    if "name" in df.columns:
        st.write("**Unique Player Names:**")
        st.write(df["name"].unique())
    # Average Bat Speed per Player (if columns exist)
    if "avg_bat_speed" in df.columns and "name" in df.columns:
        st.write("**Average Bat Speed per Player:**")
        df["avg_bat_speed"] = pd.to_numeric(df["avg_bat_speed"], errors="coerce")
        st.bar_chart(df.groupby("name")["avg_bat_speed"].mean())
    # Add more analytics as needed here!

def load_and_display_csv(file_obj, file_name):
    try:
        df = pd.read_csv(file_obj)
        st.success(f"Loaded: {file_name}")
        st.dataframe(df, use_container_width=True)
        display_omniscience_analytics(df)
    except Exception as e:
        st.error(f"Could not read {file_name}: {e}")

def handle_zip(uploaded_file):
    try:
        with zipfile.ZipFile(uploaded_file) as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if not csv_files:
                st.warning("No CSV files found in ZIP.")
            for file_name in csv_files:
                with z.open(file_name) as f:
                    load_and_display_csv(f, file_name)
    except Exception as e:
        st.error(f"Could not process ZIP file: {e}")

if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith('.csv'):
            load_and_display_csv(uploaded_file, uploaded_file.name)
        elif uploaded_file.name.endswith('.zip'):
            handle_zip(uploaded_file)
        else:
            st.warning(f"Unsupported file type: {uploaded_file.name}")
else:
    st.info("Please upload at least one CSV or ZIP file to view the dashboard.")

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#888;'>Omniscience GM Elite v2.3 &copy; 2025</p>",
    unsafe_allow_html=True
)
