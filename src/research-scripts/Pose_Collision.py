import cv2
import numpy as np
import mediapipe as mp
import numpy as np
import random
from shapely.geometry import LineString, Polygon
import traceback
import sys
import math
import time

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

number_of_players = 1
players = []


class Player:
    left_hand_track_points = []
    left_hand_track_lengths = []
    left_hand_track_current = 0
    left_hand_track_previous_point = 0, 0

    right_hand_track_points = []
    right_hand_track_lengths = []
    right_hand_track_current = 0
    right_hand_track_previous_point = 0, 0

    right_foot_track_points = []
    right_foot_track_lengths = []
    right_foot_track_current = 0
    right_foot_track_previous_point = 0, 0

    left_foot_track_points = []
    left_foot_track_lengths = []
    left_foot_track_current = 0
    left_foot_track_previous_point = 0, 0

    score = 0
    spawn_time = time.time()

    def addScore(self, current_time):
        hitTime = (current_time - self.spawn_time)
        self.score += int(100 - hitTime * 5)
        self.spawn_time = time.time()

    def check_hit(self, frame, woodLine):
        for i, point in enumerate(self.left_hand_track_points):  # any track point will do
            if i != 0:
                cv2.line(image, self.left_hand_track_points[i - 1], self.left_hand_track_points[i], (0, 0, 255), 5)
                cv2.line(image, self.right_hand_track_points[i - 1], self.right_hand_track_points[i], (0, 0, 255), 5)
                cv2.line(image, self.right_foot_track_points[i - 1], self.right_foot_track_points[i], (0, 0, 255), 5)
                cv2.line(image, self.left_foot_track_points[i - 1], self.left_foot_track_points[i], (0, 0, 255), 5)

                line_left_hand = LineString([self.left_hand_track_points[i - 1], self.left_hand_track_points[i]])
                line_right_hand = LineString([self.right_hand_track_points[i - 1], self.right_hand_track_points[i]])
                line_right_foot = LineString([self.right_foot_track_points[i - 1], self.right_foot_track_points[i]])
                line_left_foot = LineString([self.left_foot_track_points[i - 1], self.left_foot_track_points[i]])

                # woodLine = LineString([(woodX, woodY), (woodX, woodY+size)])
                if (line_left_hand.intersects(woodLine) or line_right_hand.intersects(woodLine)
                        or line_right_foot.intersects(woodLine) or line_left_foot.intersects(woodLine)):
                    self.left_hand_track_points = []
                    self.left_hand_track_lengths = []

                    self.right_hand_track_points = []
                    self.right_hand_track_lengths = []

                    self.right_foot_track_points = []
                    self.right_foot_track_lengths = []

                    self.left_foot_track_points = []
                    self.left_foot_track_lengths = []
                    return True
                    # hitTime = (time.time() - spawn_time)
                    # print("Hit in " +  str(hitTime) + " seconds")
                    # score += int(100 - hitTime * 5)
                    # spawn_time = time.time()
            # number_of_jabs += 1
        self.left_hand_track_points = self.left_hand_track_points[-2:]
        self.left_hand_track_lengths = self.left_hand_track_lengths[-2:]

        self.right_hand_track_points = self.right_hand_track_points[-2:]
        self.right_hand_track_lengths = self.right_hand_track_lengths[-2:]

        self.right_foot_track_points = self.right_foot_track_points[-2:]
        self.right_foot_track_lengths = self.right_foot_track_lengths[-2:]

        self.left_foot_track_points = self.left_foot_track_points[-2:]
        self.left_foot_track_lengths = self.left_foot_track_lengths[-2:]
        return False


for i in range(number_of_players):
    players.append(Player())


def calculate_angle(first_point, mid_point, end_point):
    first_point = np.array(first_point)
    mid_point = np.array(mid_point)
    end_point = np.array(end_point)

    radians = np.arctan2(end_point[1] - mid_point[1], end_point[0] - mid_point[0]) - np.arctan2(
        first_point[1] - mid_point[1], first_point[0] - mid_point[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180:
        angle = 360 - angle
    return angle


video_capture = cv2.VideoCapture(0)
video_capture.set(3, 880)
video_capture.set(4, 720)
# jab counter variable
number_of_jabs = 0
stage = "hit"
# Houten plank
wood = cv2.imread('resources/plank.jpg')
size = 80
wood = cv2.resize(wood, (size, size), interpolation=cv2.INTER_LINEAR)
img2gray = cv2.cvtColor(wood, cv2.COLOR_BGR2GRAY)
ret, mask = cv2.threshold(img2gray, 1, 255, cv2.THRESH_BINARY)

# Random plank coördinaten
width = int(video_capture.get(3))
height = int(video_capture.get(4))
woodX = random.randint(100, width - 110)
woodY = random.randint(100, 300)
print(woodX)
print(woodY)
woodLine = Polygon([(woodX, woodY), (woodX, woodY + size), (woodX + size, woodY), (woodX + size, woodY + size)])

spawn_time = time.time()
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    # terwijl de feed open is vernieuw de frames
    while video_capture.isOpened():

        # geeft de current read van de webcame aan frame en de return variable
        ret, frame = video_capture.read()
        frame = cv2.flip(frame, 1)
        # herkleur de foto naar RGB ipv BGR by default is die in opencv in BGR
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # haalt landmarks(coordinaten bepaalde delen lichaam) op
        try:
            # haal coordinaten op
            landmarks = result.pose_landmarks.landmark

            # krijgt coordinaten van lichaamsdelen
            # left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            # left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
            # left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]

            # left_shoulder_xy = [left_shoulder.x, left_shoulder.y]
            # left_elbow_xy = [left_elbow.x, left_elbow.y]
            # left_wrist_xy = [left_wrist.x, left_wrist.y]

            # #berekent hoek van de bepaalde lichaamsdelen
            # angle = calculate_angle(left_shoulder_xy, left_elbow_xy, left_wrist_xy)

            # stuurt angle naar beeld op de plek van de elleboog
            # cv2.putText(image, str(angle),
            #               tuple(np.multiply(left_elbow_xy, [640, 480]).astype(int)), 
            #              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
            #                    )
            # Still only for 1 player
            for player in players:

                # Set previous coordinates (previous x (px) and previosu y (py)) for the limbs
                px_left, py_left = player.left_hand_track_previous_point
                px_right, py_right = player.right_hand_track_previous_point
                px_right_foot, py_right_foot = player.right_foot_track_previous_point
                px_left_foot, py_left_foot = player.left_foot_track_previous_point

                # set current coordinates (current x (cx) and current y (cy)) for the limbs
                cx_left, cy_left = int(landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].x * width), int(
                    landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].y * height)
                cx_right, cy_right = int(landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].x * width), int(
                    landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].y * height)
                cx_right_foot, cy_right_foot = int(landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].x * width), int(
                    landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].y * height)
                cx_left_foot, cy_left_foot = int(landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].x * width), int(
                    landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].y * height)

                # print("X: " + str(cx_left) + "Y: " + str(cy_left))
                # Calculate distance between each hand's coordinates
                distance_left_hand = math.hypot(cx_left - px_left, cy_left - py_left)
                distance_right_hand = math.hypot(cx_right - px_right, cy_right - py_right)
                distance_right_foot = math.hypot(cx_right_foot - px_right_foot, cy_right_foot - py_right_foot)
                distance_left_foot = math.hypot(cx_left_foot - px_left_foot, cy_left_foot - py_left_foot)

                player.left_hand_track_points.append([cx_left, cy_left])
                player.right_hand_track_points.append([cx_right, cy_right])
                player.right_foot_track_points.append([cx_right_foot, cy_right_foot])
                player.left_foot_track_points.append([cx_left_foot, cy_left_foot])

                player.left_hand_track_lengths.append(distance_left_hand)
                player.right_hand_track_lengths.append(distance_right_hand)
                player.right_foot_track_lengths.append(distance_right_foot)
                player.left_foot_track_lengths.append(distance_left_foot)

                player.left_hand_track_current += distance_left_hand
                player.right_hand_track_current += distance_right_hand
                player.right_foot_track_current += distance_right_foot
                player.left_foot_track_current += distance_left_foot

                player.left_hand_track_previous_point = cx_left, cy_left
                player.right_hand_track_previous_point = cx_right, cy_right
                player.right_foot_track_previous_point = cx_right_foot, cy_right_foot
                player.left_foot_track_previous_point = cx_left_foot, cy_left_foot

                if (player.check_hit(frame, woodLine)):  # if hit is registered, reset wood placement and add score
                    woodX = random.randint(100, width - 110)
                    woodY = random.randint(100, 300)
                    woodLine = Polygon(
                        [(woodX, woodY), (woodX, woodY + size), (woodX + size, woodY), (woodX + size, woodY + size)])
                    player.addScore(time.time())
            # px,py = track_previous_point
            # cx,cy = int(landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].x * width), int(landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].y *height )
            # print("X: " + str(cx) + " Y: " + str(cy))
            # track_points.append([cx,cy])
            # distance = math.hypot(cx-px, cy-py)
            # track_lengths.append(distance)
            # track_current += distance
            # track_previous_point = cx,cy

            # if angle > 120 and stage == "hit" and left_wrist.visibility > 0.5 and left_elbow.visibility > 0.5:
            #     stage = "stretched"
            # #if angle < 20 and stage == "stretched":
            # #    stage = "hit"
            # for i, point in enumerate(track_points):
            #     if i != 0:
            #         cv2.line(image, track_points[i-1], track_points[i], (0,0,255),5)
            #         line = LineString([track_points[i-1], track_points[i]])
            #         #woodLine = LineString([(woodX, woodY), (woodX, woodY+size)])
            #         if(angle < 20 and stage == "stretched" and line.intersects(woodLine)):
            #             print("Intersects!")
            #             stage = "hit"
            #             number_of_jabs += 1
            #             track_points = []
            #             track_lengths = []
            #             woodX=random.randint(100, width-160)
            #             woodY=random.randint(400, height-160)
            #             woodLine = Polygon([(woodX, woodY), (woodX, woodY+size),(woodX +size, woodY), (woodX +size, woodY +size)])
            #             #hitTime = (time.time() - spawn_time)
            #             #print("Hit in " +  str(hitTime) + " seconds")
            #             #score += int(100 - hitTime * 5)  
            #             #spawn_time = time.time()
            #     #number_of_jabs += 1
            # track_points = track_points[-2:]
            # track_lengths = track_lengths[-2:]

            # cv2.putText(image, "Stage: " + stage + " " + str(int(number_of_jabs)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
            for player in players:
                cv2.putText(image, "Score: " + str(player.score), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        except Exception:
            print(traceback.format_exc())

        # zet writeable op false om ervoor te zorgen dat de image beter procest
        image.flags.writeable = False

        # detecteert het daadwerkelijke persoon en slaat het op in result
        result = pose.process(image)

        # writeable weer terugzetten
        image.flags.writeable = True
        # goede kleeurcode weer goed terugzetten
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        roi = image[woodY:woodY + size, woodX:woodX + size]
        # Set an index of where the mask is
        roi[np.where(mask)] = 0
        roi += wood
        # cv2.line(frame, (woodX, woodY), (woodX, woodY+size), (0,255,0), 2)
        cv2.rectangle(image, (woodX, woodY), (woodX + size, woodY + size), (0, 255, 0), 2)

        # render lichaam detectie
        # mp_drawing.draw_landmarks(image, result.pose_landmarks, mp_pose.POSE_CONNECTIONS,
        #    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
        #    mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2),)

        # laat de webcame frames zien met als titel webcam
        cv2.imshow('webcam', image)

        # als je op q klikt sluit t programma
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
video_capture.release()
cv2.destroyAllWindows()
