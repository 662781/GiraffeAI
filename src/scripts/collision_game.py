import cv2
import numpy as np
import mediapipe as mp
import time
import random

# Camera en handen
cap = cv2.VideoCapture(0)
mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils
  
#Houten plank
wood = cv2.imread('resources/wood.png')
size = 100
wood = cv2.resize(wood, (60, 60), interpolation=cv2.INTER_LINEAR)
img2gray = cv2.cvtColor(wood, cv2.COLOR_BGR2GRAY)
ret, mask = cv2.threshold(img2gray, 1, 255, cv2.THRESH_BINARY)

previousTime = 0
currentTime = 0

# Bereken random plaatsing van het hout met camera W en H
width  = int(cap.get(3))  
height = int(cap.get(4)) 
woodX=random.randint(100, width-60)
woodY=random.randint(100, height-60)
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(imgRGB)
    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            for id, lm in enumerate(handLms.landmark):
                #print(id, lm)
                X=lm.x*width
                Y=lm.y*height
                if X > woodX and X < (woodX+20) and  Y > woodY and Y <(woodY+40):
                    print("Wood has been hit")
                    woodX=random.randint(100, width-60)
                    woodY=random.randint(100, height-60)
                    #print(lm.x)
            mpDraw.draw_landmarks(frame, handLms, mpHands.HAND_CONNECTIONS)


    # Region of Image https://stackoverflow.com/a/58177717/12464999 dit antwoord legt het best goed uit
    roi = frame[-size-10:-10, -size-10:-10]
    roi = frame[woodY:woodY+60,woodX:woodX+60]
    # Set an index of where the mask is
    roi[np.where(mask)] = 0
    roi += wood
    
     
    currentTime = time.time()
    fps = 1/(currentTime-previousTime)
    previousTime = currentTime
    cv2.putText(frame, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)


    cv2.imshow('WebCam', frame)
    if cv2.waitKey(1) == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()