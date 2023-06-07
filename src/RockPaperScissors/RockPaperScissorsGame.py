import random
import cv2
from cvzone.HandTrackingModule import HandDetector
import time
from RockPaperScissors.model import game_utils

from shared.model import CVGame


class RockPaperScissorsGame(CVGame):
    def __init__(self):
        super().__init__()

    def setup(self, options):
        self.detectorLeft = HandDetector(maxHands=1)
        self.detectorRight = HandDetector(maxHands=1)
        self.scores = [0, 0]  # [PlayerLeft, PlayerRight]
        self.startGame = False
        self.timer = 0
        self.stateResult = False

        self.player1 = "Player 1"
        self.player2 = "Player 2" # Default names
        self.active_player = None
        self.winner = 4
        self.new_round = False

        #self.options = options
    
    def update(self, frame):
        display_fps = self.cvFpsCalc.get()
        # Split the frame in two
        height, width = frame.shape[:2]
        half_width = int(width/2)
        frame = cv2.flip(frame, 1)

        left_frame = frame[:, :half_width]
        right_frame = frame[:, half_width:]

        handLeft = self.detectorLeft.findHands(left_frame, draw=False)  # with draw
        handRight = self.detectorRight.findHands(right_frame, draw=False)  # with draw



        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self.should_switch = True
            self.next_game = "Main Menu"

        if handLeft:
            handLeftText = game_utils.mirror_hands(handLeft)
        else:
            handLeftText = "None"
        if handRight:
            handRightText = game_utils.mirror_hands(handRight)
        else:
            handRightText = "None"

        if handLeft and handRight:
            fingersLeft = self.detectorLeft.fingersUp(handLeft[0])
            fingersRight = self.detectorRight.fingersUp(handRight[0])
            if fingersLeft == [1, 0, 0, 0, 0] and fingersRight == [1, 0, 0, 0, 0]:
                self.startGame = True
                self.initialTime = time.time()
                self.stateResult = False
                self.winner = 4
                self.new_round = False

        if self.startGame:

            if self.stateResult is False:
                self.timer = time.time() - self.initialTime

                if self.timer > 1:
                    self.stateResult = True
                    self.timer = 0

                    if handLeft and handRight:

                        # Get player move
                        playerLeftMove, playerLeftMoveName, playerRightMove, playerRightMoveName = game_utils.get_players_move(handLeft, self.detectorLeft, self.player1, handRight, self.detectorRight, self.player2)
                        self.scores, self.winner, self.new_round = game_utils.calculate_results_against_players(playerLeftMove, playerRightMove, self.scores, self.player2, self.player1)
                    else:
                        print("One or both hands were not detected!")
        return game_utils.draw_ui_against_players(self.scores, left_frame, right_frame, half_width, height, handLeftText, handRightText, display_fps, self.winner, self.new_round)
        self.new_round = False
    def cleanup(self):
        super().cleanup()
