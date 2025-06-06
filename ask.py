import os

# Attempt to import pyttsx3 safely
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None  # Not available in this environment


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


# Initialize the TTS engine only when appropriate
engine = safe_init_tts()


def speak(text):
    """
    Speak the given text if TTS is available.
    Fallback to printing the message in unsupported environments.
    """
    if engine:
        engine.say(text)
        engine.runAndWait()
    else:
        print(f"[TTS Disabled] {text}")


# EXAMPLE USAGE — OPTIONAL
if __name__ == "__main__":
    speak("Welcome to the Omniscient App!")
