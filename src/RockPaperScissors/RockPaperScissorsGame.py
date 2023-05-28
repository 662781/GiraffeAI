from shared.utils import Generics
from shared.model import CVGame
import cv2

class RockPaperScissorsGame(CVGame):
    def __init__(self):
        super().__init__()

    def setup(self, options):
        self.options = options
    
    def update(self, camera_image):
        height, width, _ = camera_image.shape
        image = cv2.flip(camera_image, 1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.should_switch = True
            self.next_game = "Main Menu"

        return Generics.put_text_with_ninja_font(image, self.__class__.__name__ +"\nComing Soon!\nPress 'q'\nto Return to\nMain Menu",(10, 10),(0, 0, 0))  

    def cleanup(self):
        super().cleanup()
