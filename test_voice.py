# test_voice.py
from voice.voice_recognizer import recognize_speech

if __name__ == "__main__":
    command = recognize_speech()
    if command:
        print(f"🎯 Recognized Command: {command}")
