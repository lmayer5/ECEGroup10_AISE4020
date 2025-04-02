import pyautogui
from icon_finder import click_on_icon
from draw import draw_object

def execute_command(recognized_word, confidence):
    """Executes commands based on speech recognition."""
    if confidence < 0.3:
        print("Unclear speech detected, please repeat.")
        return

    if "enter" in recognized_word and confidence > 0.6:
        print("Hitting Enter key.")
        pyautogui.press('enter')

    elif "click" in recognized_word and confidence > 0.6:
        if "right" in recognized_word:
            print("Performing right click...")
            pyautogui.rightClick()
        else:
            print("Performing left click...")
            pyautogui.click()
    if "select" in recognized_word and confidence > 0.6:
        tool_name = recognized_word.replace("select", "").strip().lower()

        if not tool_name.endswith(".png"):  # Ensure it's a .png file
            tool_name += ".png"
            print (tool_name)

        print(f"Selecting tool: {tool_name}")  # Debug print
        click_on_icon(tool_name)
    
    elif "draw" in recognized_word and confidence > 0.6:
        object_name = recognized_word.replace("draw", "").strip()
        print(f"Drawing requested for: {object_name}")
        draw_object(object_name)

    elif "close tab" in recognized_word and confidence > 0.6:
        print("Closing the current tab...")
        pyautogui.hotkey("ctrl", "w")

    else:
        print(f"Unrecognized command: {recognized_word}")