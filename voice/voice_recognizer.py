# voice/voice_recognizer.py

import speech_recognition as sr

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening... Please speak your command.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)

    try:
        print("🧠 Processing...")
        text = recognizer.recognize_google(audio)
        print(f"✅ You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("❌ Sorry, I couldn’t understand that.")
        return None
    except sr.RequestError:
        print("⚠️ Speech Recognition API unavailable.")
        return None
