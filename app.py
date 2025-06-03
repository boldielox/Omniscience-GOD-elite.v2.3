import streamlit as st
import pandas as pd
import zipfile
import io

st.set_page_config(page_title="Bat Tracking Dashboard", layout="wide")
st.title("Bat Tracking Dashboard")

def load_csv(file_obj):
    try:
        return pd.read_csv(file_obj)
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        return None

def handle_zip(file_obj):
    dfs = {}
    try:
        with zipfile.ZipFile(file_obj) as z:
            for filename in z.namelist():
                if filename.endswith('.csv'):
                    with z.open(filename) as f:
                        df = load_csv(f)
                        if df is not None:
                            dfs[filename] = df
        if not dfs:
            st.warning("No CSV files found in ZIP.")
        return dfs
    except Exception as e:
        st.error(f"Failed to process ZIP file: {e}")
        return {}

uploaded_files = st.file_uploader(
    "Upload CSV or ZIP files",
    type=["csv", "zip"],
    accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.markdown(f"### File: `{uploaded_file.name}`")
        if uploaded_file.name.endswith(".csv"):
            df = load_csv(uploaded_file)
            if df is not None:
                st.success("CSV loaded successfully!")
                st.dataframe(df)
                st.write("**Quick Stats:**")
                st.write(df.describe())
        elif uploaded_file.name.endswith(".zip"):
            dfs = handle_zip(uploaded_file)
            for fname, df in dfs.items():
                st.markdown(f"#### CSV in ZIP: `{fname}`")
                st.dataframe(df)
                st.write("**Quick Stats:**")
                st.write(df.describe())
        else:
            st.warning("Unsupported file type.")

    # Example: Show chart for the first CSV uploaded
    first_df = None
    if uploaded_files[0].name.endswith(".csv"):
        first_df = load_csv(uploaded_files[0])
    elif uploaded_files[0].name.endswith(".zip"):
        dfs = handle_zip(uploaded_files[0])
        if dfs:
            first_df = list(dfs.values())[0]
    if first_df is not None and "avg_bat_speed" in first_df.columns and "name" in first_df.columns:
        st.header("Average Bat Speed per Player (First CSV)")
        first_df["avg_bat_speed"] = pd.to_numeric(first_df["avg_bat_speed"], errors="coerce")
        st.bar_chart(first_df.set_index("name")["avg_bat_speed"])
else:
    st.info("Please upload at least one CSV or ZIP file to view the dashboard.")
