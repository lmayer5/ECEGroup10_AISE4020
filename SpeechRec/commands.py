import pyautogui
import cv2
import numpy as np
from icon_finder import find_all_icons_on_screen, find_search_bar, click_link

def highlight_tabs(positions):
    """Draws red circles on detected 'X' buttons to highlight them."""
    img = np.array(pyautogui.screenshot())
    for i, (x, y) in enumerate(positions):
        cv2.circle(img, (x, y), 15, (0, 0, 255), 2)  # Red circles
        cv2.putText(img, str(i+1), (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)  # Label tabs
    
    cv2.imshow("Detected Tabs", img)
    cv2.waitKey(10000)  # Show for 3 seconds
    cv2.destroyAllWindows()

def execute_command(recognized_word, confidence):
    """Executes commands based on speech recognition."""
    if confidence < 0.3:
        print("Unclear speech detected, please repeat.")
        return

    if "refresh" in recognized_word and confidence > 0.6:
        print("Refreshing the page...")
        pyautogui.hotkey("ctrl", "r")

    if "close tab" in recognized_word and confidence > 0.6:
        print("Detecting close buttons...")
        x_buttons = find_all_icons_on_screen(r"C:\Users\aidan\OneDrive\Desktop\SpeechRec\Chrome Icons\closetab.png")
        x_buttons = find_all_icons_on_screen(r"C:\Users\aidan\OneDrive\Desktop\SpeechRec\Chrome Icons\closetab2.png")
        x_buttons = sorted(set(x_buttons), key=lambda pos: pos[0])  
        if not x_buttons:
            print("No close buttons found.")
            return

        highlight_tabs(x_buttons)  # Show detected tabs with numbers

        try:
            tab_number = int(recognized_word.split()[-1])  # Extract tab number
            if 1 <= tab_number <= len(x_buttons):
                print(f"Closing tab {tab_number}...")
                pyautogui.moveTo(x_buttons[tab_number - 1], duration=0.5)
                pyautogui.click()
            else:
                print("Invalid tab number.")
        except ValueError:
            print("Could not determine tab number.")

    elif "close browser" in recognized_word and confidence > 0.6:
        print("Closing Google Chrome...")
        pyautogui.hotkey("alt", "f4")

    elif "new tab" in recognized_word and confidence > 0.6:
        print("Opening a new tab...")
        pyautogui.hotkey("ctrl", "t")

    elif "switch to tab" in recognized_word and confidence > 0.6:
        try:
            tab_number = int(recognized_word.split()[-1])  # Extract tab number
            if 1 <= tab_number <= 9:
                print(f"Switching to tab {tab_number}...")
                pyautogui.hotkey("ctrl", str(tab_number))
            else:
                print("Tab number out of range (1-9).")
        except ValueError:
            print("Could not determine tab number.")

    elif "click" in recognized_word and confidence > 0.6:
        print("Performing left click...")
        pyautogui.click()
    
    elif "go back" in recognized_word and confidence > 0.6:
        print("Going back...")
        pyautogui.hotkey("alt", "left")  # Use "command" instead of "alt" for Mac
    elif "go forward" in recognized_word and confidence > 0.6:
        print("Going back...")
        pyautogui.hotkey("alt", "right")  # Use "command" instead of "alt" for Mac
    
    elif "search" in recognized_word and confidence > 0.6:
        query = recognized_word.replace("search", "").strip()
        print(f"Searching for: {query}")

        position = find_search_bar()
        if position:
            pyautogui.click(position)  # Click on the detected search bar
            pyautogui.write(query, interval=0.05)  # Type the spoken text
            pyautogui.press("enter")  # Submit the search
        else:
            print("Search bar not found.")
    
    elif "select" in recognized_word:
        link_text = recognized_word.replace("select", "").strip()
        print(f"Looking for link: {link_text}")
        click_link(link_text)
    else:
        print(f"Unrecognized command: {recognized_word}")
    