import cv2
import numpy as np
from WarmingUp.services.keypoint_classifier import KeyPointClassifier
from WarmingUp.services.keypoint_service import KeypointService
class UIService:
    frame = None

    def __init__(self, frame) -> None:
        self.frame = frame
    
    def put_score(self, players: list, xy: list, distance: int):
        if (players is not None): 
            for i, player in enumerate(players):
                cv2.putText(self.frame, "Player {}: {}".format(i+1, int(round(player.score / 2, 0))), xy, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                xy = [xy[0], xy[1] + distance]

    def put_mode(self, mode: int, xy: tuple):
        if mode == 1:
            cv2.putText(self.frame, "Snapshot Mode", xy, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    def show_pause_menu(self, frame):
        print("Game Paused: Too many or not enough players detected!")
        return self.create_faded_frame(frame)
    
    def create_faded_frame(self, frame):
        overlay = np.ones(frame.shape, dtype="uint8") * 127
        alpha = 0.7 
        frame = cv2.addWeighted(frame, 1-alpha, overlay, alpha, 0)
        return frame

    def show_prediction(self, pred_classes: list[int], xy: list, distance: 30):
        """Show the prediction of the keypoint classifier in the CV window using an Annotator object from the Ultralytics library"""
        for i, class_nr in enumerate(pred_classes):
            pred_class = ""
            for j, class_str in enumerate(KeyPointClassifier.get_classes()):
                if j == class_nr:
                    pred_class = class_str
            # Draw the predicted class on the CV window
            cv2.putText(self.frame, "Prediction Player {}: {}".format(i+1, pred_class), xy, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            xy = [xy[0], xy[1] + distance]

    def on_player_amount_change(player_amt):
        return player_amt
    
    def draw_player_amt_select():
        # Parameters: trackbar name, window name, initial value, maximum value, callback function
        cv2.createTrackbar("Player Amount", "CVDojo", 1, 4, UIService.on_player_amount_change)
    
    def draw_buttons(self):
        # Button coordinates and dimensions
        button_back = {"x": 20, "y": 350, "width": 100, "height": 50}
        button_pushup = {"x": 50, "y": 100, "width": 200, "height": 50}
        button_situp = {"x": 50, "y": 160, "width": 200, "height": 50}
        button_squat = {"x": 50, "y": 220, "width": 200, "height": 50}
        button_jumping_jacks = {"x": 50, "y": 280, "width": 200, "height": 50}
        button_start = {"x": 50, "y": 340, "width": 200, "height": 50}
        # Draw buttons on the frame
        cv2.rectangle(self.frame, (button_back["x"], button_back["y"]),
                    (button_back["x"] + button_back["width"], button_back["y"] + button_back["height"]),
                    (255, 0, 0), -1)
        cv2.putText(self.frame, "Back", (button_back["x"] + 10, button_back["y"] + 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)