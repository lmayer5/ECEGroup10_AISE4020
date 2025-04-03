import time
import speech_recognition as sr
from voice_recognition import get_working_microphone, listen_for_wake_word, recognize_speech
from commands import execute_command

def listen_and_recognize():
    """Handles voice commands using a wake word."""
    mic_index = get_working_microphone()
    if mic_index is None:
        print("No working microphone found.")
        return

    recognizer = sr.Recognizer()
    with sr.Microphone(device_index=mic_index) as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Ready to listen... Say 'Opal' to activate.")

        while True:
            # Wait for "Opal"
            listen_for_wake_word(source, recognizer)  # Fixed function call

            # Once detected, listen for commands
            print("Wake word detected! Listening for command...")

            last_speech_time = time.time()
            active_duration = 10  # Listen for commands for 10 seconds after wake word
            
            while time.time() - last_speech_time < active_duration:
                recognized_text = recognize_speech(source, recognizer)

                if recognized_text:
                    confidence = 0.8  # Assume high confidence
                    execute_command(recognized_text, confidence)
                    last_speech_time = time.time()  # Reset timer if a command is received

            print("Returning to wake-word detection mode...")

if __name__ == "__main__":
    listen_and_recognize()