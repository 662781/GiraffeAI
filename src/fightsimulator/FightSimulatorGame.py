import time
import cv2
import mediapipe as mp
import numpy as np
import math
import random
import threading

from shared.model import CVGame
from shared.utils import Generics, CVAssets

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


class FightSimulatorGame(CVGame):
    """
        A class representing a fight simulator game.

        Attributes:
            mp_drawing (module): mediapipe drawing utilities module.
            mp_pose (module): mediapipe pose module.
            pose_model: mediapipe pose model.
            number_of_players (int): number of players in the game.
            players (list): list of Player objects representing the players.
            min_visiblity (float): minimum visibility threshold for landmarks.
            cooldown_duration (int): duration of the cooldown between punches in seconds.
            last_punch_time (float): timestamp of the last punch.
            uppercut_timer (float): timer for tracking uppercut punches.
            hook_timer (float): timer for tracking hook punches.
            punch_types (list): list of available punch types.
            selected_punch (str): currently selected punch type.
            elapsed_time (float): elapsed time since the game started.
            video_capture: OpenCV VideoCapture object for capturing video frames.
            combined_points (int): combined points of all players.
            previous_combined_points (int): previous combined points for comparison.
            is_game_started (bool): flag indicating if the game has started.
            game_duration (int): duration of the game in seconds.
        """

    def __init__(self):
        super().__init__()
        self.time_since_last_selected_punch = 0
        self.punch_select_time = time.time()
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
        self.video_capture = cv2.VideoCapture(0)
        self.combined_points = 0
        self.previous_combined_points = -1
        self.is_game_started = False
        self.game_duration = 60

    def setup(self, options):
        """
        Set up the game with the given options.

        Args:
            options: game options.
        """
        self.options = options
        self.time_since_last_selected_punch = time.time() - self.punch_select_time
        self.start_time = time.time()
        self.elapsed_time = time.time() - self.start_time

    def update(self, frame):
        """
        Update the game state based on the current frame.

        Args:
            frame: current frame from the video capture.

        Returns:
            updated frame with visual elements.
        """
        global angle, left_elbow_xy
        self.create_players()
        self.time_since_last_selected_punch = time.time()

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        landmarks = self.pose_model.process(image)

        if not self.is_game_started:
            self.check_for_game_stop()
            self.check_for_game_start()
            return self.draw_play_button(image)

        self.check_and_select_punch()

        if landmarks.pose_landmarks is not None:
            left_shoulder_xy, left_elbow_xy, left_wrist_xy, left_wrist_visibility, left_elbow_visibility = self.get_landmarks(
                landmarks)

            width, height = image.shape[1], image.shape[0]

            self.track_left_hand(player=self.players[0], landmarks=landmarks.pose_landmarks.landmark,
                                 width=width, height=height)

            angle = self.calculate_angle(first_point=left_shoulder_xy, mid_point=left_elbow_xy,
                                         end_point=left_wrist_xy)

            self.start_punch_detection_thread(player=self.players[0], angle=angle,
                                              left_wrist_visibility=left_wrist_visibility,
                                              left_elbow_visibility=left_elbow_visibility)

            self.elapsed_time = time.time() - self.start_time

            self.check_for_game_stop()

            return self.draw_on_frame(image=image, angle=angle, left_elbow_xy=left_elbow_xy, results=landmarks,
                                      player=self.players[0])
        else:
            return frame

    def check_for_game_start(self):
        """
        Check for the start of the game.
        """
        if cv2.waitKey(1) & 0xFF == ord('s'):
            self.start_time = time.time()
            self.is_game_started = True

    def cleanup(self):
        """
        Clean up the game resources.
        """
        super().cleanup()

    class Player:
        """
        Initialize a new Player object.
        """

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

    def check_for_game_stop(self):
        """
        Check for the end of the game.
        """
        if cv2.waitKey(1) & 0xFF == ord('q') or self.elapsed_time > self.game_duration:
            self.should_switch = True
            self.next_game = "Main Menu"

    @staticmethod
    def draw_play_button(image):
        """
        Draw the play button on the image.

        Args:
            image (numpy.ndarray): Image to draw the play button on.

        Returns:
            numpy.ndarray: Image with the play button.
        """
        image = Generics.put_text_with_custom_font(image=image, text="Hold 'S' to start the game,",
                                                   position=(110, 80),
                                                   font_path=CVAssets.FONT_FRUIT_NINJA, font_size=35,
                                                   font_color=(255, 0, 0), outline_color=(0, 0, 0), outline_width=2)

        image = Generics.put_text_with_custom_font(image=image, text="Be Ready!",
                                                   position=(110, 110),
                                                   font_path=CVAssets.FONT_FRUIT_NINJA, font_size=35,
                                                   font_color=(248, 210, 62), outline_color=(0, 0, 0), outline_width=2)

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image

    def check_and_select_punch(self):
        """
        Check if the user has selected a punch type and update the selected punch accordingly.
        """
        if self.get_time_difference() > 5:
            self.punch_select_time = time.time()
            self.select_random_punch()
            print("time difference", self.get_time_difference())

        if self.combined_points != self.previous_combined_points:
            self.select_random_punch()
            self.previous_combined_points = self.combined_points

    def select_random_punch(self):
        """
        Select a random punch type based on the probabilities. The probabilities are as follows:
        1. Jab: 4/6
        2. Uppercut: 1/6
        3. Hook: 1/6
        """
        probabilities = [4, 1, 1]

        weighted_punches = []
        for i, punch in enumerate(self.punch_types):
            weighted_punches.extend([punch] * probabilities[i])

        random_punch = random.choice(weighted_punches)
        self.selected_punch = random_punch

    def start_punch_detection_thread(self, player, angle, left_wrist_visibility, left_elbow_visibility):
        punch_detection_thread = threading.Thread(target=self.detect_punch,
                                                  args=(player, angle, left_wrist_visibility, left_elbow_visibility))
        punch_detection_thread.start()

    def get_time_difference(self):
        return self.time_since_last_selected_punch - self.punch_select_time

    @staticmethod
    def get_moving_average(points, number_of_last_points):
        """
        Calculate the moving average of a list of points.

        Args:
            points (list): List of points.
            number_of_last_points (int): Number of last points to consider.

        returns:
            int: Moving average value.
        """
        if len(points) < number_of_last_points:
            return points[-1][0]  # Return the last point if not enough points are available

        sum_x = sum(point[0][0] for point in points[-number_of_last_points:])
        sum_y = sum(point[0][1] for point in points[-number_of_last_points:])

        return int(sum_x / number_of_last_points), int(sum_y / number_of_last_points)

    def get_direction(self, player, number_of_points_to_track):
        """
        Calculate the direction based on the tracked points.

        Args:
            player (FightSimulatorGame.Player): Player object.
            number_of_points_to_track (int): Number of points to track.

        Returns:
            tuple: Direction values (dx, dy).
        """
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
        """
        Track the left hand movement of a player.

        Args:
            player (FightSimulatorGame.Player): Player object.
            landmarks (list): List of landmarks detected in the frame.
            width (int): Width of the image.
            height (int): Height of the image.
        """
        min_detection_accuracy = 0.7
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

    @staticmethod
    def calculate_angle(first_point: list, mid_point: list, end_point: list):
        """
        Calculate the angle between the shoulder, elbow, and wrist landmarks.

        Args:
            first_point: x and y coordinates of the shoulder landmark.
            mid_point: x and y coordinates of the elbow landmark.
            end_point: x and y coordinates of the wrist landmark.

        Returns:
            angle: angle in degrees.
        """
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
        """
        Get the landmarks of interest from the results.

        Args:
            results: Results from the pose model.

        Returns:
            tuple: Landmark coordinates and visibility values.
        """
        left_shoulder = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        left_elbow = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
        left_wrist = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST.value]

        left_shoulder_xy = [left_shoulder.x, left_shoulder.y]
        left_elbow_xy = [left_elbow.x, left_elbow.y]
        left_wrist_xy = [left_wrist.x, left_wrist.y]

        return left_shoulder_xy, left_elbow_xy, left_wrist_xy, left_wrist.visibility, left_elbow.visibility

    def detect_punch(self, player, angle, left_wrist_visibility, left_elbow_visibility):
        """
        Detect and handle punches based on the angle and visibility values.

        Args:
            player (FightSimulatorGame.Player): Player object.
            angle (float): Angle between the shoulder, elbow, and wrist landmarks.
            left_wrist_visibility (float): Visibility value of the left wrist landmark.
            left_elbow_visibility (float): Visibility value of the left elbow landmark.
        """
        dx, dy = self.get_direction(player=player, number_of_points_to_track=2)

        if time.time() - self.last_punch_time >= self.cooldown_duration:
            if left_wrist_visibility > self.min_visiblity and left_elbow_visibility > self.min_visiblity:
                punch_threads = []

                jab_thread = threading.Thread(target=self.detect_jab, args=(angle, dx, dy, player))
                punch_threads.append(jab_thread)

                uppercut_thread = threading.Thread(target=self.detect_uppercut, args=(angle, dy, player))
                punch_threads.append(uppercut_thread)

                hook_thread = threading.Thread(target=self.detect_hook, args=(angle, dx, dy, player))
                punch_threads.append(hook_thread)

                for thread in punch_threads:
                    thread.start()

                for thread in punch_threads:
                    thread.join()

    def detect_uppercut(self, angle, dy, player):
        """
        Detect and handle uppercut punches based on the angle and direction values.

        Args:
            angle (float): Angle between the shoulder, elbow, and wrist landmarks.
            dy (float): Vertical direction value.
            player (FightSimulatorGame.Player): Player object.
        """
        if 20 < angle < 160 and dy < 0:
            if self.uppercut_timer >= 0.5:
                print("uppercut")
                if self.selected_punch == "uppercut":
                    player.points += 1
                    self.combined_points += 1
                self.uppercut_timer = 0
                self.last_punch_time = time.time()
            else:
                self.uppercut_timer += time.time() - self.uppercut_timer
        else:
            self.uppercut_timer = 0

    def detect_hook(self, angle, dx, dy, player):
        """
        Detect and handle hook punches based on the angle and direction values.

        Args:
            angle (float): Angle between the shoulder, elbow, and wrist landmarks.
            dx (float): Horizontal direction value.
            dy (float): Vertical direction value.
            player (FightSimulatorGame.Player): Player object.
        """
        if 40 < angle < 170 and (abs(dx) ** 2) > (abs(dy) ** 2):
            if self.hook_timer >= 0.1:
                if self.selected_punch == "hook":
                    player.points += 1
                    self.combined_points += 1
                self.hook_timer = 0
                self.last_punch_time = time.time()
            else:
                self.hook_timer += time.time() - self.hook_timer
        else:
            self.hook_timer = 0

    def detect_jab(self, angle, dx, dy, player):
        """
        Detect and handle jab punches based on the angle and direction values.

        Args:
            angle (float): Angle between the shoulder, elbow, and wrist landmarks.
            dx (float): Horizontal direction value.
            dy (float): Vertical direction value.
            player (FightSimulatorGame.Player): Player object.
        """
        if angle > 100 and (abs(dy) ** 2) < (abs(dx) ** 2):
            print("jab")
            if self.selected_punch == "jab":
                player.points += 1
                self.combined_points += 1
                self.last_punch_time = time.time()

    def draw_on_frame(self, image, angle, left_elbow_xy, results, player):
        """
        Draw visual elements on the frame.

        Args:
            image (numpy.ndarray): Frame image.
            angle (float): Angle between the shoulder, elbow, and wrist landmarks.
            left_elbow_xy (tuple): X and Y coordinates of the left elbow landmark.
            results: Results from the pose model.
            player (FightSimulatorGame.Player): Player object.

        Returns:
            numpy.ndarray: Updated frame image with visual elements.
        """
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

        image = Generics.put_text_with_custom_font(image=image,
                                                   text=f"time left: {self.game_duration + 1 - self.elapsed_time:.0f}",
                                                   position=(420, 10), font_path=CVAssets.FONT_FRUIT_NINJA,
                                                   font_size=30, font_color=(205, 127, 50), outline_color=(0, 0, 0),
                                                   outline_width=2)

        self.mp_drawing.draw_landmarks(image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                                       self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                       self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2,
                                                                   circle_radius=2), )
        # self.draw_snake_line(image=image, player=player, color=(0, 255, 0))

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image

    def create_players(self):
        """
        Create player objects based on the number of players in the game.
        """
        for i in range(self.number_of_players):
            self.players.append(self.Player())

    @staticmethod
    def draw_snake_line(image, player, color):
        """
        Draw a snake-like line based on the player's hand movement.

        Args:
            image (numpy.ndarray): Frame image.
            player (FightSimulatorGame.Player): Player object.
            color (tuple): Color of the line.
        """
        line_time = 3
        current_time = time.time()
        player.left_hand_track_points = [(point, timestamp) for point, timestamp in player.left_hand_track_points if
                                         current_time - timestamp <= line_time]

        for i in range(1, len(player.left_hand_track_points)):
            if player.left_hand_track_lengths[i - 1] != 0:
                cv2.line(image, tuple(player.left_hand_track_points[i - 1][0]),
                         tuple(player.left_hand_track_points[i][0]),
                         color, 3)
