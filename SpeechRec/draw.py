import pyautogui
import time
import cv2
import numpy as np
import os
import requests
from PIL import Image
from io import BytesIO
import pygetwindow as gw

# Function to download the image from a URL
def download_image(search_term):
    """Search for an image online and download it."""
    # Use Pexels API or your own image source
    PEXELS_API_KEY = "tUY4cWgCMtu1il15uigfXLwQgZX25Hv5bRxKII8oheBDNj6qTwZCLDc7"  # Make sure you replace with your API key from Pexels
    PEXELS_URL = "https://api.pexels.com/v1/search"
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    params = {
        "query": search_term,
        "per_page": 1  # Get one image
    }

    response = requests.get(PEXELS_URL, headers=headers, params=params)

    # Debugging: print the response URL and status
    print(f"Request URL: {PEXELS_URL}?query={search_term}")
    print(f"Response Status Code: {response.status_code}")
    
    # Check if the response status is successful
    if response.status_code == 200:
        # Fetch image URL from the API response
        try:
            image_url = response.json()['photos'][0]['src']['original']
            print(f"Image URL: {image_url}")

            # Fetch the image using the image URL
            img_response = requests.get(image_url)
            if img_response.status_code == 200:
                # Check if the response content is an image
                content_type = img_response.headers.get('Content-Type')
                print(f"Content-Type of the response: {content_type}")

                # Debugging: Print the first few bytes of the image content
                print(f"First 100 bytes of the response: {img_response.content[:100]}")

                # Check if the content is an image
                if 'image' in content_type:
                    # Try to open the image from the response
                    try:
                        img = Image.open(BytesIO(img_response.content))
                        img_path = "downloaded_image.png"
                        img.save(img_path)
                        print(f"Image saved as {img_path}")
                        return img_path
                    except Exception as e:
                        print(f"Error opening image: {e}")
                else:
                    print("The content is not an image.")
            else:
                print(f"Error fetching image from URL: {img_response.status_code}")
        except Exception as e:
            print(f"Error parsing JSON or getting image URL: {e}")
    else:
        print(f"Error fetching image data: {response.status_code}")

    return None

# Function to convert an image to a sketch
def convert_to_sketch(image_path):
    """Converts an image to a pencil sketch for tracing in Paint."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    # Invert the image and blur
    inv_img = 255 - img
    blur = cv2.GaussianBlur(inv_img, (21, 21), 0)
    
    # Create sketch effect by blending
    sketch = cv2.divide(img, 255 - blur, scale=256)
    
    # Save the sketch
    sketch_path = "sketch.png"
    cv2.imwrite(sketch_path, sketch)
    print(f"Sketch saved as {sketch_path}")
    
    return sketch_path

# Function to open Paint
def open_paint():
    """Opens MS Paint if not already open, or brings it to the foreground and maximizes it."""
    paint_windows = [win for win in gw.getWindowsWithTitle("Paint") if win.visible]
    
    if paint_windows:
        print("Paint is already open. Bringing it to the front...")
        paint_window = paint_windows[0]
        
        try:
            # Activate and maximize the window, handle potential error
            if not paint_window.isActive:
                paint_window.activate()
                time.sleep(1)
            paint_window.maximize()  # Ensure it is maximized
        except Exception as e:
            print(f"Error activating Paint: {e}")
    else:
        print("Opening Paint...")
        pyautogui.press("win")  
        time.sleep(1)
        pyautogui.write("paint")
        time.sleep(1)
        pyautogui.press("enter")
        time.sleep(3)  # Wait for Paint to open
        pyautogui.hotkey("win", "up")  # Maximize the window
# Function to simulate drawing based on the sketch
def get_canvas_position():
    """Estimate the position of the drawing canvas inside Paint."""
    paint_windows = [win for win in gw.getWindowsWithTitle("Paint") if win.visible]

    if not paint_windows:
        print("Paint window not found!")
        return None

    paint_window = paint_windows[0]
    left, top, width, height = paint_window.left, paint_window.top, paint_window.width, paint_window.height

    # Canvas is usually inside the window with some padding
    canvas_x = left + 50  # Approximate offset from the left edge
    canvas_y = top + 100  # Approximate offset from the top edge
    canvas_width = width - 100  # Adjusting for possible UI elements
    canvas_height = height - 150

    return canvas_x, canvas_y, canvas_width, canvas_height

def draw_sketch(sketch_path):
    """Simulates mouse drawing based on the sketch outline, adjusted to canvas size."""
    img = cv2.imread(sketch_path, cv2.IMREAD_GRAYSCALE)

    # Find edges in the sketch
    edges = cv2.Canny(img, 100, 200)
    y_indices, x_indices = np.where(edges != 0)

    # Get the Paint canvas position
    canvas = get_canvas_position()
    if not canvas:
        print("Could not determine Paint canvas position.")
        return

    canvas_x, canvas_y, canvas_width, canvas_height = canvas

    # Scale sketch to fit within the canvas
    img_height, img_width = img.shape
    scale_x = canvas_width / img_width
    scale_y = canvas_height / img_height
    scale = min(scale_x, scale_y)  # Maintain aspect ratio

    # Start drawing
    pyautogui.moveTo(canvas_x, canvas_y)  
    pyautogui.mouseDown()

    for x, y in zip(x_indices, y_indices):
        new_x = int(canvas_x + x * scale)
        new_y = int(canvas_y + y * scale)
        pyautogui.moveTo(new_x, new_y, duration=0.01)

    pyautogui.mouseUp()
    print("Drawing completed!")

# Main function that downloads an image, converts it to a sketch, and draws it in Paint
def draw_object(object_name):
    """Main function: Downloads an image, converts it to a sketch, and draws in Paint."""
    print(f"Searching for '{object_name}' image...")
    image_path = download_image(object_name)
    
    if not image_path:
        print("Could not fetch image.")
        return

    sketch_path = convert_to_sketch(image_path)
    open_paint()
    draw_sketch(sketch_path)

    # Optional: Cleanup downloaded and temporary files
    os.remove(image_path)  # Delete downloaded image
    os.remove(sketch_path)  # Delete sketch image
    print("Cleaned up temporary files.")
