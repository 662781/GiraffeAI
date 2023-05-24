import time
import cv2
import mediapipe as mp
import numpy as np
import math

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Initialize pose model
pose_model = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Initialize video capture
video_capture = cv2.VideoCapture(0)

number_of_players = 1
players = []

min_visiblity = 0.5

cooldown_duration = 1  # Cooldown duration in seconds
last_punch_time = 0  # Variable to store the timestamp of the last detected punch
uppercut_timer = 0
hook_timer = 0


class Player:
    left_hand_track_points = []
    left_hand_track_lengths = []
    left_hand_track_current = 0
    left_hand_track_previous_point = 0, 0

    score = {
        "jab": 0,
        "uppercut": 0,
        "hook": 0
    }

    spawn_time = time.time()


def get_moving_average(points, number_of_last_points):
    if len(points) < number_of_last_points:
        return points[-1][0]  # Return the last point if not enough points are available

    sum_x = sum(point[0][0] for point in points[-number_of_last_points:])
    sum_y = sum(point[0][1] for point in points[-number_of_last_points:])

    return int(sum_x / number_of_last_points), int(sum_y / number_of_last_points)


def get_direction(player, number_of_points_to_track):
    if len(player.left_hand_track_points) < 2:
        return 0, 0  # Return 0, 0 if not enough points are available

    current_avg = get_moving_average(points=player.left_hand_track_points,
                                     number_of_last_points=number_of_points_to_track)
    prev_avg = get_moving_average(points=player.left_hand_track_points[:-1],
                                  number_of_last_points=number_of_points_to_track)
    dx = current_avg[0] - prev_avg[0]
    dy = current_avg[1] - prev_avg[1]

    return dx, dy


def track_left_hand(player, landmarks, width, height):
    min_detection_accuracy = 0.8
    left_index = landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value]
    cx_left, cy_left = int(left_index.x * width), int(left_index.y * height)
    detection_accuracy = left_index.visibility

    if detection_accuracy > min_detection_accuracy:
        px_left, py_left = player.left_hand_track_previous_point
        distance_left_hand = math.hypot(cx_left - px_left, cy_left - py_left)

        current_time = time.time()
        player.left_hand_track_points.append(([cx_left, cy_left], current_time))
        player.left_hand_track_lengths.append(distance_left_hand)
        player.left_hand_track_current += distance_left_hand
        player.left_hand_track_previous_point = cx_left, cy_left


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


def detect_punch(player, angle, left_wrist_visibility, left_elbow_visibility):
    global last_punch_time

    dx, dy = get_direction(player=player, number_of_points_to_track=2)

    if time.time() - last_punch_time >= cooldown_duration:
        if left_wrist_visibility > min_visiblity and left_elbow_visibility > min_visiblity:
            detect_jab(angle, dx, dy, player)
            detect_uppercut(angle, dy, player)
            detect_hook(angle, dx, dy, player)

            last_punch_time = time.time()


def detect_uppercut(angle, dy, player):
    global uppercut_timer

    if 30 < angle < 150 and dy < 0:
        if uppercut_timer >= 0.5:
            print("uppercut")
            player.score["uppercut"] += 1
        else:
            uppercut_timer += time.time() - uppercut_timer
    else:
        uppercut_timer = 0


def detect_hook(angle, dx, dy, player):
    global hook_timer

    if 60 < angle < 160 and abs(dx) ** 2 > abs(dy) ** 2:
        if hook_timer >= 0.1:
            print("hook")
            player.score["hook"] += 1
        else:
            hook_timer += time.time() - hook_timer
    else:
        hook_timer = 0


def detect_jab(angle, dx, dy, player):
    if angle > 110 and abs(dy) ** 2 < abs(dx) ** 2:
        print("jab")
        player.score["jab"] += 1


def draw_on_frame(image, angle, left_elbow_xy, results, dx, dy):
    cv2.putText(image, str(angle), tuple(np.multiply(left_elbow_xy, [640, 480]).astype(int)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.putText(image, f"dx: {dx:.2f}, dy: {dy:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
                cv2.LINE_AA)

    # Draw the landmarks on the image
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                              mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                              mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2), )

    # Display the resulting image
    cv2.imshow('Webcam', image)


def create_players():
    for i in range(number_of_players):
        players.append(Player())


def draw_snake_line(image, player, color):
    line_time = 3
    current_time = time.time()
    player.left_hand_track_points = [(point, timestamp) for point, timestamp in player.left_hand_track_points if
                                     current_time - timestamp <= line_time]

    for i in range(1, len(player.left_hand_track_points)):
        if player.left_hand_track_lengths[i - 1] != 0:
            cv2.line(image, tuple(player.left_hand_track_points[i - 1][0]), tuple(player.left_hand_track_points[i][0]),
                     color, 3)


def main_loop():
    global stage

    create_players()

    while video_capture.isOpened():
        # Capture frame-by-frame
        ret, frame = video_capture.read()

        if not ret:
            break

        # Convert the image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect the landmarks
        landmarks = pose_model.process(image)

        # Check if any landmarks were detected
        if landmarks.pose_landmarks is not None:
            left_shoulder_xy, left_elbow_xy, left_wrist_xy, left_wrist_visibility, left_elbow_visibility = get_landmarks(results=landmarks)

            # Calculate the angle between the shoulder, elbow and wrist
            angle = calculate_angle(left_shoulder_xy, left_elbow_xy, left_wrist_xy)

            for player in players:
                track_left_hand(player, landmarks.pose_landmarks.landmark, image.shape[1], image.shape[0])

                # Update the stage and punch counters for each player
                detect_punch(player, angle, left_wrist_visibility, left_elbow_visibility)

            wrist_dx, wrist_dy = get_direction(player, 5)

            draw_snake_line(image=image, player=player, color=(0, 255, 0))  # Use green color for the line
            draw_on_frame(image, angle, left_elbow_xy, landmarks, wrist_dx, wrist_dy)

            # Display the punch counters on the image for the first player
            player = players[0]

            # Convert the image back to BGR for display
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Display the resulting image
            cv2.imshow('Webcam', image)

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture and destroy all windows
    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main_loop()
