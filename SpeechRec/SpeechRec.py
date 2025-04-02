import pyautogui
import cv2
import numpy as np
import pytesseract
import speech_recognition as sr
import pygetwindow as gw
import time

# Set up Tesseract OCR (Update path if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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

def get_chrome_window_region():
    """Finds the Chrome window position dynamically."""
    chrome_windows = [win for win in gw.getWindowsWithTitle("Google Chrome")]
    if chrome_windows:
        win = chrome_windows[0]
        return (win.left, win.top, win.width, 100)  # Capture only the tab bar area
    return None

def bring_chrome_to_front():
    """Brings Chrome to the front before taking a screenshot."""
    chrome_windows = [win for win in gw.getWindowsWithTitle("Google Chrome")]
    if chrome_windows:
        chrome_windows[0].activate()
        time.sleep(1)  # Wait for Chrome to be in focus

def capture_tab_bar():
    """Captures only the Chrome tab bar dynamically."""
    region = get_chrome_window_region()
    if not region:
        print("Chrome window not found!")
        return None
    
    screenshot = pyautogui.screenshot(region=region)
    screenshot_np = np.array(screenshot)
    
    gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    return thresh

def extract_tab_titles():
    """Uses OpenCV and OCR to extract tab names."""
    bring_chrome_to_front()
    processed_image = capture_tab_bar()
    if processed_image is None:
        return []
    
    tab_text = pytesseract.image_to_string(processed_image, config="--psm 6")
    tab_lines = tab_text.split("\n")

    tabs = [line.strip() for line in tab_lines if line.strip()]
    return tabs

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

def click_on_tab(tab_name, tabs):
    """Finds and closes the specified tab."""
    if not tabs:
        print("No tabs detected.")
        return False

    for tab in tabs:
        if tab_name in tab.lower():
            print(f"Found tab: {tab}, closing it...")
            pyautogui.hotkey("ctrl", "w")  # Close the tab
            return True
    
    print("Tab not found.")
    return False

def listen_and_recognize():
    """Handles voice commands for mouse clicks, typing, and closing tabs."""
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

                # Handling "Close Tab" command
                if "close tab" in recognized_word and confidence > 0.6:
                    print("Closing tab...")
                    tabs = extract_tab_titles()
                    if not tabs:
                        print("No tabs detected via OCR.")
                        continue
                    
                    print("\nDetected Tabs:")
                    for idx, tab in enumerate(tabs):
                        print(f"{idx + 1}. {tab}")

                    print("\nSay the tab name you want to close...")
                    tab_name = recognize_speech()
                    
                    if tab_name:
                        click_on_tab(tab_name, tabs)

                elif "enter" in recognized_word and confidence > 0.6:
                    print("Hitting Enter key.")
                    pyautogui.press('enter')

                elif "click" in recognized_word and confidence > 0.6:
                    if "right" in recognized_word:
                        print("Performing right click...")
                        pyautogui.rightClick()
                    else:
                        print("Performing left click...")
                        pyautogui.click()

                elif confidence < 0.3:
                    print("Unclear speech detected, please repeat.")

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