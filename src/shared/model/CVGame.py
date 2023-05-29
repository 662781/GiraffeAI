from shared.utils import CvFpsCalc

class CVGame:
    """An abstract class used as the base for all games and menus.  
    
    The CVGame class is an abstract class that is used as the base class for all games and menus.
    Every Game and Menu inherits these methods and may override them to suit their requirements. 
    The class comes with some predetermined attributes that roughly apply to all CVGames.

    Attributes:
        next_game (CVGame): The CVGame that should be started after the current CVGame has concluded, usually used to return to the Main Menu
        options (Dict[str, Any]): An associative array consisting of options either passed from a previous CVGame or the standard camera dimension values.
        options_next_game (Dict[str, Any]): The options that will be passed to the next_game
        camera_width (int): The width of the camera frames which the game will be receiving.
        camera_height (int): The height of the camera frames which the game will be receiving.
        should_switch (bool): The flag on whether or not the CVGame should switch to the defined next_game
        cvFpsCalc (cvFpsCalc): An FPS utility that can be to measure general performance of the CVGame.
    """
    def __init__(self):
        """Intialize CVGame with standard attributes that apply to most games"""

        self.next_game = None
        self.options = {"CAMERA_WIDTH": 640, "CAMERA_HEIGHT" : 480}
        self.options_next_game = {"CAMERA_WIDTH": 640, "CAMERA_HEIGHT" : 480}

        self.camera_width = self.options_next_game["CAMERA_WIDTH"]
        self.camera_height = self.options_next_game["CAMERA_HEIGHT"]
        # Indicator used by other games if the game is exiting to another game or a complete quit
        self.should_switch = False
        self.cvFpsCalc = CvFpsCalc(buffer_len=10)


    def setup(self, options):
        """Setup the CVGame's 'board' before it starts
        
        setup() is used to set up anything the CVGame requires before starting it's loop.

        Args:
            options (Dict[str, Any]): An associative array of options required for setup
        
        Returns:
            None
        """
        pass

    def update(self, frame):
        """Update the game state with every new frame received

        update() is where the CVGame uses the given frame to apply its logic and behavior and returns the processed frame to be displayed 

        Returns:
            np.ndarray: The processed frame
        """
        pass

    def cleanup(self):
        """Cleanup any loose ends after the game has concluded
        
        cleanup() is used to finalize the game state by cleaning and tying up loose ends
        By default every CVGame will reset the should_switch and next_game values to the initial values. 

        Returns:
            None
        """
        self.should_switch = False
        self.next_game = None


