import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Omniscience God Mode Elite", layout="wide")
st.title("Omniscience God Mode Elite Dashboard")

FLASK_URL = "http://localhost:5000"  # Change if deploying Flask elsewhere

# Upload files
st.header("Upload CSV or ZIP files")
uploaded_files = st.file_uploader("Choose CSV or ZIP files", accept_multiple_files=True)

if uploaded_files and st.button("Upload and Process"):
    files = []
    for file in uploaded_files:
        files.append(("files", (file.name, file, file.type)))
    with st.spinner("Uploading and processing..."):
        try:
            response = requests.post(f"{FLASK_URL}/upload_stats", files=files)
            if response.status_code == 200:
                data = response.json()
                st.success("Files uploaded and processed successfully!")
                if data.get("alerts"):
                    st.warning("Alerts:")
                    for alert in data["alerts"]:
                        st.write(f"- {alert}")
                if data.get("results"):
                    st.write("Processed Results:")
                    st.dataframe(pd.DataFrame(data["results"]))
            else:
                st.error(f"Upload failed: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Could not connect to backend: {e}")

st.header("Latest Analytics")
if st.button("Refresh Data"):
    pass  # Just re-runs the script

try:
    stats_response = requests.get(f"{FLASK_URL}/api/omniscience_stats")
    if stats_response.status_code == 200:
        stats_data = stats_response.json()
        if stats_data:
            st.dataframe(pd.DataFrame(stats_data))
        else:
            st.info("No analytics data available yet.")
    else:
        st.error(f"Failed to fetch stats: {stats_response.status_code}")
except Exception as e:
    st.error(f"Could not connect to backend: {e}")
