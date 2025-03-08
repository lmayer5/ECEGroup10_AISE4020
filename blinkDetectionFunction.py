import cv2
import dlib
import numpy as np
import mouse

# Eye landmark indices (for dlib’s 68-point model)
LEFT_EYE_POINTS  = [36, 37, 38, 39, 40, 41]
RIGHT_EYE_POINTS = [42, 43, 44, 45, 46, 47]

def euclidean_distance(ptA, ptB):
    return np.linalg.norm(ptA - ptB)

def eye_aspect_ratio(eye_points):
    # p2-p6 (eye_points[1], eye_points[5]) and p3-p5 (eye_points[2], eye_points[4])
    A = euclidean_distance(eye_points[1], eye_points[5])
    B = euclidean_distance(eye_points[2], eye_points[4])
    # p1-p4 (eye_points[0], eye_points[3])
    C = euclidean_distance(eye_points[0], eye_points[3])
    EAR = (A + B) / (2.0 * C)
    return EAR

# Set blink threshold and consecutive frame count requirement
EAR_THRESHOLD = 0.15
CONSEC_FRAMES = 3

# Counters
blink_counter = 0
total_blinks = 0

def detectblink(coords, frame):
	global blink_counter, total_blinks  # <-- Declare global here

	# Extract eye coordinates for both eyes
	leftEye  = coords[LEFT_EYE_POINTS]
	rightEye = coords[RIGHT_EYE_POINTS]

	# Compute the EAR for both eyes
	leftEAR  = eye_aspect_ratio(leftEye)
	rightEAR = eye_aspect_ratio(rightEye)
	#ear = (leftEAR + rightEAR) / 2.0  # average EAR for both eyes
	ear = (rightEAR) #only right eye

	# Check if EAR is below the blink threshold
	if ear < EAR_THRESHOLD:
		blink_counter += 1
		#mouse.click()
	else:
		# If the eye was below threshold for a sufficient number of frames,
		# count as a blink
		if blink_counter >= CONSEC_FRAMES:
			total_blinks += 1
		blink_counter = 0

	# Display EAR on the frame
	cv2.putText(frame, f"EAR: {ear:.2f}", (30, 30),
	            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
	# Display total blinks
	cv2.putText(frame, f"Blinks: {total_blinks}", (30, 60),
	            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
