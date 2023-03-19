import cv2
import numpy as np
import random
import traceback
import mediapipe as mp

# Open the camera
cap = cv2.VideoCapture(0)
cap.set(3, 1920)
cap.set(4, 1080)
players = 2
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

wood = cv2.imread('resources/wood.png')
size = 80
wood = cv2.resize(wood, (size, size), interpolation=cv2.INTER_LINEAR)
img2gray = cv2.cvtColor(wood, cv2.COLOR_BGR2GRAY)
ret, mask = cv2.threshold(img2gray, 1, 255, cv2.THRESH_BINARY)

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while True:
        rval, frame = cap.read()

        h, w, channels = frame.shape
        half = w//2

        split_frames = np.split(frame, players, axis=1)
        # for i in range(players):
        for i, split_frame in enumerate(split_frames):
            frame_height, frame_width, frame_channels = split_frame.shape
            woodX=random.randint(100, frame_width-110)
            woodY=random.randint(100, frame_height-300)
                #haalt landmarks(coordinaten bepaalde delen lichaam) op
            try:
                #haal coordinaten op
                landmarks = result.pose_landmarks.landmark
                # Still only for 1 player

            
            except Exception:
                print(traceback.format_exc())
                
            #zet writeable op false om ervoor te zorgen dat de image beter procest
            split_frame.flags.writeable = False

            #detecteert het daadwerkelijke persoon en slaat het op in result
            result = pose.process(split_frame.copy())

            #writeable weer terugzetten
            split_frame.flags.writeable = True
            #goede kleeurcode weer goed terugzetten
            #split_frame = cv2.cvtColor(split_frame, cv2.COLOR_RGB2BGR)
            #render lichaam detectie
            mp_drawing.draw_landmarks(split_frame, result.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2),)

            cv2.imshow(f'split frame {i}', split_frame)
        # full_frame = cv2.hconcat(split_frames)
        #print("FPS: " + str(int(cap.get(cv2.CAP_PROP_FPS))))

        #cv2.imshow("full",frame)

        key = cv2.waitKey(20)
        if key == 27: # exit on ESC
            break

cv2.destroyWindow("preview")
cap.release()



   