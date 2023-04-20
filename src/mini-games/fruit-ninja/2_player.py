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
mp_pose2 = mp.solutions.pose
mp_poses = [mp_pose, mp_pose2]

number_of_players = 2
players = []

class Player:
    left_hand_track_points = []
    left_hand_track_lengths = []
    left_hand_track_current = 0
    left_hand_track_previous_point = 0,0
    
    right_hand_track_points = []
    right_hand_track_lengths = []
    right_hand_track_current = 0
    right_hand_track_previous_point = 0,0

    right_foot_track_points = []
    right_foot_track_lengths = []
    right_foot_track_current = 0
    right_foot_track_previous_point = 0,0

    left_foot_track_points = []
    left_foot_track_lengths = []
    left_foot_track_current = 0
    left_foot_track_previous_point = 0,0

    score = 0
    spawn_time = time.time()

    def addScore(self, current_time):
        hitTime = (current_time - self.spawn_time)
        self.score += int(100 - hitTime * 5) 
        self.spawn_time = time.time()

    def draw_tracking_lines(self, image):
        return
        cv2.line(image, self.left_hand_track_points[i-1], self.left_hand_track_points[i], (0,0,255),2)
        cv2.line(image, self.right_hand_track_points[i-1], self.right_hand_track_points[i], (0,0,255),2)
        cv2.line(image, self.right_foot_track_points[i-1], self.right_foot_track_points[i], (0,0,255),2)
        cv2.line(image, self.left_foot_track_points[i-1], self.left_foot_track_points[i], (0,0,255),2)

    def check_hit(self, frame, woodLine):
        for i, point in enumerate(self.left_hand_track_points): # any track point will do
                if i != 0:
                    cv2.line(image, self.left_hand_track_points[i-1], self.left_hand_track_points[i], (0,0,255),5)
                    cv2.line(image, self.right_hand_track_points[i-1], self.right_hand_track_points[i], (0,0,255),5)
                    cv2.line(image, self.right_foot_track_points[i-1], self.right_foot_track_points[i], (0,0,255),5)
                    cv2.line(image, self.left_foot_track_points[i-1], self.left_foot_track_points[i], (0,0,255),5)

                    line_left_hand = LineString([self.left_hand_track_points[i-1], self.left_hand_track_points[i]])
                    line_right_hand = LineString([self.right_hand_track_points[i-1], self.right_hand_track_points[i]])
                    line_right_foot = LineString([self.right_foot_track_points[i-1], self.right_foot_track_points[i]])
                    line_left_foot = LineString([self.left_foot_track_points[i-1], self.left_foot_track_points[i]])

                    #woodLine = LineString([(woodX, woodY), (woodX, woodY+size)])
                    if(line_left_hand.intersects(woodLine) or line_right_hand.intersects(woodLine) 
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
                        #hitTime = (time.time() - spawn_time)
                        #print("Hit in " +  str(hitTime) + " seconds")
                        #score += int(100 - hitTime * 5)  
                        #spawn_time = time.time()
                #number_of_jabs += 1
        self.left_hand_track_points = self.left_hand_track_points[-2:]
        self.left_hand_track_lengths = self.left_hand_track_lengths [-2:]

        self.right_hand_track_points = self.right_hand_track_points[-2:]
        self.right_hand_track_lengths = self.right_hand_track_lengths[-2:]

        self.right_foot_track_points = self.right_foot_track_points[-2:]
        self.right_foot_track_lengths = self.right_foot_track_lengths[-2:]

        self.left_foot_track_points = self.left_foot_track_points[-2:]
        self.left_foot_track_lengths = self.left_foot_track_lengths[-2:]
        return False

def draw_stick_figure(
        image,
        landmarks,
        color=(100, 33, 3),
        bg_color=(255, 255, 255),
        visibility_th=0.5,
):
    image_width, image_height = image.shape[1], image.shape[0]

    # 各ランドマーク算出
    landmark_point = []
    for index, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        landmark_z = landmark.z
        landmark_point.append(
            [index, landmark.visibility, (landmark_x, landmark_y), landmark_z])

    # 脚の付け根の位置を腰の中点に修正
    right_leg = landmark_point[23]
    left_leg = landmark_point[24]
    leg_x = int((right_leg[2][0] + left_leg[2][0]) / 2)
    leg_y = int((right_leg[2][1] + left_leg[2][1]) / 2)

    landmark_point[23][2] = (leg_x, leg_y)
    landmark_point[24][2] = (leg_x, leg_y)

    # 距離順にソート
    sorted_landmark_point = sorted(landmark_point,
                                   reverse=True,
                                   key=lambda x: x[3])

    # 各サイズ算出
    (face_x, face_y), face_radius = min_enclosing_face_circle(landmark_point)

    face_x = int(face_x)
    face_y = int(face_y)
    face_radius = int(face_radius * 1.5)

    stick_radius01 = int(face_radius * (4 / 5))
    stick_radius02 = int(stick_radius01 * (3 / 4))
    stick_radius03 = int(stick_radius02 * (3 / 4))

    # 描画対象リスト
    draw_list = [
        11,  # 右腕
        12,  # 左腕
        23,  # 右脚
        24,  # 左脚
    ]

    # 背景色
    #cv2.rectangle(image, (0, 0), (image_width, image_height),
    #             bg_color,
    #             thickness=-1)

    # 顔 描画
    cv2.circle(image, (face_x, face_y), face_radius, color, -1)

    # 腕/脚 描画
    for landmark_info in sorted_landmark_point:
        index = landmark_info[0]

        if index in draw_list:
            point01 = [p for p in landmark_point if p[0] == index][0]
            point02 = [p for p in landmark_point if p[0] == (index + 2)][0]
            point03 = [p for p in landmark_point if p[0] == (index + 4)][0]

            if point01[1] > visibility_th and point02[1] > visibility_th:
                image = draw_stick(
                    image,
                    point01[2],
                    stick_radius01,
                    point02[2],
                    stick_radius02,
                    color=color,
                    bg_color=bg_color,
                )
            if point02[1] > visibility_th and point03[1] > visibility_th:
                image = draw_stick(
                    image,
                    point02[2],
                    stick_radius02,
                    point03[2],
                    stick_radius03,
                    color=color,
                    bg_color=bg_color,
                )

    return image


def min_enclosing_face_circle(landmark_point):
    landmark_array = np.empty((0, 2), int)

    index_list = [1, 4, 7, 8, 9, 10]
    for index in index_list:
        np_landmark_point = [
            np.array(
                (landmark_point[index][2][0], landmark_point[index][2][1]))
        ]
        landmark_array = np.append(landmark_array, np_landmark_point, axis=0)

    center, radius = cv2.minEnclosingCircle(points=landmark_array)

    return center, radius


def draw_stick(
        image,
        point01,
        point01_radius,
        point02,
        point02_radius,
        color=(100, 33, 3),
        bg_color=(255, 255, 255),
):
    cv2.circle(image, point01, point01_radius, color, -1)
    cv2.circle(image, point02, point02_radius, color, -1)

    draw_list = []
    for index in range(2):
        rad = math.atan2(point02[1] - point01[1], point02[0] - point01[0])

        rad = rad + (math.pi / 2) + (math.pi * index)
        point_x = int(point01_radius * math.cos(rad)) + point01[0]
        point_y = int(point01_radius * math.sin(rad)) + point01[1]

        draw_list.append([point_x, point_y])

        point_x = int(point02_radius * math.cos(rad)) + point02[0]
        point_y = int(point02_radius * math.sin(rad)) + point02[1]

        draw_list.append([point_x, point_y])

    points = np.array((draw_list[0], draw_list[1], draw_list[3], draw_list[2]))
    cv2.fillConvexPoly(image, points=points, color=color)

    return image


def draw_landmarks(
    image,
    landmarks,
    # upper_body_only,
    visibility_th=0.5,
):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_point = []

    for index, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        landmark_z = landmark.z
        landmark_point.append([landmark.visibility, (landmark_x, landmark_y)])

        if landmark.visibility < visibility_th:
            continue

        if index >= 0 and index <= 32:
            cv2.circle(image, (landmark_x, landmark_y), 5, (0, 255, 0), 2)

        # if not upper_body_only:
        if True:
            cv2.putText(image, "z:" + str(round(landmark_z, 3)),
                       (landmark_x - 10, landmark_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
                       cv2.LINE_AA)

    # 右目
    if landmark_point[1][0] > visibility_th and landmark_point[2][
            0] > visibility_th:
        cv2.line(image, landmark_point[1][1], landmark_point[2][1],
                (0, 255, 0), 2)
    if landmark_point[2][0] > visibility_th and landmark_point[3][
            0] > visibility_th:
        cv2.line(image, landmark_point[2][1], landmark_point[3][1],
                (0, 255, 0), 2)

    # 左目
    if landmark_point[4][0] > visibility_th and landmark_point[5][
            0] > visibility_th:
        cv2.line(image, landmark_point[4][1], landmark_point[5][1],
                (0, 255, 0), 2)
    if landmark_point[5][0] > visibility_th and landmark_point[6][
            0] > visibility_th:
        cv2.line(image, landmark_point[5][1], landmark_point[6][1],
                (0, 255, 0), 2)

    # 口
    if landmark_point[9][0] > visibility_th and landmark_point[10][
            0] > visibility_th:
        cv2.line(image, landmark_point[9][1], landmark_point[10][1],
                (0, 255, 0), 2)

    # 肩
    if landmark_point[11][0] > visibility_th and landmark_point[12][
            0] > visibility_th:
        cv2.line(image, landmark_point[11][1], landmark_point[12][1],
                (0, 255, 0), 2)

    # 右腕
    if landmark_point[11][0] > visibility_th and landmark_point[13][
            0] > visibility_th:
        cv2.line(image, landmark_point[11][1], landmark_point[13][1],
                (0, 255, 0), 2)
    if landmark_point[13][0] > visibility_th and landmark_point[15][
            0] > visibility_th:
        cv2.line(image, landmark_point[13][1], landmark_point[15][1],
                (0, 255, 0), 2)

    # 左腕
    if landmark_point[12][0] > visibility_th and landmark_point[14][
            0] > visibility_th:
        cv2.line(image, landmark_point[12][1], landmark_point[14][1],
                (0, 255, 0), 2)
    if landmark_point[14][0] > visibility_th and landmark_point[16][
            0] > visibility_th:
        cv2.line(image, landmark_point[14][1], landmark_point[16][1],
                (0, 255, 0), 2)

    # 右手
    if landmark_point[15][0] > visibility_th and landmark_point[17][
            0] > visibility_th:
        cv2.line(image, landmark_point[15][1], landmark_point[17][1],
                (0, 255, 0), 2)
    if landmark_point[17][0] > visibility_th and landmark_point[19][
            0] > visibility_th:
        cv2.line(image, landmark_point[17][1], landmark_point[19][1],
                (0, 255, 0), 2)
    if landmark_point[19][0] > visibility_th and landmark_point[21][
            0] > visibility_th:
        cv2.line(image, landmark_point[19][1], landmark_point[21][1],
                (0, 255, 0), 2)
    if landmark_point[21][0] > visibility_th and landmark_point[15][
            0] > visibility_th:
        cv2.line(image, landmark_point[21][1], landmark_point[15][1],
                (0, 255, 0), 2)

    # 左手
    if landmark_point[16][0] > visibility_th and landmark_point[18][
            0] > visibility_th:
        cv2.line(image, landmark_point[16][1], landmark_point[18][1],
                (0, 255, 0), 2)
    if landmark_point[18][0] > visibility_th and landmark_point[20][
            0] > visibility_th:
        cv2.line(image, landmark_point[18][1], landmark_point[20][1],
                (0, 255, 0), 2)
    if landmark_point[20][0] > visibility_th and landmark_point[22][
            0] > visibility_th:
        cv2.line(image, landmark_point[20][1], landmark_point[22][1],
                (0, 255, 0), 2)
    if landmark_point[22][0] > visibility_th and landmark_point[16][
            0] > visibility_th:
        cv2.line(image, landmark_point[22][1], landmark_point[16][1],
                (0, 255, 0), 2)

    # 胴体
    if landmark_point[11][0] > visibility_th and landmark_point[23][
            0] > visibility_th:
        cv2.line(image, landmark_point[11][1], landmark_point[23][1],
                (0, 255, 0), 2)
    if landmark_point[12][0] > visibility_th and landmark_point[24][
            0] > visibility_th:
        cv2.line(image, landmark_point[12][1], landmark_point[24][1],
                (0, 255, 0), 2)
    if landmark_point[23][0] > visibility_th and landmark_point[24][
            0] > visibility_th:
        cv2.line(image, landmark_point[23][1], landmark_point[24][1],
                (0, 255, 0), 2)

    if len(landmark_point) > 25:
        # 右足
        if landmark_point[23][0] > visibility_th and landmark_point[25][
                0] > visibility_th:
            cv2.line(image, landmark_point[23][1], landmark_point[25][1],
                    (0, 255, 0), 2)
        if landmark_point[25][0] > visibility_th and landmark_point[27][
                0] > visibility_th:
            cv2.line(image, landmark_point[25][1], landmark_point[27][1],
                    (0, 255, 0), 2)
        if landmark_point[27][0] > visibility_th and landmark_point[29][
                0] > visibility_th:
            cv2.line(image, landmark_point[27][1], landmark_point[29][1],
                    (0, 255, 0), 2)
        if landmark_point[29][0] > visibility_th and landmark_point[31][
                0] > visibility_th:
            cv2.line(image, landmark_point[29][1], landmark_point[31][1],
                    (0, 255, 0), 2)

        # 左足
        if landmark_point[24][0] > visibility_th and landmark_point[26][
                0] > visibility_th:
            cv2.line(image, landmark_point[24][1], landmark_point[26][1],
                    (0, 255, 0), 2)
        if landmark_point[26][0] > visibility_th and landmark_point[28][
                0] > visibility_th:
            cv2.line(image, landmark_point[26][1], landmark_point[28][1],
                    (0, 255, 0), 2)
        if landmark_point[28][0] > visibility_th and landmark_point[30][
                0] > visibility_th:
            cv2.line(image, landmark_point[28][1], landmark_point[30][1],
                    (0, 255, 0), 2)
        if landmark_point[30][0] > visibility_th and landmark_point[32][
                0] > visibility_th:
            cv2.line(image, landmark_point[30][1], landmark_point[32][1],
                    (0, 255, 0), 2)
    return image

for i in range(number_of_players):
    players.append(Player())


def calculate_angle(first_point, mid_point, end_point):
    first_point = np.array(first_point)
    mid_point = np.array(mid_point)
    end_point = np.array(end_point)

    radians = np.arctan2(end_point[1]-mid_point[1], end_point[0]-mid_point[0]) - np.arctan2(first_point[1]-mid_point[1], first_point[0] - mid_point[0])
    angle = np.abs(radians*180.0/np.pi)
    if angle > 180:
        angle = 360 - angle
    return angle

video_capture = cv2.VideoCapture(0)
video_capture.set(3, 640)
video_capture.set(4, 480)
#jab counter variable
number_of_jabs = 0
stage = "hit"
# Houten plank
wood = cv2.imread('resources/wood.png')
size = 80
wood = cv2.resize(wood, (size, size), interpolation=cv2.INTER_LINEAR)
img2gray = cv2.cvtColor(wood, cv2.COLOR_BGR2GRAY)
ret, mask = cv2.threshold(img2gray, 1, 255, cv2.THRESH_BINARY)

# Random plank coördinaten
width  = int(video_capture.get(3))  
height = int(video_capture.get(4)) 
woodX=random.randint(100, width-110)
woodY=random.randint(100, 300)
print(woodX)
print(woodY)
woodLine = Polygon([(woodX, woodY), (woodX, woodY+size),(woodX +size, woodY), (woodX +size, woodY +size)  ])
previousTime = 0
currentTime = 0
fps = video_capture.get(cv2.CAP_PROP_FPS)
print("FPS CAMERA: " + str(int(fps)))
spawn_time = time.time()
num_frames = 1

cv2.namedWindow("webcam", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("webcam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

bg_image = cv2.imread("resources/dojo.png")


pose_results = [None, None]
#terwijl de feed open is vernieuw de frames
while video_capture.isOpened():
    start = time.time()
#geeft de current read van de webcame aan frame en de return variable
    ret, frame = video_capture.read()
    frame = cv2.flip(frame,1)
    #herkleur de foto naar RGB ipv BGR by default is die in opencv in BGR
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # split the frame into two halves
    height, width, channels = image.shape
    half_width = int(width / 2)
    left_image = image[:, :half_width, :]
    right_image = image[:, half_width:, :]
    images = [left_image, right_image]
    for playerIndex, player in enumerate(players):

        with mp_poses[playerIndex].Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=0) as pose:
            #haalt landmarks(coordinaten bepaalde delen lichaam) op
            try:
                #haal coordinaten op
                landmarks = pose_results[playerIndex].pose_landmarks.landmark
                # Still only for 1 player

                # Set previous coordinates (previous x (px) and previosu y (py)) for the limbs
                px_left,py_left = player.left_hand_track_previous_point
                px_right,py_right = player.right_hand_track_previous_point
                px_right_foot,py_right_foot = player.right_foot_track_previous_point
                px_left_foot,py_left_foot = player.left_foot_track_previous_point

                # set current coordinates (current x (cx) and current y (cy)) for the limbs
                cx_left,cy_left = int(landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].x * width), int(landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].y *height )
                cx_right,cy_right = int(landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].x * width), int(landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].y *height )
                cx_right_foot,cy_right_foot = int(landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].x * width), int(landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].y *height )
                cx_left_foot,cy_left_foot = int(landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].x * width), int(landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].y *height )
                
                #print("X: " + str(cx_left) + "Y: " + str(cy_left))
                # Calculate distance between each hand's coordinates
                distance_left_hand = math.hypot(cx_left-px_left, cy_left-py_left)
                distance_right_hand = math.hypot(cx_right-px_right, cy_right-py_right)
                distance_right_foot = math.hypot(cx_right_foot-px_right_foot, cy_right_foot-py_right_foot)
                distance_left_foot = math.hypot(cx_left_foot-px_left_foot, cy_left_foot-py_left_foot)

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

                player.left_hand_track_previous_point = cx_left,cy_left
                player.right_hand_track_previous_point = cx_right, cy_right
                player.right_foot_track_previous_point = cx_right_foot, cy_right_foot
                player.left_foot_track_previous_point = cx_left_foot, cy_left_foot


                player.draw_tracking_lines(images[playerIndex])
                if(player.check_hit(frame, woodLine)): # if hit is registered, reset wood placement and add score
                    woodX=random.randint(100, width-110)
                    woodY=random.randint(100, 300)
                    woodLine = Polygon([(woodX, woodY), (woodX, woodY+size),(woodX +size, woodY), (woodX +size, woodY +size)])
                    player.addScore(time.time())
            
            except Exception:
                print(traceback.format_exc())

            #images[playerIndex].flags.writeable = False
            print(playerIndex)
            pose_results[playerIndex] = pose.process(images[playerIndex])
            #images[playerIndex].flags.writeable = True
    #zet writeable op false om ervoor te zorgen dat de image beter procest

    #detecteert het daadwerkelijke persoon en slaat het op in result
    #result = pose.process(image)
    #writeable weer terugzetten
    #image.flags.writeable = True
    #goede kleeurcode weer goed terugzetten
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    # Set background image
    bg_resize_image = cv2.resize(bg_image, (image.shape[1], image.shape[0]))
    
    
    #cv2.line(frame, (woodX, woodY), (woodX, woodY+size), (0,255,0), 2)
    cv2.rectangle(image, (woodX, woodY), (woodX+size, woodY+size), (0,255,0), 2)
    for pose_result in pose_results:        
        #render lichaam detectie
        try:
            image = draw_stick_figure(image, pose_result.pose_landmarks)
        except:
            pass
    # mp_drawing.draw_landmarks(image, result.pose_landmarks, mp_pose.POSE_CONNECTIONS,
    #     mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
    #     mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2),)

    roi = image[woodY:woodY+size,woodX:woodX+size]
    # Set an index of where the mask is
    roi[np.where(mask)] = 0
    roi += wood
    #cv2.putText(frame, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
    #print("FPS: " + str(int(video_capture.get(cv2.CAP_PROP_FPS))))
    #cv2.putText(frame, str(int(fps)), (200, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

    # laat de webcame frames zien met als titel webcam
    end = time.time()
    seconds = end - start
    fps = num_frames / seconds
    seconds = num_frames / fps
    cv2.putText(image, str(fps), (200, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

    cv2.imshow('webcam', image)

    #als je op q klikt sluit t programma
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break
video_capture.release()
cv2.destroyAllWindows()
