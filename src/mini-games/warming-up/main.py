from ultralytics import YOLO
import cv2
import torch
import time
import pprint
from models.game_menu import GameMenu
from services.fps_counter_service import FPSCounterService
from services.player_service import PlayerService

# Load the custom YOLOv8 model
model = YOLO('dl-model/yolov8n-pose.pt')  # load a pretrained model (recommended for training)
# Use CUDA, AKA the GPU
#model.to('cuda')

players = []
score = 0
# Time in minutes to compete for points in the chosen exercise game
timer = 240
# Check which exercise is chosen (Push-Up, Sit-Up, Jumping Jack, Squat, Remix (all at once))
exercise = GameMenu.chosen_exercise

# Capture video frames with "camera 0"
cap = cv2.VideoCapture(0)

# Set the window to full screen
cv2.namedWindow("Warming-Up | CV DOJO", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Warming-Up | CV DOJO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

#print(torch.cuda.is_available())

while cap.isOpened():
    # Read frame
    ret, frame = cap.read()

    # Break loop if video ends
    if not ret:
        break

    # Show FPS in the CV Window
    FPSCounterService.show_fps(frame, time.time(), FPSCounterService)

    # Process frame and put it through the model (what activity / pose is detected, how many people)
    # This can currently only classify people
    results = model(frame)

    # Assign all detected people to a Player class (with e.g. a current_score and high_score)

    # Split the CV window into multiple frames for each player

    # Draw the keypoints (only for testing) and add class name to visualize the current detected activity / pose of all players in the CV window
    # Draws the bounding box & keypoints from the YOLOv8 model
    annotated_frame = results[0].plot()
    
    # Start keeping score of the chosen exercise for each player. Add the score to each players total.

    keypoints = results[0].keypoints.squeeze().tolist()
    # pprint.pprint(results[0].keypoints.squeeze().tolist())
    # pprint.pprint(keypoints)
    if(keypoints != None and PlayerService.does_pushup(keypoints)):
        score = score + 1

    # Put the score of each player in their frame of the CV window
    # This puts the score of 1 player on the screen
    cv2.putText(annotated_frame, "Score: {}".format(score), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Load the game-UI in the CV window

    # Display frame
    cv2.imshow("Warming-Up | CV DOJO", annotated_frame)

    # Stop application if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture and close windows
cap.release()
cv2.destroyAllWindows()

