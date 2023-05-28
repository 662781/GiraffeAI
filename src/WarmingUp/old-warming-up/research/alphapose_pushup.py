import cv2
import time
import alphapose

# Load the AlphaPose model
model = alphapose.PoseEstimation()

# Set up the video capture device
cap = cv2.VideoCapture(0)

# Loop through the frames of the video
while True:
    # Read a frame from the video capture device
    ret, frame = cap.read()
    if not ret:
        break

    # Detect the poses in the frame using AlphaPose
    poses = model.detect(frame)

    # Count the number of people doing a pushup
    pushup_count = 0
    for pose in poses:
        # Check if the person is doing a pushup
        if pose['score'] > 0.5 and pose['keypoints'][11][1] < pose['keypoints'][13][1] and pose['keypoints'][12][1] < pose['keypoints'][14][1]:
            pushup_count += 1

    # Display the number of people doing a pushup
    cv2.putText(frame, f"Pushup count: {pushup_count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.imshow('frame', frame)

    # Wait for a key press and check if it is the 'q' key to quit
    if cv2.waitKey(1) == ord('q'):
        break

# Release the video capture device and close the OpenCV window
cap.release()
cv2.destroyAllWindows()
