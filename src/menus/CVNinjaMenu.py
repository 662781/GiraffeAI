import cv2
from shared.model import CVGame
from cvninja import CVNinjaGame # todo
from .model import MainMenuObject
import pymunk
import numpy as np
from shared.utils import Generics, CVAssets
from shared.model import CVNinjaPlayer
from shared.model import YOLO
import traceback
from PIL import Image, ImageDraw, ImageFont



class CVNinjaMenu(CVGame):
    

    def __init__(self):
        super().__init__()
        self.cvninja_image = cv2.imread(CVAssets.IMAGE_MENU_CVNINJA_START, cv2.IMREAD_UNCHANGED) 
        self.game_options = []
        self.yolo_model = YOLO(CVAssets.YOLO_MODEL_L)  # load an official model
        self.background = cv2.imread(CVAssets.IMAGE_DOJO, cv2.IMREAD_UNCHANGED)
        self.background = cv2.cvtColor(self.background, cv2.COLOR_BGRA2RGBA)
        self.back_button = cv2.imread(CVAssets.IMAGE_MENU_BACK_BUTTON, cv2.IMREAD_UNCHANGED)

    def setup(self, options):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.option_back_button = MainMenuObject(self.back_button, 100)
        self.option_back_button.spawn_object(self.space, 99, position=(30,350))

        self.ninja_item = MainMenuObject(self.cvninja_image, 150)
        self.ninja_item.spawn_object(self.space, 1, position=(420,250))

        self.game_options.extend([self.ninja_item, self.option_back_button])
        
        self.background = cv2.resize(self.background, (self.options["CAMERA_WIDTH"], self.options["CAMERA_WIDTH"]))
        self.player = CVNinjaPlayer(5)
        self.space.add(self.player.line_left_hand_body, self.player.line_left_hand_shape)
        self.space.add(self.player.line_right_hand_body, self.player.line_right_hand_shape)
        self.space.add(self.player.line_left_leg_body, self.player.line_left_leg_shape)
        self.space.add(self.player.line_right_leg_body, self.player.line_right_leg_shape)
        handler = self.space.add_collision_handler(5, 1)
        handler.data["player"] = self.player # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
        handler.begin = self.process_hit
        handler = self.space.add_collision_handler(5, 99)
        handler.data["player"] = self.player # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
        handler.begin = self.process_hit


        
    def update(self, image):

        height, width, _ = image.shape
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.flip(image, 1)

        image.flags.writeable = False  
        results = self.yolo_model(image, max_det=1, verbose=False)
        image.flags.writeable = True  
        self.space.step(1/60)
        image = Generics.overlayPNG(image, self.background, pos=[0, 0])
        image = Generics.put_text_with_ninja_font(image, " CV \nNinja",(250, 10),(0, 0, 0)) 

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        try:
            for i, result in enumerate(results):
                keypoints = result.keypoints.cpu().numpy()[0]
                self.player.update_tracking(keypoints)
                Generics.get_player_trailing(self.player, image)
                Generics.draw_stick_figure(image, keypoints)
                self.player.reset_keypoints()

        except Exception:
            traceback.print_exc()
            pass

        for object_spawner in self.game_options:
               for shape in object_spawner.pymunk_objects_to_draw:
                    image = Generics.draw_pymunk_object_in_opencv(image, shape)

        
        if cv2.waitKey(1) & 0xFF == 27:
            self.should_switch = True
            self.next_game = None
        return image

    def cleanup(self):
        self.game_options = []
        super().cleanup()

    def process_hit(self, arbiter, space, data):
        # Get objects that were involved in collision
        kinematic_shape = arbiter.shapes[0]
        shape_trail_length = data["player"].get_trailing_length_by_limb(kinematic_shape.player_limb)
        print("Hit with ", kinematic_shape.player_limb)
        shape = next((obj for obj in arbiter.shapes if obj.body.body_type != pymunk.Body.KINEMATIC), None)
        if(shape_trail_length > 10): 
            shape.parent_object.collision_aftermath(space, shape)
            self.should_switch = True
            if(shape.collision_type == 1):
                self.options_next_game["NUMBER_OF_PLAYERS"] = 1 # todo: dynamic
                self.next_game = "CVNinja"
            elif(shape.collision_type == 99):
                self.next_game = "Main Menu"
        return True
    

