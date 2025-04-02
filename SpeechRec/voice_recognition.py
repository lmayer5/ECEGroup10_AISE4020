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

def recognize_speech():
    """Listens for a spoken command."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for commands...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text.lower()
        except sr.UnknownValueError:
            print("Could not understand speech.")
        except sr.RequestError:
            print("Speech recognition service unavailable.")
    return None