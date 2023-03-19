import cv2
import mediapipe as mp

# Functions

def does_push_up(results):
     # Check if the person is doing a push-up
        if results.pose_landmarks is not None:
            left_hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]

            if left_hip.y < left_shoulder.y and right_hip.y < right_shoulder.y:
                return True

# Main Script

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
        cv2.putText(annotated_image, "Score: {}".format(push_up_count * 10), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Check if the person is doing a push-up
        if does_push_up(results):
            push_up_count += 1

        # Show the frame
        cv2.imshow('Push-up Detector', annotated_image)

        # Press 'q' to quit
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

# Release resources
cap.release()
cv2.destroyAllWindows()