from ultralytics import YOLO
import cv2
from models.game_menu import GameMenu

# Load the custom YOLOv8 model
model = YOLO('model.yaml').load('weights.pt')  # build from YAML and transfer weights
players = []
# Time in minutes to compete for points in the chosen exercise game
timer = 240
# Check which exercise is chosen (Push-Up, Sit-Up, Jumping Jack, Squat, Remix (all at once))
exercise = GameMenu.chosen_exercise
# Load video file
cap = cv2.VideoCapture(0)

while cap.isOpened():
    # Read frame
    ret, frame = cap.read()

    # Break loop if video ends
    if not ret:
        break

    # Process frame and put it through the model (what activity / pose is detected, how many people)

    # Assign all detected people to a Player class (with e.g. a current_score and high_score)

    # Split the CV window into multiple frames for each player

    # Draw the keypoints (only for testing) and add class name to visualize the current detected activity / pose of all players in the CV window

    # Start keeping score of the chosen exercise for each player. Add the score to each players total.

    # Put the score of each player in their frame of the CV window

    # Load the game-UI in the CV window

    # Display frame
    cv2.imshow("Warming-Up | CV DOJO", frame)

    # Exit loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture and close windows
cap.release()
cv2.destroyAllWindows()

