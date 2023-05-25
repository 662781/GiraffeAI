import time
import cv2
import mediapipe as mp
import numpy as np
import math
import random

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

punch_types = ["jab", "uppercut", "hook"]
selected_punch = "jab"


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

    points = 0
    spawn_time = time.time()


def select_random_punch():
    global selected_punch
    punch_types = ["jab", "uppercut", "hook"]
    probabilities = [4, 1, 1]  # Probabilities of each punch type

    # Create a weighted list of punches based on probabilities
    weighted_punches = []
    for i, punch in enumerate(punch_types):
        weighted_punches.extend([punch] * probabilities[i])

    # Select a random punch from the weighted list
    random_punch = random.choice(weighted_punches)
    print("Selected punch:", random_punch)
    selected_punch = random_punch


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
            if selected_punch == "uppercut":
                player.points += 1
            uppercut_timer = 0
        else:
            uppercut_timer += time.time() - uppercut_timer
    else:
        uppercut_timer = 0


def detect_hook(angle, dx, dy, player):
    global hook_timer

    if 60 < angle < 160 and abs(dx) ** 2 > abs(dy) ** 2:
        if hook_timer >= 0.1:
            if selected_punch == "hook":
                player.points += 1
            hook_timer = 0
        else:
            hook_timer += time.time() - hook_timer
    else:
        hook_timer = 0


def detect_jab(angle, dx, dy, player):
    if angle > 110 and abs(dy) ** 2 < abs(dx) ** 2:
        print("jab")
        if selected_punch == "jab":
            player.points += 1


def draw_on_frame(image, angle, left_elbow_xy, results, dx, dy, player, elapsed_time):
    cv2.putText(image, str(angle), tuple(np.multiply(left_elbow_xy, [640, 480]).astype(int)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.putText(image, f"dx: {dx:.2f}, dy: {dy:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
                cv2.LINE_AA)
    # put the selected_punch on the screen in the middle
    cv2.putText(image, f"selected punch: {selected_punch}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
                cv2.LINE_AA)

    # Draw the landmarks on the image
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                              mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                              mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2), )
    draw_snake_line(image=image, player=player, color=(0, 255, 0))

    # draw the points on the screen
    cv2.putText(image, f"points: {player.points}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
                cv2.LINE_AA)
    #draw the time in the top right corner
    cv2.putText(image, f"time: {91 - elapsed_time:.0f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
                cv2.LINE_AA)

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
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


# ...

def main_loop():
    global last_punch_time
    create_players()

    start_time = time.time()

    while video_capture.isOpened():
        ret, frame = video_capture.read()

        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        landmarks = pose_model.process(image)

        if landmarks.pose_landmarks is not None:
            left_shoulder_xy, left_elbow_xy, left_wrist_xy, left_wrist_visibility, left_elbow_visibility = get_landmarks(
                results=landmarks)
            angle = calculate_angle(left_shoulder_xy, left_elbow_xy, left_wrist_xy)

            for player in players:
                track_left_hand(player, landmarks.pose_landmarks.landmark, image.shape[1], image.shape[0])
                detect_punch(player, angle, left_wrist_visibility, left_elbow_visibility)

            wrist_dx, wrist_dy = get_direction(player, 5)

            # Call the selected_punch function every 5 seconds
            if time.time() - last_punch_time >= 5:
                select_random_punch()
                last_punch_time = time.time()

            # Calculate elapsed time
            elapsed_time = time.time() - start_time

            draw_on_frame(image, angle, left_elbow_xy, landmarks, wrist_dx, wrist_dy, player, elapsed_time)


            # Check if the game time has exceeded 90 seconds
            if elapsed_time >= 91:
                break

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture and destroy all windows
    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main_loop()
