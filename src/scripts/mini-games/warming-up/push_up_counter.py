# Imports
import cv2
import mediapipe as mp
from pose_detector import PoseDetector


mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Initialize video capture object
cap = cv2.VideoCapture(0)

# Initialize MediaPipe pose object
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    push_up_count = 0
    while cap.isOpened():
        ret, frame = cap.read()

        # Convert the image to RGB and process it with MediaPipe
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        # Draw the pose landmarks on the frame
        annotated_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(annotated_image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        # Flip the annotated image
        annotated_image = cv2.flip(annotated_image, 1)
        
        # Add score to the CV window
        cv2.putText(annotated_image, "Score: {}".format(push_up_count * 10), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Check if the person is doing a push-up
        if PoseDetector.does_push_up(results, mp):
            push_up_count += 1

        # Show the frame
        cv2.imshow('Push-up Detector', annotated_image)

        # Press 'q' to quit
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

# Release resources
cap.release()
cv2.destroyAllWindows()