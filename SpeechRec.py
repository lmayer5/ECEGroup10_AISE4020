import speech_recognition as sr
import pyautogui
import pytesseract
from PIL import Image
import time

def get_working_microphone():
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

def is_textbox_active():
    screenshot = pyautogui.screenshot()
    text = pytesseract.image_to_string(screenshot)
    
    # Check if the text contains the pattern typically found in a textbox (e.g., cursor).
    if "I-beam" in text or "textbox" in text:
        return True
    return False

def listen_and_recognize():
    mic_index = get_working_microphone()
    if mic_index is None:
        print("No working microphone found.")
        return

    recognizer = sr.Recognizer()
    with sr.Microphone(device_index=mic_index) as source:
        print("Listening for speech (say 'click' to perform a mouse click)...")
        recognizer.adjust_for_ambient_noise(source)

        last_speech_time = time.time()  # Track the time of the last speech input
        timeout_duration = 3 
        
        while True:
            try:
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio, show_all=True)  # Get detailed results
                
                if not text or "alternative" not in text:
                    continue

                # Find the best guess based on confidence
                best_guess = max(text["alternative"], key=lambda x: x.get("confidence", 0))

                recognized_word = best_guess["transcript"]
                confidence = best_guess.get("confidence", 0)

                print(f"Recognized: {recognized_word} (Confidence: {confidence:.2f})")

                # Update last_speech_time when speech is detected
                last_speech_time = time.time()

                if "enter" in recognized_word.lower() and confidence > 0.6:
                    print("Enter detected! Hitting the enter key.")
                    pyautogui.press('enter')

                if "click" in recognized_word.lower() and confidence > 0.6:
                    if "right" in recognized_word.lower() and confidence > 0.6:
                        print("Click command detected! Performing right click...")
                        pyautogui.rightClick()
                    else:
                        print("Click command detected! Performing mouse click...")
                        pyautogui.click()
                    # Check if the click is inside a textbox
                    time.sleep(0.2)  # Wait for a moment to simulate the click being registered
                    if is_textbox_active():
                        print("Textbox detected! You can now dictate text.")
                        while True:
                            audio = recognizer.listen(source, timeout=5)
                            try:
                                text = recognizer.recognize_google(audio)
                                print(f"Dictated: {text}")
                                # Type the recognized text into the textbox
                                pyautogui.typewrite(text)
                                last_speech_time = time.time()
                            except sr.UnknownValueError:
                                print("Could not understand the audio.")
                            except sr.RequestError as e:
                                print(f"Could not request results from Google API; {e}")
                    
                elif confidence < 0.3:
                    print("Unclear speech detected, please repeat.")

                # Check for long pause (inactivity) to deselect the textbox
                if time.time() - last_speech_time > timeout_duration:
                    print("No speech detected for a while, deselecting text box.")
                    last_speech_time = time.time()  # Reset the timer after deselecting

            except sr.WaitTimeoutError:
                print("Listening timeout, no speech detected.")
            except sr.UnknownValueError:
                print("Could not understand the audio.")
            except sr.RequestError as e:
                print(f"Could not request results from Google API; {e}")

if __name__ == "__main__":
    listen_and_recognize()