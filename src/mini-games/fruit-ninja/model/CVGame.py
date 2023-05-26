from utils import CvFpsCalc

class CVGame:
    # Indicator used by other games if the game is exiting to another game or a complete quit
    should_switch = False
    def __init__(self, camera_width = 640 ,camera_height = 480):
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.cvFpsCalc = CvFpsCalc(buffer_len=10)
        

    def update(self, image):
        pass

    def cleanup(self):
        self.should_switch = False # if the game is chosen again later, this property needs to be False again. 

    def get_next_game(self):
        pass

