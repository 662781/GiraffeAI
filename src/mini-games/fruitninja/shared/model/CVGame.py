from shared.utils import CvFpsCalc

class CVGame:
    
    def __init__(self):
        self.next_game = None
        self.options = {"CAMERA_WIDTH": 640, "CAMERA_HEIGHT" : 480}
        self.options_next_game = {"CAMERA_WIDTH": 640, "CAMERA_HEIGHT" : 480}

        self.camera_width = self.options_next_game["CAMERA_WIDTH"]
        self.camera_height = self.options_next_game
        # Indicator used by other games if the game is exiting to another game or a complete quit
        self.should_switch = False
        self.cvFpsCalc = CvFpsCalc(buffer_len=10)


    def setup(self, options):

        pass

    def update(self, image):
        pass

    def cleanup(self):
        self.should_switch = False # if the game is chosen again later, this property needs to be False again. 
        self.next_game = None


