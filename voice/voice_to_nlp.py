# voice/voice_to_nlp.py
from voice.voice_recognizer import recognize_speech
from nlp.nlp_processor import parse_command

if __name__ == "__main__":
    text = recognize_speech()
    if not text:
        print("No command recognized.")
    else:
        parsed = parse_command(text)
        print("NLP:", parsed.model_dump())
