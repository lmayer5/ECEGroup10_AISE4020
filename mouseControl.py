import mouse
import math
import time
import pyautogui
import numpy as np
from collections import deque

# Get the screen resolution
screen_width, screen_height = pyautogui.size()

#Take a range of x,y coordinates and map unto screen resolusion
old_range_x = [550, 200]
old_range_y = [230,	300]

def map_coordinates(x, y, old_range_x, old_range_y, new_range_x, new_range_y):

    # Extract ranges
    old_min_x, old_max_x = old_range_x
    old_min_y, old_max_y = old_range_y
    new_min_x, new_max_x = new_range_x
    new_min_y, new_max_y = new_range_y

    # Map x and y
    new_x = new_min_x + (x - old_min_x) * (new_max_x - new_min_x) / (old_max_x - old_min_x)
    new_y = new_min_y + (y - old_min_y) * (new_max_y - new_min_y) / (old_max_y - old_min_y)

    return new_x, new_y

#Move mouse to that location




class MovingAverageFilterPair:
    def __init__(self, window_size):
        """
        Initialize the moving average filter for (x, y) pairs.
        
        :param window_size: Number of the most recent pairs to average.
        """
        self.window_size = window_size
        self.queue = deque()
        self.sum_x = 0.0
        self.sum_y = 0.0

    def update(self, new_value):
        """
        Update the filter with a new (x, y) pair.
        
        :param new_value: A tuple (x, y).
        :return: The current moving average as a tuple (avg_x, avg_y).
        """
        x, y = new_value
        
        # Add the new pair to the queue
        self.queue.append((x, y))
        # Update sums
        self.sum_x += x
        self.sum_y += y

        # If we exceed the window size, remove the oldest value
        if len(self.queue) > self.window_size:
            old_x, old_y = self.queue.popleft()
            self.sum_x -= old_x
            self.sum_y -= old_y

        # Compute current average
        current_window_size = len(self.queue)
        avg_x = self.sum_x / current_window_size
        avg_y = self.sum_y / current_window_size

        return (avg_x, avg_y)

def clamp_values(deltas, min_val=-10, max_val=10):
    """
    Takes a list/tuple of two values (deltas).
    If both values lie in the preset range [min_val, max_val], 
    default them to [0, 0]. Otherwise, keep them as is.
    """
    x, y = deltas
    
    # Check if BOTH x and y are within the range
    if min_val <= x <= max_val and min_val <= y <= max_val:
        return [0, 0]
    else:
        return [x, y]
