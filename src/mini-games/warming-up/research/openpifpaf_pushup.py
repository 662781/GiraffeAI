import cv2
import numpy as np
import openpifpaf
from openpifpaf import decoder, show
from openpifpaf.network.factory import PifPaf

# Define indices for the keypoints
NOSE = 0
LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_HIP = 11
RIGHT_HIP = 12
LEFT_KNEE = 13
RIGHT_KNEE = 14

# Define angle threshold for pushup
ANGLE_THRESHOLD = 30

# Define model
model = PifPaf(resolution='640x480')

# Start video capture from webcam
cap = cv2.VideoCapture(0)

# Initialize scores for each person
scores = []

while True:
    # Read the frame from the webcam
    ret, frame = cap.read()

    # Process the frame
    predictions, _ = model.process(frame)

    # Decode the predictions
    keypoints, _, _, _ = decoder.decode(predictions, default_confidence_threshold=0.2)

    # Check if shoulders and hips are visible for each person
    for i in range(keypoints.shape[0]):
        if (keypoints[i, NOSE, 2] > 0 and keypoints[i, LEFT_SHOULDER, 2] > 0
            and keypoints[i, RIGHT_SHOULDER, 2] > 0 and keypoints[i, LEFT_HIP, 2] > 0
            and keypoints[i, RIGHT_HIP, 2] > 0):

            # Calculate the angle between the shoulders and hips
            left_shoulder = keypoints[i, LEFT_SHOULDER, :2]
            right_shoulder = keypoints[i, RIGHT_SHOULDER, :2]
            left_hip = keypoints[i, LEFT_HIP, :2]
            right_hip = keypoints[i, RIGHT_HIP, :2]
            vector_1 = left_shoulder - left_hip
            vector_2 = right_shoulder - right_hip
            cosine_angle = np.dot(vector_1, vector_2) / (np.linalg.norm(vector_1) * np.linalg.norm(vector_2))
            angle = np.degrees(np.arccos(cosine_angle))

            # Check if the angle is less than the threshold
            if angle < ANGLE_THRESHOLD:
                # Update the score for this person
                if i < len(scores):
                    scores[i] += 1
                else:
                    scores.append(1)

                cv2.putText(frame, f'Person {i+1}: Pushup Detected! Score: {scores[i]}', (50, 50+50*i), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            else:
                cv2.putText(frame, f'Person {i+1}: Pushup Not Detected. Score: {scores[i]}', (50, 50+50*i), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, f'Person {i+1}: Cannot detect pushup, some keypoints missing. Score: {scores[i]}', (50, 50+50*i), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

    # Show the frame
    cv2.imshow('Pushup Detection', frame)

    # Press 'q' to exit
    if cv2.waitKey(10) & 0xFF==ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
