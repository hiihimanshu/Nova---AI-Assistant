import speech_recognition as sr
import time
import threading

from app.config import ASSISTANT_NAME, WAKE_WORD
from app.core.speaker import speak
from app.core.commands import process_command


def looks_like_question(text: str) -> bool:
    return text.startswith((
        "who", "what", "when", "where",
        "why", "how", "tell me", "explain"
    ))


def start_background_listening(recognizer: sr.Recognizer):
    stop_listening = None

    def callback(recognizer, audio):
        try:
            text = recognizer.recognize_google(audio).lower()
            print("You (voice):", text)

            if text in ["stop", "exit", "goodbye"]:
                speak("Stopping voice input.")
                if stop_listening:
                    stop_listening(wait_for_stop=False)
                return

            process_command(text)

        except sr.UnknownValueError:
            pass
        except Exception as e:
            print("Voice error:", e)

    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.2)

    stop_listening = recognizer.listen_in_background(mic, callback)
    return stop_listening


def text_input_loop():
    while True:
        try:
            text = input("You (text): ").strip()
            if not text:
                continue

            if text.lower() in ["exit", "quit"]:
                speak("Goodbye.")
                break

            process_command(text)

        except KeyboardInterrupt:
            break


def main():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.6
    recognizer.phrase_time_limit = 4

    print("\n" + "━" * 40)
    print(f"🤖 {ASSISTANT_NAME.upper()} IS READY")
    print("• Say the wake word to speak")
    print("• Type anytime")
    print("• Say 'stop' to stop voice")
    print("• Type 'exit' to quit")
    print("━" * 40 + "\n")

    speak("NOVA is ready.")


    # Start text input thread
    threading.Thread(target=text_input_loop, daemon=True).start()

    # Wake-word loop
    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                #print(f"Listening for wake word '{WAKE_WORD}'...")
                audio = recognizer.listen(source)

            heard = recognizer.recognize_google(audio).lower()
            print("Heard:", heard)

            # If wake word OR direct question → respond
            if WAKE_WORD in heard.split() or looks_like_question(heard):
                speak("Go ahead.")
                start_background_listening(recognizer)

                # process first question immediately
                if looks_like_question(heard):
                    process_command(heard)

                while True:
                    time.sleep(0.1)



        except sr.UnknownValueError:
            pass
        except KeyboardInterrupt:
            speak("Goodbye.")
            break


if __name__ == "__main__":
    main()
