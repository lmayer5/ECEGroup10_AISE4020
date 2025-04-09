import speech_recognition as sr

def get_working_microphone():
    """Finds a working microphone and returns its index."""
    recognizer = sr.Recognizer()
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        try:
            with sr.Microphone(device_index=index) as source:
                print(f"Testing microphone: {name}")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=3)
                text = recognizer.recognize_google(audio)
                print(f"Microphone {name} works. Detected: {text}")
                return index
        except Exception as e:
            print(f"Microphone {name} failed: {e}")
    return None

def listen_for_wake_word(source, recognizer):
    """Listens continuously for the wake word 'Opal'."""
    print("Waiting for wake word: 'Test'...")

    while True:
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio).lower()
            print(f"Detected: {text}")

            if "test" in text:
                print("Wake word detected! Listening for command...")
                return True  # Wake word detected, return to main loop

        except sr.WaitTimeoutError:
            print("No speech detected, continuing to listen for wake word.")
        except sr.UnknownValueError:
            print("Could not understand speech.")
        except sr.RequestError:
            print("Speech recognition service unavailable.")


def recognize_speech(source, recognizer):
    """Listens for a spoken command after wake word."""
    print("Listening for command...")
    try:
        audio = recognizer.listen(source, timeout=5)
        text = recognizer.recognize_google(audio).lower()
        print(f"Recognized command: {text}")
        return text
    except sr.WaitTimeoutError:
        print("No speech detected during command listening.")
        return None
    except sr.UnknownValueError:
        print("Could not understand speech.")
        return None
    except sr.RequestError:
        print("Speech recognition service unavailable.")
        return None