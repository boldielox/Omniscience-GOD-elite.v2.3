import streamlit as st
import pandas as pd
import zipfile
import io

# --- Custom CSS for the All Seeing Eye backdrop and premium styling ---
st.markdown("""
    <style>
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?fit=crop&w=1200&q=80'); /* Replace with your All Seeing Eye image URL if needed */
        background-size: cover;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }
    .main {
        background: rgba(10,10,20,0.85);
        border-radius: 18px;
        padding: 2rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #00ffe7 !important;
        text-shadow: 0 0 10px #0ff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
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

def load_and_display_csv(file_obj, file_name):
    try:
        df = pd.read_csv(file_obj)
        st.success(f"Loaded: {file_name}")
        st.dataframe(df, use_container_width=True)
        st.write("**Quick Stats:**")
        st.write(df.describe())
        # Example: Custom analytics
        if "avg_bat_speed" in df.columns and "name" in df.columns:
            st.header("Average Bat Speed per Player")
            df["avg_bat_speed"] = pd.to_numeric(df["avg_bat_speed"], errors="coerce")
            st.bar_chart(df.set_index("name")["avg_bat_speed"])
        # Add your custom Omniscience analytics here!
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
