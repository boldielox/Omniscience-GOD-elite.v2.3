# ask.py
import os
import streamlit as st

# --- Safe import of pyttsx3 for local TTS ---
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None  # TTS unavailable


def safe_init_tts():
    """
    Initialize the TTS engine unless running in a Streamlit environment or pyttsx3 is unavailable.
    """
    if st._is_running_with_streamlit:
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
    Streamlit UI function for the Omniscient App "Ask" tab.
    Optionally takes an analyzer and sport context.
    """
    st.title("🔮 Ask the Omniscient")
    st.markdown("Enter a sports-related question, prediction, or hypothesis.")

    user_question = st.text_input("Ask your question:")
    if st.button("Submit") and user_question:
        # Replace with actual model logic
        if analyzer:
            response = analyzer.answer(user_question, sport) if hasattr(analyzer, "answer") else f"Mocked: {user_question}"
        else:
            response = f"Answer to: {user_question}"

        st.success(response)
        speak(response)
