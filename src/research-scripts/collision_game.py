import cv2
import numpy as np
import mediapipe as mp
import time
import random
import math
from shapely.geometry import LineString, Polygon

# Camera en handen
cap = cv2.VideoCapture(0)
mpHands = mp.solutions.hands
hands = mpHands.Hands(static_image_mode=True, max_num_hands=1)
mpDraw = mp.solutions.drawing_utils

# Houten plank
wood = cv2.imread('resources/plank.jpg')
size = 80
wood = cv2.resize(wood, (size, size), interpolation=cv2.INTER_LINEAR)
img2gray = cv2.cvtColor(wood, cv2.COLOR_BGR2GRAY)
ret, mask = cv2.threshold(img2gray, 1, 255, cv2.THRESH_BINARY)

previousTime = 0
currentTime = 0
cap.set(3, 720)
cap.set(4, 680)
# Bereken random plaatsing van het hout met camera W en H
width = int(cap.get(3))
height = int(cap.get(4))
woodX = random.randint(100, width - 160)
woodY = random.randint(100, height - 160)
woodLine = Polygon([(woodX, woodY), (woodX, woodY + size), (woodX + size, woodY), (woodX + size, woodY + size)])
track_points = []
track_lengths = []
track_current = 0
track_previous_point = 0, 0
spawn_time = time.time()

score = 0
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(imgRGB)
    if result.multi_hand_landmarks:

        for handLms in result.multi_hand_landmarks:

            # tracking, currently only usable for one hand. If we can get intersection detection, it will help a lot with collision detection
            px, py = track_previous_point
            cx, cy = int(handLms.landmark[9].x * width), int(handLms.landmark[9].y * height)
            track_points.append([cx, cy])
            distance = math.hypot(cx - px, cy - py)
            track_lengths.append(distance)
            track_current += distance
            track_previous_point = cx, cy

            for i, point in enumerate(track_points):
                if i != 0:
                    cv2.line(frame, track_points[i - 1], track_points[i], (0, 0, 255), 5)
                    line = LineString([track_points[i - 1], track_points[i]])
                    # woodLine = LineString([(woodX, woodY), (woodX, woodY+size)])

                    if (line.intersects(woodLine)):
                        print("Intersects!")

                        track_points = []
                        track_lengths = []
                        woodX = random.randint(100, width - 160)
                        woodY = random.randint(100, height - 160)
                        woodLine = Polygon([(woodX, woodY), (woodX, woodY + size), (woodX + size, woodY),
                                            (woodX + size, woodY + size)])
                        hitTime = (time.time() - spawn_time)
                        print("Hit in " + str(hitTime) + " seconds")
                        score += int(100 - hitTime * 5)
                        spawn_time = time.time()

            # if X > woodX and X < (woodX+20) and  Y > woodY and Y <(woodY+40):
            #            print("Wood has been hit")
            # --- todo: refactor into a method for

            # for id, lm in enumerate(handLms.landmark):
            #     #print(id, lm)
            #     X=lm.x*width
            #     Y=lm.y*height
            #     if X > woodX and X < (woodX+20) and  Y > woodY and Y <(woodY+40):
            #         #print("Wood has been hit")
            #         track_points = []
            #         track_lengths = []
            #         woodX=random.randint(100, width-size)
            #         woodY=random.randint(100, height-size)
            # print(lm.x)
            # print(handLms.landmark[5].x)
            # mpDraw.draw_landmarks(frame, handLms, mpHands.HAND_CONNECTIONS)

    # Region of Image https://stackoverflow.com/a/58177717/12464999 dit antwoord legt het best goed uit
    # roi = frame[-size-10:-10, -size-10:-10]
    roi = frame[woodY:woodY + size, woodX:woodX + size]

    # Set an index of where the mask is
    roi[np.where(mask)] = 0
    roi += wood
    # cv2.line(frame, (woodX, woodY), (woodX, woodY+size), (0,255,0), 2)
    cv2.rectangle(frame, (woodX, woodY), (woodX + size, woodY + size), (0, 255, 0), 2)

    currentTime = time.time()
    fps = 1 / (currentTime - previousTime)
    previousTime = currentTime
    cv2.putText(frame, "Score: " + str(score), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

    cv2.imshow('WebCam', frame)
    if cv2.waitKey(1) == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
