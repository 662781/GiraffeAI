import cv2
import mediapipe as mp
import numpy as np

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Initialize pose model
pose_model = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Initialize video capture
video_capture = cv2.VideoCapture(0)

# Initialize jab counter variable
number_of_jabs = 0
stage = "hit"


def calculate_angle(first_point, mid_point, end_point):
    first_point = np.array(first_point)
    mid_point = np.array(mid_point)
    end_point = np.array(end_point)

    radians = np.arctan2(end_point[1] - mid_point[1], end_point[0] - mid_point[0]) - \
              np.arctan2(first_point[1] - mid_point[1], first_point[0] - mid_point[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180:
        angle = 360 - angle
    return angle


def get_landmarks(results):
    left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    left_elbow = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW.value]
    left_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST.value]

    left_shoulder_xy = [left_shoulder.x, left_shoulder.y]
    left_elbow_xy = [left_elbow.x, left_elbow.y]
    left_wrist_xy = [left_wrist.x, left_wrist.y]

    return left_shoulder_xy, left_elbow_xy, left_wrist_xy, left_wrist.visibility, left_elbow.visibility


def update_stage_and_jab_counter(angle, stage, left_wrist_visibility, left_elbow_visibility, number_of_jabs):
    if angle > 120 and stage == "hit" and left_wrist_visibility > 0.5 and left_elbow_visibility > 0.5:
        stage = "stretched"

    if angle < 20 and stage == "stretched":
        stage = "hit"
        number_of_jabs += 1

    return stage, number_of_jabs


def draw_on_frame(image, angle, left_elbow_xy, number_of_jabs, results):
    cv2.putText(image, str(angle), tuple(np.multiply(left_elbow_xy, [640, 480]).astype(int)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    # Display the jab counter on the image
    cv2.putText(image, str(int(number_of_jabs)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

    # Convert the image back to BGR for display
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Draw the landmarks on the image
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                              mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                              mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2), )

    # Display the resulting image
    cv2.imshow('Webcam', image)


def main_loop():
    global number_of_jabs, stage
    while video_capture.isOpened():
        # Capture frame-by-frame
        ret, frame = video_capture.read()

        if not ret:
            break

        # Convert the image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect the landmarks
        results = pose_model.process(image)

        # Check if any landmarks were detected
        if results.pose_landmarks is not None:
            left_shoulder_xy, left_elbow_xy, left_wrist_xy, left_wrist_visibility, left_elbow_visibility = get_landmarks(
                results)

            # Calculate the angle between the shoulder, elbow and wrist
            angle = calculate_angle(left_shoulder_xy, left_elbow_xy, left_wrist_xy)

            # Update the stage and jab counter
            stage, number_of_jabs = update_stage_and_jab_counter(angle, stage, left_wrist_visibility,
                                                                 left_elbow_visibility, number_of_jabs)

            # Draw on the frame
            draw_on_frame(image, angle, left_elbow_xy, number_of_jabs, results)

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture and destroy all windows
    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main_loop()
