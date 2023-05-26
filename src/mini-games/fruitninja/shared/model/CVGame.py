from shared.utils import CvFpsCalc

class CVGame:
    
    def __init__(self, camera_width = 640 ,camera_height = 480):
        self.camera_width = camera_width
        self.camera_height = camera_height
        # Indicator used by other games if the game is exiting to another game or a complete quit
        self.should_switch = False
        self.cvFpsCalc = CvFpsCalc(buffer_len=10)

        

    def update(self, image):
        pass

    def cleanup(self):
        self.should_switch = False # if the game is chosen again later, this property needs to be False again. 
        self.next_game = ""

    def get_next_game(self):
        pass

