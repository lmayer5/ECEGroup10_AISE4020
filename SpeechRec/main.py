import time
import speech_recognition as sr
from voice_recognition import get_working_microphone, recognize_speech
from commands import execute_command

def listen_and_recognize():
    """Handles voice commands for mouse clicks and typing."""
    mic_index = get_working_microphone()
    if mic_index is None:
        print("No working microphone found.")
        return

    recognizer = sr.Recognizer()
    with sr.Microphone(device_index=mic_index) as source:
        print("Listening for commands...")
        recognizer.adjust_for_ambient_noise(source)

        last_speech_time = time.time()
        timeout_duration = 3 
        
        while True:
            try:
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio, show_all=True)

                if not text or "alternative" not in text:
                    continue

                best_guess = max(text["alternative"], key=lambda x: x.get("confidence", 0))
                recognized_word = best_guess["transcript"].lower()
                confidence = best_guess.get("confidence", 0)

                print(f"Recognized: {recognized_word} (Confidence: {confidence:.2f})")
                last_speech_time = time.time()

                # Execute the recognized command
                execute_command(recognized_word, confidence)

                if time.time() - last_speech_time > timeout_duration:
                    print("No speech detected for a while, resetting timer.")
                    last_speech_time = time.time()

            except sr.WaitTimeoutError:
                print("Listening timeout, no speech detected.")
            except sr.UnknownValueError:
                print("Could not understand the audio.")
            except sr.RequestError as e:
                print(f"Could not request results from Google API; {e}")

if __name__ == "__main__":
    listen_and_recognize()