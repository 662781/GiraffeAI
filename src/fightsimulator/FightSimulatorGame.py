import time
import cv2
import mediapipe as mp
import numpy as np
import math
import random

from shared.model import CVGame
from shared.utils import Generics, CVAssets

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


class FightSimulatorGame(CVGame):
    def __init__(self):
        super().__init__()
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.pose_model = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.number_of_players = 1
        self.players = []
        self.min_visiblity = 0.5
        self.cooldown_duration = 1
        self.last_punch_time = 0
        self.uppercut_timer = 0
        self.hook_timer = 0
        self.punch_types = ["jab", "uppercut", "hook"]
        self.selected_punch = "jab"
        self.elapsed_time = 0
        self.start_time = time.time()
        self.video_capture = cv2.VideoCapture(0)
        self.combined_points = 0
        self.previous_combined_points = -1

    def setup(self, options):
        self.options = options


    def update(self, frame):
        self.create_players()

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        landmarks = self.pose_model.process(image)

        self.check_and_select_punch()

        if landmarks.pose_landmarks is not None:
            left_shoulder_xy, left_elbow_xy, left_wrist_xy, left_wrist_visibility, left_elbow_visibility = self.get_landmarks(
                landmarks)

            width, height = image.shape[1], image.shape[0]

            self.track_left_hand(player=self.players[0], landmarks=landmarks.pose_landmarks.landmark,
                                 width=width, height=height)

            angle = self.calculate_angle(first_point=left_shoulder_xy, mid_point=left_elbow_xy,
                                         end_point=left_wrist_xy)

            self.detect_punch(player=self.players[0], angle=angle, left_wrist_visibility=left_wrist_visibility,
                              left_elbow_visibility=left_elbow_visibility)

            self.elapsed_time = time.time() - self.start_time

            if cv2.waitKey(1) & 0xFF == ord('q') or self.elapsed_time > 95:
                self.should_switch = True
                self.next_game = None

        return self.draw_on_frame(image=image, angle=angle, left_elbow_xy=left_elbow_xy, results=landmarks,
                                  player=self.players[0])

    def cleanup(self):
        super().cleanup()

    class Player:
        def __init__(self):
            self.left_hand_track_points = []
            self.left_hand_track_lengths = []
            self.left_hand_track_current = 0
            self.left_hand_track_previous_point = 0, 0

            self.score = {
                "jab": 0,
                "uppercut": 0,
                "hook": 0
            }

            self.points = 0
            self.spawn_time = time.time()

    def check_and_select_punch(self):
        if self.elapsed_time % 5 <= 0.13:
            self.select_random_punch()

        if self.combined_points != self.previous_combined_points:
            self.select_random_punch()
            self.previous_combined_points = self.combined_points

    def select_random_punch(self):
        punch_types = ["jab", "uppercut", "hook"]
        probabilities = [4, 1, 1]  # Probabilities of each punch type

        # Create a weighted list of punches based on probabilities
        weighted_punches = []
        for i, punch in enumerate(punch_types):
            weighted_punches.extend([punch] * probabilities[i])

        # Select a random punch from the weighted list
        random_punch = random.choice(weighted_punches)
        print("Selected punch:", random_punch)
        self.selected_punch = random_punch

    def get_moving_average(self, points, number_of_last_points):
        if len(points) < number_of_last_points:
            return points[-1][0]  # Return the last point if not enough points are available

        sum_x = sum(point[0][0] for point in points[-number_of_last_points:])
        sum_y = sum(point[0][1] for point in points[-number_of_last_points:])

        return int(sum_x / number_of_last_points), int(sum_y / number_of_last_points)

    def get_direction(self, player, number_of_points_to_track):
        if len(player.left_hand_track_points) < 2:
            return 0, 0  # Return 0, 0 if not enough points are available

        current_avg = self.get_moving_average(points=player.left_hand_track_points,
                                              number_of_last_points=number_of_points_to_track)
        prev_avg = self.get_moving_average(points=player.left_hand_track_points[:-1],
                                           number_of_last_points=number_of_points_to_track)
        dx = current_avg[0] - prev_avg[0]
        dy = current_avg[1] - prev_avg[1]

        return dx, dy

    def track_left_hand(self, player, landmarks, width, height):
        min_detection_accuracy = 0.8
        left_index = landmarks[self.mp_pose.PoseLandmark.LEFT_INDEX.value]
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

    def calculate_angle(self, first_point, mid_point, end_point):
        first_point = np.array(first_point)
        mid_point = np.array(mid_point)
        end_point = np.array(end_point)

        radians = np.arctan2(end_point[1] - mid_point[1], end_point[0] - mid_point[0]) - \
                  np.arctan2(first_point[1] - mid_point[1], first_point[0] - mid_point[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180:
            angle = 360 - angle
        return angle

    def get_landmarks(self, results):
        left_shoulder = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        left_elbow = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
        left_wrist = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST.value]

        left_shoulder_xy = [left_shoulder.x, left_shoulder.y]
        left_elbow_xy = [left_elbow.x, left_elbow.y]
        left_wrist_xy = [left_wrist.x, left_wrist.y]

        return left_shoulder_xy, left_elbow_xy, left_wrist_xy, left_wrist.visibility, left_elbow.visibility

    def detect_punch(self, player, angle, left_wrist_visibility, left_elbow_visibility):
        dx, dy = self.get_direction(player=player, number_of_points_to_track=2)

        if time.time() - self.last_punch_time >= self.cooldown_duration:
            if left_wrist_visibility > self.min_visiblity and left_elbow_visibility > self.min_visiblity:
                self.detect_jab(angle, dx, dy, player)
                self.detect_uppercut(angle, dy, player)
                self.detect_hook(angle, dx, dy, player)

                self.last_punch_time = time.time()

    def detect_uppercut(self, angle, dy, player):
        if 30 < angle < 150 and dy < 0:
            if self.uppercut_timer >= 0.5:
                print("uppercut")
                if self.selected_punch == "uppercut":
                    player.points += 1
                    self.combined_points += 1
                self.uppercut_timer = 0
            else:
                self.uppercut_timer += time.time() - self.uppercut_timer
        else:
            self.uppercut_timer = 0

    def detect_hook(self, angle, dx, dy, player):
        if 60 < angle < 160 and abs(dx) ** 2 > abs(dy) ** 2:
            if self.hook_timer >= 0.1:
                if self.selected_punch == "hook":
                    player.points += 1
                    self.combined_points += 1
                self.hook_timer = 0
            else:
                self.hook_timer += time.time() - self.hook_timer
        else:
            self.hook_timer = 0

    def detect_jab(self, angle, dx, dy, player):
        if angle > 110 and abs(dy) ** 2 < abs(dx) ** 2:
            print("jab")
            if self.selected_punch == "jab":
                player.points += 1
                self.combined_points += 1

    def draw_on_frame(self, image, angle, left_elbow_xy, results, player):
        cv2.putText(image, str(angle), tuple(np.multiply(left_elbow_xy, [640, 480]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

        # put the selected_punch on the screen in the middle
        image = Generics.put_text_with_custom_font(image=image, text=f"punch: {self.selected_punch}",
                                                   position=(220, 80),
                                                   font_path=CVAssets.FONT_FRUIT_NINJA, font_size=35,
                                                   font_color=(248, 210, 62), outline_color=(0, 0, 0), outline_width=2)

        image = Generics.put_text_with_custom_font(image=image, text=f"score: {player.points}", position=(10, 10),
                                                   font_path=CVAssets.FONT_FRUIT_NINJA,
                                                   font_size=30, font_color=(205, 127, 50), outline_color=(0, 0, 0),
                                                   outline_width=2)

        image = Generics.put_text_with_custom_font(image=image, text=f"time left: {94 - self.elapsed_time:.0f}",
                                                   position=(420, 10), font_path=CVAssets.FONT_FRUIT_NINJA,
                                                   font_size=30, font_color=(205, 127, 50), outline_color=(0, 0, 0),
                                                   outline_width=2)

        self.mp_drawing.draw_landmarks(image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                                       self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                       self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2,
                                                                   circle_radius=2), )
        self.draw_snake_line(image=image, player=player, color=(0, 255, 0))

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image

    def create_players(self):
        for i in range(self.number_of_players):
            self.players.append(self.Player())

    def draw_snake_line(self, image, player, color):
        line_time = 3
        current_time = time.time()
        player.left_hand_track_points = [(point, timestamp) for point, timestamp in player.left_hand_track_points if
                                         current_time - timestamp <= line_time]

        for i in range(1, len(player.left_hand_track_points)):
            if player.left_hand_track_lengths[i - 1] != 0:
                cv2.line(image, tuple(player.left_hand_track_points[i - 1][0]),
                         tuple(player.left_hand_track_points[i][0]),
                         color, 3)
