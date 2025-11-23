# voice/voice_nlp_tester.py
import csv
import datetime as dt
import os
import sys
from pathlib import Path

import speech_recognition as sr
from nlp.nlp_processor import parse_command

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "voice_nlp_tests.csv"

def print_banner():
    print("\n" + "="*80)
    print("🎙️  ACADEXA Voice → NLP Tester (say 'quit' to exit)")
    print("="*80)

def write_header_if_needed():
    new = not LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "recognized_text", "intent", "slots", "error"])

def append_log(text, intent, slots, error):
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([dt.datetime.now().isoformat(timespec="seconds"), text, intent, slots, error])

def listen_once(recognizer: sr.Recognizer, mic: sr.Microphone, timeout=5, phrase_time_limit=6):
    print("\n🎤 Listening... (speak now)")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            print("⌛ No speech detected (timeout).")
            return None, "timeout"
    print("🧠 Processing speech → text...")
    try:
        text = recognizer.recognize_google(audio)
        print(f"✅ You said: {text}")
        return text, None
    except sr.UnknownValueError:
        print("❌ Couldn't understand audio.")
        return None, "unrecognized"
    except sr.RequestError as e:
        print(f"⚠️ Speech service error: {e}")
        return None, f"request_error:{e}"

def main():
    # prepare
    print_banner()
    write_header_if_needed()

    recog = sr.Recognizer()
    try:
        mic = sr.Microphone()
    except OSError as e:
        print("❌ No microphone found or access denied.")
        print("Tip: check recording devices, drivers, and app permissions.")
        sys.exit(1)

    while True:
        text, err = listen_once(recog, mic)
        if text:
            lower = text.strip().lower()
            if lower in {"quit", "exit", "stop"}:
                print("👋 Bye!")
                break

            parsed = parse_command(text)
            print("🔎 NLP Result:", parsed.model_dump())

            append_log(text, parsed.intent, parsed.slots, None)
        else:
            append_log("", "unknown", {}, err)

        print("— say another command, or say 'quit' to stop —")

if __name__ == "__main__":
    main()
