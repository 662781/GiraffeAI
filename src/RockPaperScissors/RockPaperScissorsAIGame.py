import random
import cv2
from cvzone.HandTrackingModule import HandDetector
import time
from RockPaperScissors.model import game_utils


from shared.utils import Generics
from shared.model import CVGame

class RockPaperScissorsAIGame(CVGame):
    def __init__(self):
        super().__init__()

    def setup(self, options):
        #self.options = options
        self.detectorLeft = HandDetector(maxHands=1)
        self.scores = [0, 0]  # [PlayerLeft, AI]
        self.winStreak = [0, 0] # [PlayerLeft, AI]
        self.startGame = False
        self.timer = 0
        self.stateResult = False
        self.AIMove = 0
        self.player1 = "Change Name"
        self.player2 =  "AI" # Default names
        self.active_player = None
    
    def update(self, frame):
        # Split the frame in two
        height, width = frame.shape[:2]
        half_width = int(width/2)

        left_frame = frame[:, :half_width]
        right_frame = frame[:, half_width:]

        handLeft, frame = self.detectorLeft.findHands(right_frame)  # with draw



        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self.should_switch = True
            self.next_game = "Main Menu"
        elif key == ord('1'):
            self.active_player = 1
            self.player1 = ""
        elif key == 13: # Enter key
            self.active_player = None
        elif self.active_player is not None:
            if key == 8:  # backspace
                if self.active_player == 1 and len(self.player1) > 0:
                    self.player1 = self.player1[:-1]
                elif self.active_player == 2 and len(self.player2) > 0:
                    self.player2 = self.player2[:-1]
            elif 32 <= key <= 126:  # visible ASCII characters
                if self.active_player == 1:
                    self.player1 += chr(key)
                else:
                    self.player2 += chr(key)

        if handLeft:
            fingersLeft = self.detectorLeft.fingersUp(handLeft[0])
            if fingersLeft == [1, 0, 0, 0, 0]:
                self.startGame = True
                self.initialTime = time.time()
                self.stateResult = False

        if self.startGame:

            if self.stateResult is False:
                self.timer = time.time() - self.initialTime
                self.AIMove = 0
                if self.timer > 3:
                    self.stateResult = True
                    self.timer = 0

                    if handLeft:
                        # Get player move
                        playerLeftMove, playerLeftMoveName = game_utils.get_player_move(handLeft, self.detectorLeft, self.player1)
                        # Get AI move
                        self.AIMove, predicted_move = game_utils.get_ai_move(self.player1)

                        result, self.scores, self.winStreak = game_utils.calculate_result_against_AI(playerLeftMove, self.AIMove, self.scores, self.winStreak)
                        game_utils.save_to_csv(self.player1, playerLeftMove, self.winStreak[1], predicted_move, self.AIMove)

                    else:
                        print("hand not detected!")

        return game_utils.draw_ui_against_AI(self.player1, self.player2, self.scores, self.AIMove, left_frame, right_frame, half_width, height)  

    def cleanup(self):
        super().cleanup()
