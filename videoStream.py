from faceOrientation import *
from mouseControl import *
from blinkDetectionFunction import *
#from average import *

# Initialize the camera (use 0 for the default camera, 1 for an external USB camera, etc.)
camera_index = 0  # Change to 1, 2, etc., for other USB cameras
cap = cv2.VideoCapture(camera_index)
# Print the resolution
print(f"Screen resolution: {screen_width}x{screen_height}")

# Check if the camera opened successfully
if openCameraSafely(cap):
	frame_count = 0

	# Display the video stream
	while True:
		frame = captureFrame(cap)
		faces, gray = detectFace(frame)

		if faces is not None:
			pframe, landmarks, coords = processLandmarks(frame, faces, gray)
			detectblink(coords, frame)
			p1, p2 = processOrientation(pframe, landmarks)
			presentFrame(pframe, p1, p2)
			x = p2[0]
			y = p2[1]
			#remap 
			raw_cursor = map_coordinates(x, y, old_range_x, old_range_y, [-50, 50], [-50, 50] )
			# clamp values between -10 and 10 
			clamped_cursor = clamp_values(raw_cursor)

			ma_filter = MovingAverageFilterPair(window_size=10)
			avg_cursor = ma_filter.update(clamped_cursor)


			mouse.move(clamped_cursor[0], clamped_cursor[1], absolute = False)

		else:
			presentFrameNoLm(frame)

		# Exit on pressing 'q'
		if cv2.waitKey(1) & 0xFF == ord('q'):
		    break

	# Release the camera and close the window
	cap.release()
	cv2.destroyAllWindows()

