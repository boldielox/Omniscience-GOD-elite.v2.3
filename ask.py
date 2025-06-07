# ask.py

import os
import streamlit as st

# --- Safe import of pyttsx3 for local TTS ---
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None  # pyttsx3 is not available


def is_streamlit_runtime():
    """
    Detect if running in a Streamlit runtime environment.
    """
    try:
        import streamlit.runtime
        return True
    except ImportError:
        return False


def safe_init_tts():
    """
    Initialize the TTS engine unless running in Streamlit or pyttsx3 is unavailable.
    """
    if is_streamlit_runtime():
        print("TTS disabled: Running in Streamlit environment.")
        return None
    if pyttsx3 is None:
        print("TTS disabled: pyttsx3 not installed.")
        return None
    try:
        return pyttsx3.init()
    except Exception as e:
        print(f"TTS initialization error: {e}")
        return None


# Initialize TTS engine
engine = safe_init_tts()


def speak(text):
    """
    Speak the given text if TTS is available; otherwise print it.
    """
    if engine:
        engine.say(text)
        engine.runAndWait()
    else:
        print(f"[TTS Disabled] {text}")


# --- Omniscient UI Entry Point ---
def ask_omniscience_ui(analyzer=None, sport=None):
    """
    Streamlit UI for the Omniscient 'Ask' tab.

    :param analyzer: Optional model or inference engine
    :param sport: Optional selected sport context
    """
    st.title("🔮 Ask the Omniscient")
    st.markdown("Enter a sports-related question, prediction, or hypothesis.")

    user_question = st.text_input("Ask your question:")

    if st.button("Submit") and user_question:
        if analyzer and hasattr(analyzer, "answer"):
            try:
                response = analyzer.answer(user_question, sport)
            except Exception as e:
                response = f"Error from analyzer: {e}"
        else:
            response = f"Answer to: {user_question}"

        st.success(response)
        speak(response)
