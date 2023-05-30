import cv2
import time
import numpy as np

from cvninja import CVNinjaGame
from fightsimulator import FightSimulatorGame
from RockPaperScissors import RockPaperScissorsGame
from RockPaperScissors import RockPaperScissorsAIGame
from WarmingUp import WarmingUpGame

from shared.utils import Generics, CVAssets
from shared.model import CVNinjaPlayer
from menus import CVMainMenu, CVNinjaMenu, RockPaperScissorsMenu



class GameManager:
    """Manages the CVGame objects and camera feed.
    
    The GameManager controls the camera and feeds camera frames to the currently played game. 
    Each iteration it will show the image feed according to what the current game has drawn on it during the update method.
    When the switch flag is set to True, the GameManager sets a loading screen and loads the next game/menu. 
    
    As the game starts with GameManager, all imports are relative to the folder in which the GameManager class resides. 
    Another important feature of the GameManager is built in delay.
    This delay allows games and menus to briefly show their collision effects (menu options splitting in half) before the new game is loaded.   

    Attributes:
        games (Dict[str, CVGame]): list of CVGame object callable by a key string.
        count (int): Used as a way of setting up the loading screen by checking for changes in count.
        start_time (time): Set when a game is switched to help check if the delay_duration is reached.
        delay_duration (float): The amount of delay in seconds until the next game is setup.
        enough_time_passed (bool): Used to ensure the delay requirement is met before switching games.
    """
    # count used for overlaying a "loading screen", more info below. 
    count = 0
    delay_duration = .5 # Delay before next game loads
    start_time = None
    enough_time_passed = False
    games = {
        # Put your menus on the same line as your game, for clarity 
        "Main Menu": CVMainMenu(),

        "CVNinja": CVNinjaGame(), "CVNinja Menu": CVNinjaMenu(),

        "Fight Simulator": FightSimulatorGame(),

        "Rock Paper Scissors": RockPaperScissorsGame(), "Rock Paper Scissors AI": RockPaperScissorsAIGame(), "Rock Paper Scissors Menu": RockPaperScissorsMenu(),

        "Warming Up": WarmingUpGame()
    }
    def __init__(self):
        self.current_game = None
        self.cap = cv2.VideoCapture(0)
        self.loading_image = cv2.imread(CVAssets.IMAGE_LOADING, cv2.IMREAD_UNCHANGED)

        camera_width = 640
        camera_height = 480
        self.cap.set(3, camera_width)
        self.cap.set(4, camera_height)

        cv2.namedWindow("CVDojo", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("CVDojo", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def switch_game(self, new_game):
        options = None
        if self.current_game is not None:
            self.current_game.cleanup()
            options = self.current_game.options_next_game
            if(options["CAMERA_WIDTH"] != self.cap.get(3)  or options["CAMERA_HEIGHT"] != self.cap.get(4)):
                # GameManager overwrites camera dimension where needed
                self.cap.set(3, options["CAMERA_WIDTH"])
                self.cap.set(4, options["CAMERA_HEIGHT"])
    
        self.current_game = self.games[new_game]
        self.current_game.setup(options) 
       
    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Frame not captured, exiting...")
                break
            frame = self.current_game.update(frame)
           
            if self.current_game.should_switch and self._enough_time_passed():
                if(self.count == 0): # We require an overlay with the progress bar to be set as the last shown frame
                    overlay = np.ones(frame.shape, dtype="uint8") * 127
                    alpha = 0.7 
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
                    self.enough_time_passed = False
            cv2.imshow("CVDojo", frame)

        self.cap.release()
        cv2.destroyAllWindows()

    def _enough_time_passed(self): # A small delay before the next screen is set to make sure player sees the menu physics
        if self.enough_time_passed:
            return True
        if self.start_time is None:
            print("Start Time not defined, creating...")
            self.start_time = time.time()
            return False

        self.elapsed_time = time.time() - self.start_time  
        print("Elapsed time: ", self.elapsed_time)
        if(self.elapsed_time >= self.delay_duration):
            print("ENOUGH TIME HAS ELAPSED")
            self.enough_time_passed = True
            self.start_time = None
            return True
        return False


game_manager = GameManager()
game_manager.switch_game("Warming Up")
game_manager.run()