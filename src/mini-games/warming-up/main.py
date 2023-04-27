from ultralytics import YOLO
from ultralytics.yolo.engine.results import Results
from ultralytics.yolo.utils.plotting import Annotator
import cv2
import torch
import time
import pprint
from models.game_menu import GameMenu
from services.fps_counter_service import FPSCounterService
from services.player_service import PlayerService
from services.keypoint_service import KeypointService

# Load the service instances
kp_serv = KeypointService()

# Load the custom YOLOv8 model
model: YOLO = YOLO('dl-model/yolov8n-pose.pt')  # load a pretrained model (recommended for training)
# Use CUDA, AKA the GPU
#model.to('cuda')

players = []
score = 0
# Check which exercise is chosen (Push-Up, Sit-Up, Jumping Jack, Squat, Remix (all at once))
exercise = GameMenu.chosen_exercise
# Time in minutes to compete for points in the chosen exercise game
timer = 240

# Capture video frames with "camera 0"
cap = cv2.VideoCapture(0)
# Set the capture resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Set the window to full screen
# cv2.namedWindow("Warming-Up | CV DOJO", cv2.WINDOW_NORMAL)
# cv2.setWindowProperty("Warming-Up | CV DOJO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

#print(torch.cuda.is_available())

# Set the default mode
mode = 0

while cap.isOpened():
    # Read frame
    ret, frame = cap.read()

    # Break loop if video ends
    if not ret:
        break

    # Check for user input
    key = cv2.waitKey(1) & 0xFF
    # Stop application if 'q' key is pressed
    if key == ord('q'):
        break
    
    # Save the letter & number pressed to determine the "mode" (0 = default, 1 = snapshot mode)
    # In mode 1, any number between 0 - 9 can be pressed to take a snap shot of the current keypoints with that number as a prefix
    # This number is based off of the index of one of the classes in "classifier_classes.csv" (e.g. PushUp_Down)
    number, mode = KeypointService.select_mode(key, mode)

    # Flip the frame (selfie mode)
    frame = cv2.flip(frame, 1)

    # Show FPS in the CV Window
    FPSCounterService.show_fps(frame, time.time(), FPSCounterService)

    # Process frame and put it through the model (what activity / pose is detected, how many people)
    # This can currently only classify multiple people
    # Predict and get the results from YOLOv8 model
    results: Results = model.predict(frame)[0]

    # Split the CV window into multiple frames for each player

    # Assign all detected people to a Player class (with e.g. a current_score and high_score)

    # Draw the keypoints (only for testing) and add class name to visualize the current detected activity / pose of all players in the CV window
    # Draws the bounding box & keypoints from the YOLOv8 model
    annotated_frame = results.plot()
    
    # Get the keypoints in a list 
    keypoints = results.keypoints.squeeze().tolist()
    
    # Show all keypoint numbers  
    ann = Annotator(annotated_frame)
    KeypointService.show_keypoint_nrs(ann, keypoints)

    # Pre-process keypoints for keypoint / pose prediction input
    proc_keypoints = kp_serv.pre_process_keypoints(keypoints)

    # If 'k' is pressed and a number between 0 - 9, save current keypoints to csv
    KeypointService.write_kp_data_to_csv(number, mode, proc_keypoints)

    # Debug
    # pprint.pprint(keypoints)
    # pprint.pprint(proc_keypoints)
    # pprint.pprint(len(proc_keypoints))
    # pprint.pprint(len(keypoints))

    # Start keeping score of the chosen exercise for each player. Add the score to each players total.
    # if(keypoints is not None and PlayerService.does_pushup(keypoints)):
    #     score = score + 1

    # Put the score of each player in their frame of the CV window
    # This puts the score of 1 player on the screen
    cv2.putText(annotated_frame, "Score: {}".format(score), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Place an indicator of the mode on screen if it's 1
    if mode == 1:
        cv2.putText(annotated_frame, "Snapshot Mode", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Load the game-UI in the CV window

    # Display frame
    cv2.imshow("Warming-Up | CV DOJO", annotated_frame)

# Release video capture and close windows
cap.release()
cv2.destroyAllWindows()

