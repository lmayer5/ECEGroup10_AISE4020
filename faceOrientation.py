import cv2
import time
from datetime import datetime
import dlib
import numpy as np

# Load the pre-trained dlib face detector
detector = dlib.get_frontal_face_detector()

# Load the pre-trained facial landmark predictor
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  # Download this file separately

def openCameraSafely(cap):

    if not cap.isOpened():
        print("Error: Could not open the camera.")
        return False
    else:
        print("Camera Opened Succesfully")
        return True

def captureFrame(cap):
    # Capture a frame
    ret, frame = cap.read()
    if not ret:
        print(f"Error: Failed to capture image.")
        sys.exit() #not sure what might cause image to not capture - possible bug latter on
    return frame


model_points = np.array([
    (0.0, 0.0, 0.0),             # Nose tip
    (0.0, -330.0, -65.0),        # Chin
    (-225.0, 170.0, -135.0),     # Left eye left corner
    (225.0, 170.0, -135.0),      # Right eye right corner
    (-150.0, -150.0, -125.0),    # Left Mouth corner
    (150.0, -150.0, -125.0)      # Right mouth corner
    ])

dist_coeffs = np.zeros((4, 1))

def detectFace(frame):
    #faceDetected = True
    # Convert frame to grayscale (dlib works better on grayscale images)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = detector(gray)
    if len(faces) == 0:
        faces = None
        print("Face not deteced")

    return faces, gray

def processLandmarks(frame, faces, gray):

    for face in faces:
        # Get the landmarks
        landmarks = predictor(gray, face)
        # Loop through each landmark point and draw it on the image and save to coords
        coords = []
        for n in range(68):
            x = landmarks.part(n).x
            y = landmarks.part(n).y
            coords.append((x, y))
            pFrame = cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
        coords = np.array(coords, dtype="float")
    
    return pFrame, landmarks, coords #returns processed frame and landmark array

def processOrientation(frame, landmarks):
    #####################
    """
    Given an image and a set of facial landmarks generates the direction of pose
    """
    size = frame.shape
    image_points = np.array([
        (landmarks.part(33).x, landmarks.part(33).y),     # Nose tip
        (landmarks.part(8).x, landmarks.part(8).y),       # Chin
        (landmarks.part(36).x, landmarks.part(36).y),     # Left eye left corner
        (landmarks.part(45).x, landmarks.part(45).y),      # Right eye right corner
        (landmarks.part(48).x, landmarks.part(48).y),     # Left Mouth corner
        (landmarks.part(54).x, landmarks.part(54).y),       # Right mouth corner
        ], dtype="double")

    focal_length = size[1]
    center = (size[1]/2, size[0]/2)
    camera_matrix = np.array([
    [focal_length, 0, center[0]],
    [0, focal_length, center[1]],
    [0, 0, 1]
    ], dtype="double")

    success, rotation_vector, translation_vector = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs)     
    (nose_end_point2D, jacobian) = cv2.projectPoints(np.array([(0.0, 0.0, 1000.0)]), rotation_vector, translation_vector, camera_matrix, dist_coeffs)
    p1 = (int(image_points[0][0]), int(image_points[0][1]))
    p2 = (int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))
    #print(landmarks.part(33))

    return p1, p2


font = cv2.FONT_HERSHEY_SIMPLEX
def presentFrame(frame, p1, p2):
    text = "Coordinates: " + str(p1) + "  Direction: " + str(p2)
    cv2.putText(frame, text,(0,20), font, 0.6,(140,0,255),1,cv2.LINE_AA)
    cv2.imshow('LandMark', frame)  # Show the frame

def presentFrameNoLm(frame):
    cv2.imshow('LandMark', frame)  # Show the frame






