import os

# --- Safe import of pyttsx3 for local TTS ---
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None  # pyttsx3 not available in this environment


def safe_init_tts():
    """
    Initialize the TTS engine unless running on Streamlit Cloud
    or pyttsx3 is unavailable or broken.
    """
    if "STREAMLIT_SERVER_ENABLED" in os.environ:
        print("TTS disabled: Streamlit Cloud detected.")
        return None
    if pyttsx3 is None:
        print("TTS disabled: pyttsx3 is not installed.")
        return None
    try:
        return pyttsx3.init()
    except Exception as e:
        print(f"TTS initialization error: {e}")
        return None


# Initialize TTS engine if appropriate
engine = safe_init_tts()


def speak(text):
    """
    Speak the given text if TTS is available, otherwise print it.
    """
    if engine:
        engine.say(text)
        engine.runAndWait()
    else:
        print(f"[TTS Disabled] {text}")


# --- Omniscient UI Entry Point ---
import streamlit as st


def ask_omniscience_ui():
    """
    Streamlit UI function for the Omniscient App.
    Adjust logic as needed — this is a stub.
    """
    st.title("🔮 Ask the Omniscient")

    user_question = st.text_input("Ask your question:")

    if st.button("Submit") and user_question:
        # Here you could add logic to generate a response
        response = f"Answer to: {user_question}"
        st.write(response)

        # Optional: use TTS (only local)
        speak(response)
