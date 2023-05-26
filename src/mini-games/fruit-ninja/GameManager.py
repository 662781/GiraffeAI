import cv2
from CVNinja import CVNinja
from CVMainMenu import CVMainMenu
import time
import numpy as np
from utils import Generics

'''
The GameManager controls the camera and feeds camera frames to the currently played game. 
Each iteration it will show the image feed according to what the current game has drawn on it during the update method.
When the switch flag is set to True, the GameManager sets a loading screen and loads the next game/menu. 
'''

class GameManager:
    def __init__(self):
        self.current_game = None
        self.cap = cv2.VideoCapture(0)
        self.loading_image = cv2.imread('resources/loading.png', cv2.IMREAD_UNCHANGED)

        camera_width = 640
        camera_height = 480
        self.cap.set(3, camera_width)
        self.cap.set(4, camera_height)

        cv2.namedWindow("CVDojo", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("CVDojo", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def switch_game(self, new_game):
        if self.current_game is not None:
            self.current_game.cleanup()
        self.current_game = new_game
        
        self.current_game.setup()
       
    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Frame not captured, exiting...")
                break

            frame = self.current_game.update(frame)
        
            if self.current_game.should_switch:
                cv2.imshow("CVDojo", frame)
                next_game = self.current_game.get_next_game()
                if(next_game is None):
                    print("No new game given. Got: ", next_game)
                    break # exit entirely
                self.switch_game(next_game)


            cv2.imshow("CVDojo", frame)

        self.cap.release()
        cv2.destroyAllWindows()

game_manager = GameManager()
game_manager.switch_game(CVMainMenu())
game_manager.run()