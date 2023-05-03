import random
import traceback
import numpy as np
import cv2
import time
from ultralytics import YOLO
from utils import CvFpsCalc
from utils import Generics
from CVNinjaPlayer import CVNinjaPlayer
from shapely.geometry import LineString, Polygon


yolo_model = YOLO('yolov8m-pose.pt')  # load an official model
number_of_players = 1 # todo: argument

players = []
for i in range(number_of_players):
    players.append(CVNinjaPlayer())

camera_width = 640
camera_height = 480

def get_trailing(player, image):
    # return
    for i, point in enumerate(player.left_hand_track_points): # any track point will do
        if i != 0:
            cv2.line(image, player.left_hand_track_points[i-1], player.left_hand_track_points[i], (0,0,255),5)
            cv2.line(image, player.right_hand_track_points[i-1], player.right_hand_track_points[i], (0,0,255),5)
            cv2.line(image, player.right_foot_track_points[i-1], player.right_foot_track_points[i], (0,0,255),5)
            cv2.line(image, player.left_foot_track_points[i-1], player.left_foot_track_points[i], (0,0,255),5)

cap = cv2.VideoCapture(0)
cap.set(3, camera_width)
cap.set(4, camera_height)

cv2.namedWindow("webcam", cv2.WINDOW_NORMAL)
#cv2.setWindowProperty("webcam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cvFpsCalc = CvFpsCalc(buffer_len=10)
current_player = "none"

wood = cv2.imread('resources/wood.png')
size = 80
wood = cv2.resize(wood, (size, size), interpolation=cv2.INTER_LINEAR)
img2gray = cv2.cvtColor(wood, cv2.COLOR_BGR2GRAY)
ret, mask = cv2.threshold(img2gray, 1, 255, cv2.THRESH_BINARY)
woodX=random.randint(100, camera_width-110)
woodY=random.randint(100, 300)
woodLine = Polygon([(woodX, woodY), (woodX, woodY+size),(woodX +size, woodY), (woodX +size, woodY +size)  ])


while cap.isOpened():    
    display_fps = cvFpsCalc.get()
    ret, frame = cap.read()
    if not ret:
      break
    height, width, _ = frame.shape
    # if (number_of_players == 1):
    #     frame = frame[:,100:width-100, :] # singleplayer
    # Recolor Feed from RGB to BGR
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = cv2.flip(image,1)
    #making image writeable to false improves prediction
    image.flags.writeable = False    

    results = yolo_model(image, max_det=number_of_players, verbose=False)
    
    try:
        for i,result in enumerate(results):
            #print("Result: ") todo: debug with person
            keypoints = result.keypoints.cpu().numpy()[0]
            # Depending on the boolean statement, update a person's tracking
            player_index = int(keypoints[2][0]) > (camera_width / number_of_players) 
            players[player_index].update_tracking(keypoints)
            get_trailing(players[player_index], image)

            if(players[player_index].check_hit(image, woodLine)):
                woodX=random.randint(100, width-110)
                woodY=random.randint(100, 300)
                woodLine = Polygon([(woodX, woodY), (woodX, woodY+size),(woodX +size, woodY), (woodX +size, woodY +size)])
                 
    except Exception:
        traceback.print_exc()
        pass

    image = results[0].plot()
    # Recolor image back to BGR for rendering
    image.flags.writeable = True 
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.putText(image, "FPS:" + str(display_fps), (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 

    # cv2.putText(image, current_player, (int(camera_width/2 -20), 30),
    #                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 
    #cv2.line(image, (width // 2,0), (width // 2, height), (0,255,0), 2)
    roi = image[woodY:woodY+size,woodX:woodX+size]
    roi[np.where(mask)] = 0
    roi += wood

    
    cv2.imshow('webcam', image)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
         break

cap.release()
cv2.destroyAllWindows()

