import cv2
import time
import numpy as np

# SATURDAY TODO'S:
'''
    - Asset paths with a class in shared.model
    - Singleton YOLO model calling
    - Setup with options from previous menu
    - Special setup for camera shape changes
    - Think about the current way of switching, is the boolean necessary if next_game is already set? maybe cause we have 
'''

from cvninja import CVNinjaGame
from shared.utils import Generics
from shared.model import CVNinjaPlayer
from menus import CVMainMenu

'''
The GameManager controls the camera and feeds camera frames to the currently played game. 
Each iteration it will show the image feed according to what the current game has drawn on it during the update method.
When the switch flag is set to True, the GameManager sets a loading screen and loads the next game/menu. 
'''

class GameManager:
    # count used for overlaying a "loading screen", more info below. 
    self.count = 0 
    games = { 
        "Main Menu": CVMainMenu(),
        "CVNinja": CVNinjaGame()
    }
    def __init__(self):
        self.current_game = None
        self.cap = cv2.VideoCapture(0)
        self.loading_image = cv2.imread('shared/assets/loading.png', cv2.IMREAD_UNCHANGED)

        camera_width = 640
        camera_height = 480
        self.cap.set(3, camera_width)
        self.cap.set(4, camera_height)

        cv2.namedWindow("CVDojo", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("CVDojo", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def switch_game(self, new_game):
        if self.current_game is not None:
            self.current_game.cleanup()
        # maybe get the options here from the game
        #options = self.current_game.options
        self.current_game = self.games[new_game]
        
        self.cap.set(3, self.current_game) # options["CAMERA_HEIGHT"] maybe?
        self.cap.set(4, camera_height)
        self.current_game.setup() 
       
    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Frame not captured, exiting...")
                break

            frame = self.current_game.update(frame)
        
            if self.current_game.should_switch:
                # In order to get a standard loading screen, we load in an overlay with a fake progress bar. 
                # The count is required to make sure the frame is sent as the last frame before the games are switched 
                if(self.count == 0 ):
                    overlay = np.ones(frame.shape, dtype="uint8") * 127
                    alpha = 0.7  # Adjust the overlay intensity (0.0 to 1.0)
                    frame = cv2.addWeighted(frame, 1-alpha, overlay, alpha, 0)
                    frame = Generics.overlayPNG(frame,self.loading_image, [200,200] )
                    self.count = 1
                else:
                    self.count = 0 
                    next_game = self.current_game.next_game
                    if(next_game is None):
                        print("No new game given. Got: ", next_game)
                        break # exit entirely
                    self.switch_game(next_game)

            


            cv2.imshow("CVDojo", frame)

        self.cap.release()
        cv2.destroyAllWindows()

game_manager = GameManager()
game_manager.switch_game("Main Menu")
game_manager.run()