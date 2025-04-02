import os
import cv2
import pyautogui
import numpy as np

ICON_FOLDER = r"C:\Users\Aidan\Desktop\Paint Icons"

def preprocess_icon(icon_path):
    """Loads and preprocesses an icon (grayscale + edge detection)."""
    icon = cv2.imread(icon_path, cv2.IMREAD_GRAYSCALE)
    icon = cv2.Canny(icon, 50, 200)  # Apply edge detection
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

    for scale in np.linspace(0.8, 1.3, 10):  # Try different sizes
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

def validate_paint_window(x, y):
    """Checks if a detected coordinate is within the Paint application window."""
    window = pyautogui.getWindowsWithTitle("Paint")
    if window:
        left, top, width, height = window[0].left, window[0].top, window[0].width, window[0].height
        return left <= x <= left + width and top <= y <= top + height
    return False

def click_on_icon(icon_name):
    print(icon_name)
    """Finds and clicks an icon with improved detection."""
    
    # Ensure .png extension is added if missing
    if not icon_name.endswith(".png"):
        icon_name += ".png"

    # Debug: Show the full path being checked
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