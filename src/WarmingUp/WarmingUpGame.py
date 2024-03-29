from shared.utils import Generics
from shared.model import CVGame
from shared.model import YOLO
from ultralytics.yolo.engine.results import Results
from ultralytics.yolo.utils.plotting import Annotator
import cv2
import torch
import time
import os
import pprint
from WarmingUp.model.game_menu import GameMenu
from WarmingUp.model.player import Player
from WarmingUp.services.fps_counter_service import FPSCounterService
from WarmingUp.services.player_service import PlayerService
from WarmingUp.services.keypoint_service import KeypointService
from WarmingUp.services.keypoint_classifier import KeyPointClassifier
from WarmingUp.services.ui_service import UIService

class WarmingUpGame(CVGame):
    def __init__(self):
        super().__init__()

    def setup(self, options):
        self.options = options

        # Load the custom YOLOv8 model
        self.model: YOLO = YOLO()  # Load a pretrained YOLOv8 model via the custom class (YOCO)

        # Set the path for the custom keypoint classifier model
        self.model_path: str = 'WarmingUp/assets/tflite/keypoint_classifier.tflite' 

        print(torch.cuda.is_available())

        # The number of players chosen (should be chosen in the future game menu)
        self.no_players_set: int = 1

        # Create Player class instances with PlayerService
        self.pl_serv = PlayerService(self.no_players_set)
        self.players_list: list[Player] = self.pl_serv.create_players()

        # Instantiate prediction list
        self.pred_classes: list[int] = []

        # Check which exercise is chosen (Push-Up, Sit-Up, Jumping Jack, Squat)
        self.exercise: str = GameMenu.get_exercise()

        # Time in seconds to compete for points in the chosen exercise game
        self.timer: int = 240

        # Set the default mode
        self.mode: int = 0
    
    def update(self, frame):
        # Check for user input
        key = cv2.waitKey(1) & 0xFF
        # Stop application if 'q' key is pressed
        if key == ord('q'):
            self.should_switch = True
            self.next_game = "Main Menu"
        
        # Save the letter & number pressed to determine the "mode" (0 = default, 1 = snapshot mode)
        # In mode 1, any number between 0 - 9 can be pressed to take a snap shot of the current keypoints with that number as a prefix
        # This number is based off of the index of one of the classes in "classifier_classes.csv" (e.g. PushUp_Down)
        number, self.mode = KeypointService.select_mode(key, self.mode)

        # Flip the frame (selfie mode)
        frame = cv2.flip(frame, 1)

        # Show FPS in the CV Window
        # FPSCounterService.show_fps(frame, time.time(), FPSCounterService)

        # Set writeable to false
        frame.flags.writeable = False

        # Process frame and put it through the YOLOv8 model (how many people are detected?)
        # This can detect multiple people
        # Predict and get the results from YOLOv8 model
        results: Results = self.model.predict(frame, max_det=self.no_players_set)[0]

        # Set writeable to true
        frame.flags.writeable = True

        # Draw the keypoints (only for testing) and add class name to visualize the current detected pose of all players in the CV window
        # Draws the bounding box & keypoints from the YOLOv8 model
        # Use annotated_frame = frame to not show the bounding boxes and keypoints
        annotated_frame = results.plot()
        
        # Get the keypoints in a easier iterable list
        # Shape when 1 person is detected: [[x, y, conf], ..]
        # Shape when more people are detected: [[[x, y, conf], ..], [[x, y, conf], ..]]
        keypoints: list = results.keypoints.squeeze().tolist()
        
        if KeypointService.keypoints_detected(keypoints):
            
            # Get the amount of detected players
            no_players_detected = results.__len__()

            # Add the amount of detected players to the PlayerService instance
            self.pl_serv.no_players_detected = no_players_detected

            if self.pl_serv.all_players_present():

                # Create instance of KeypointService
                kp_serv = KeypointService(no_players_detected) 

                # Append preprocessed keypoints to the player objects
                self.pl_serv.append_preprocessed_keypoints_to_players(keypoints)

                # Show all keypoint numbers with a custom annotation (for testing only)
                # kp_serv.show_keypoint_nrs(ann, keypoints)

                # Get the pre-processed keypoints (for every detected person)
                player_proc_keypoints: list = []
                if (no_players_detected == 1):
                    player_proc_keypoints.append(self.players_list[0].keypoints)
                elif (no_players_detected > 1):
                    for player in self.players_list:
                        player_proc_keypoints.append(player.keypoints)

                # Show the predicted class if the custom model is available (for every detected person)
                self.pred_classes.clear()
                classifier = KeyPointClassifier(self.model_path, num_threads=1)
                if (KeyPointClassifier.is_model_available(self.model_path)):
                    for kp_list in player_proc_keypoints:
                        self.pred_classes.append(classifier(kp_list))

                # If 'k' is pressed and then a number between 0 - 9, save current keypoints to csv
                # Only available if 1 person is detected
                if self.no_players_set == 1 and no_players_detected == 1:
                    kp_serv.write_kp_data_to_csv(number, self.mode, player_proc_keypoints[0])

                # Start keeping score of the chosen exercise for each player. Add the score to each players total.
                for i, player in enumerate(self.players_list):
                    if(player.does_exercise(self.exercise, self.pred_classes[i]) == True):
                        player.score += 1
            else:
                ui = UIService(annotated_frame)
                return ui.show_pause_menu(annotated_frame)

        # Load a new instance of the UIService class
        ui = UIService(annotated_frame)

        # Put the score of each player on the CV window
        ui.put_score(self.players_list, [10, 30], 30)

        # Put the predicted class of each player on the CV window
        ui.show_prediction(self.pred_classes, [10, 100], 30)

        # Place an indicator of the mode on screen if it's 1 (Snapshot Mode) and if there is only 1 player
        if self.no_players_set == 1:
            ui.put_mode(self.mode, (50, 150))

        # Display frame
        return annotated_frame

    def cleanup(self):
        super().cleanup()
