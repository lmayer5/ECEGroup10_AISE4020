import os
import cv2
import time
import pyautogui
import numpy as np
import pytesseract
from difflib import SequenceMatcher 


ICON_FOLDER = r"C:\Users\aidan\OneDrive\Desktop\SpeechRec\Chrome Icons"
SEARCH_BAR_FOLDER = r"C:\Users\aidan\OneDrive\Desktop\SpeechRec\Chrome Icons\SearchBars"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def find_search_bar(confidence=0.79):
    """Detects the search bar using multiple example images."""
    screen = pyautogui.screenshot()
    screen_np = np.array(screen)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)

    best_match = None
    highest_confidence = 0

    for image_file in os.listdir(SEARCH_BAR_FOLDER):
        icon_path = os.path.join(SEARCH_BAR_FOLDER, image_file)
        icon = cv2.imread(icon_path, cv2.IMREAD_GRAYSCALE)
        if icon is None:
            raise ValueError("Template image (search bar icon) not found or could not be loaded.")
        if screen_gray is None:
            raise ValueError("Screenshot capture failed. Ensure that the screen is being captured correctly.") 
        if icon.shape[0] > screen_gray.shape[0] or icon.shape[1] > screen_gray.shape[1]:
            scale_factor = min(screen_gray.shape[0] / icon.shape[0], screen_gray.shape[1] / icon.shape[1])
            icon = cv2.resize(icon, (0, 0), fx=scale_factor, fy=scale_factor)       
        result = cv2.matchTemplate(screen_gray, icon, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        print("Screenshot size:", screen_gray.shape)
        print("Template size:", icon.shape)
        if max_val > confidence and max_val > highest_confidence:
            highest_confidence = max_val
            best_match = (max_loc[0] + icon.shape[1] // 2, max_loc[1] + icon.shape[0] // 2)

    if best_match:
        print(f"Search bar detected at {best_match} with confidence {highest_confidence:.2f}")
        return best_match
    else:
        print("No search bar detected.")
        return None

def filter_duplicates(positions, min_distance=50):
    """Removes duplicate close-tab detections that are too close to each other."""
    filtered_positions = []
    
    for pos in positions:
        if all(np.linalg.norm(np.array(pos) - np.array(existing)) > min_distance for existing in filtered_positions):
            filtered_positions.append(pos)

    print(f"Filtered to {len(filtered_positions)} unique close-tab buttons.")
    return filtered_positions


def find_all_icons_on_screen(icon_path, confidence=0.8):
    """Finds all instances of an icon on the screen and returns their positions."""
    print("Capturing screenshot...")
    screen = pyautogui.screenshot()
    screen_np = np.array(screen)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)

    print(f"Loading icon from: {icon_path}")
    icon = cv2.imread(icon_path, cv2.IMREAD_GRAYSCALE)

    if icon is None:
        print(f"ERROR: Could not load icon image from {icon_path}")
        return []

    detected_positions = []
    for scale in np.linspace(0.9, 1.1, 5):
        resized_icon = cv2.resize(icon, None, fx=scale, fy=scale)
        result = cv2.matchTemplate(screen_gray, resized_icon, cv2.TM_CCOEFF_NORMED)
        
        locations = np.where(result >= confidence)
        for pt in zip(*locations[::-1]): 
            detected_positions.append((pt[0] + resized_icon.shape[1] // 2, pt[1] + resized_icon.shape[0] // 2))

    detected_positions = filter_duplicates(detected_positions)
    
    if detected_positions:
        print(f"Final detected close buttons: {len(detected_positions)}")
    else:
        print("No close-tab buttons found.")
    
    return detected_positions

def validate_chrome_window(x, y):
    """Checks if a detected coordinate is within the Chrome application window."""
    window = pyautogui.getWindowsWithTitle("Google Chrome")
    if window:
        left, top, width, height = window[0].left, window[0].top, window[0].width, window[0].height
        return left <= x <= left + width and top <= y <= top + height
    return False

def preprocess_icon(icon_path):
    """Loads and preprocesses an icon (grayscale + edge detection)."""
    icon = cv2.imread(icon_path, cv2.IMREAD_GRAYSCALE)
    icon = cv2.Canny(icon, 50, 200)
    return icon

def find_icon_on_screen(icon_path, confidence=0.8):
    """Finds an icon on the screen with dynamic scaling."""
    print("Capturing screenshot...")
    screen = pyautogui.screenshot()
    screen_np = np.array(screen)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)

    print(f"Loading icon from: {icon_path}")
    icon = cv2.imread(icon_path, cv2.IMREAD_GRAYSCALE)

    if icon is None:
        print(f"ERROR: Could not load icon image from {icon_path}")
        return None

    for scale in np.linspace(0.8, 1.3, 10): 
        resized_icon = cv2.resize(icon, None, fx=scale, fy=scale)
        result = cv2.matchTemplate(screen_gray, resized_icon, cv2.TM_CCOEFF_NORMED)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            icon_x = max_loc[0] + (resized_icon.shape[1] // 2)
            icon_y = max_loc[1] + (resized_icon.shape[0] // 2)
            print(f"Match found at {icon_x}, {icon_y} with confidence {max_val:.2f}")
            return (icon_x, icon_y)

    print("No match found at any scale.")
    return None

def click_on_icon(icon_name):
    print(icon_name)
    """Finds and clicks an icon with improved detection."""
    
    if not icon_name.endswith(".png"):
        icon_name += ".png"

    icon_path = os.path.join(ICON_FOLDER, icon_name)
    print(icon_path)
    print(f"Attempting to find icon: '{icon_name}'")
    print(f"Full icon path: {icon_path}")

    # Check if the folder exists
    if not os.path.exists(ICON_FOLDER):
        print(f"ERROR: The folder '{ICON_FOLDER}' does not exist.")
        return False

    # Check if the icon file exists
    if not os.path.exists(icon_path):
        print(f"ERROR: Icon '{icon_name}' not found in folder '{ICON_FOLDER}'")
        print(f"Available files: {os.listdir(ICON_FOLDER)}")  # List all files in folder
        return False

    position = find_icon_on_screen(icon_path)
    if position:
        print(f"Icon '{icon_name}' found at: {position}, clicking...")
        pyautogui.moveTo(position, duration=0.5)
        pyautogui.click()
        return True
    else:
        print(f"Icon '{icon_name}' not found on screen.")
        return False

def similar(a, b):
    """Returns a similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()

def detect_colored_text(screen_np, lower_color, upper_color):
    """Extracts text of a specific color range from an image."""
    hsv = cv2.cvtColor(screen_np, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    colored_text = cv2.bitwise_and(screen_np, screen_np, mask=mask)
    gray = cv2.cvtColor(colored_text, cv2.COLOR_RGB2GRAY)
    
    return pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

def extract_text_positions(detected_text):
    """Extracts text positions from OCR results."""
    link_positions = []
    for i, text in enumerate(detected_text["text"]):
        clean_text = text.lower().strip()
        if clean_text and len(clean_text) > 2:
            x, y, w, h = (detected_text["left"][i], detected_text["top"][i], 
                          detected_text["width"][i], detected_text["height"][i])
            link_positions.append((clean_text, x + w // 2, y + h // 2))

    return link_positions

def similar(a, b):
    """Returns a similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()

def normalize_text(text):
    """Lowercases and removes spaces for better comparison."""
    return text.lower().replace(" ", "")

def detect_text(screen_np):
    """Detects all text in an image using optimized OCR settings."""
    gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
    custom_config = r'--oem 3 --psm 6'
    detected_text = pytesseract.image_to_data(gray, config=custom_config, output_type=pytesseract.Output.DICT)
    
    link_positions = []
    for i, text in enumerate(detected_text["text"]):
        clean_text = text.strip()
        if clean_text and len(clean_text) > 2:  # Ignore very short words
            x, y, w, h = (detected_text["left"][i], detected_text["top"][i], 
                          detected_text["width"][i], detected_text["height"][i])
            link_positions.append((clean_text, x + w // 2, y + h // 2))

    return link_positions

def find_links_on_screen():
    """Captures screenshot and extracts text positions."""
    print("Capturing screenshot to detect links...")
    screen = pyautogui.screenshot()
    screen_np = np.array(screen)

    return detect_text(screen_np)

def click_link(target_text, timeout=5):
    """Finds and clicks a link with the given text."""
    print(f"Looking for link: {target_text}")
    normalized_target = normalize_text(target_text)

    start_time = time.time()
    while time.time() - start_time < timeout:  
        links = find_links_on_screen()

        if not links:
            print("No links detected.")
            return False

        links.sort(key=lambda item: similar(normalized_target, normalize_text(item[0])), reverse=True)
        
        best_match, x, y = links[0]
        confidence = similar(normalized_target, normalize_text(best_match))

        print(f"Best match: {best_match} (Confidence: {confidence:.2f})")

        if confidence > 0.79:
            print(f"Clicking link: {best_match} at ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.3)
            pyautogui.click()
            return True
        else:
            print("No strong match found.")

        time.sleep(0.5)  

    print(f"Link '{target_text}' not found. Exiting.")
    return False