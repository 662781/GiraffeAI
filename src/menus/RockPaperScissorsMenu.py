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



class RockPaperScissorsMenu(CVGame):
    

    def __init__(self):
        super().__init__()
        self.versus_image_ai = cv2.imread(CVAssets.IMAGE_MENU_OPTION_AI, cv2.IMREAD_UNCHANGED) 
        self.versus_image_player = cv2.imread(CVAssets.IMAGE_MENU_OPTION_PLAYER, cv2.IMREAD_UNCHANGED)
        self.back_button = cv2.imread(CVAssets.IMAGE_MENU_BACK_BUTTON, cv2.IMREAD_UNCHANGED)

        self.game_options = []
        self.yolo_model = YOLO(CVAssets.YOLO_MODEL_L)  # load an official model
        self.background = cv2.imread(CVAssets.IMAGE_MENU_BACKGROUND_CLASSROOM, cv2.IMREAD_UNCHANGED)
        self.background = cv2.cvtColor(self.background, cv2.COLOR_BGRA2RGBA)

    def setup(self, options):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        # todo: game menu options need new images but the design has terrible images except for the CVNinja one. Have Bas edit them on figma and download them 
        self.option_versus_player = MainMenuObject(self.versus_image_player, 150)
        self.option_versus_ai = MainMenuObject(self.versus_image_ai, 150)
        self.option_back_button = MainMenuObject(self.back_button, 100)


        self.option_versus_player.spawn_object(self.space, 1, position=(420,250))
        self.option_versus_ai.spawn_object(self.space, 2, position=(420,50))
        self.option_back_button.spawn_object(self.space, 99, position=(30,380))


        self.game_options.extend([self.option_versus_player, self.option_versus_ai, self.option_back_button])
        
        self.background = cv2.resize(self.background, (self.options["CAMERA_WIDTH"], self.options["CAMERA_WIDTH"]))
        self.player = CVNinjaPlayer(5)
        self.space.add(self.player.line_left_hand_body, self.player.line_left_hand_shape)
        self.space.add(self.player.line_right_hand_body, self.player.line_right_hand_shape)
        self.space.add(self.player.line_left_leg_body, self.player.line_left_leg_shape)
        self.space.add(self.player.line_right_leg_body, self.player.line_right_leg_shape)
        handler = self.space.add_collision_handler(5, 1)
        handler.data["player"] = self.player # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
        handler.begin = self.process_hit

        handler = self.space.add_collision_handler(5, 2)
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
        image = Generics.put_text_with_custom_font(image, "Rock Paper Scissors",(25, 10), CVAssets.FONT_FRUIT_NINJA, 25, (255,255,255) ,(0, 0, 0))
        image = Generics.put_text_with_custom_font(image,"INSTRUCTIONS",(20, 145), CVAssets.FONT_FRUIT_NINJA, 18, (255, 255, 255), (0, 0, 0))
        image = Generics.put_text_with_custom_font(image,
                                                   "Ready to face your\nopponent?\nDo a thumbs-up followed\nby your move.\n\nWant to go back to the\nmain menu?\nPress ‘ Q ’\n\n                V.S. A.I\nPress ‘ 1 ’ to change your\nname, when finished\ntyping press ‘ Enter ’",
                                                   (20, 175), CVAssets.FONT_CALIBRI, 12, (255, 255, 255), (0, 0, 0), outline_width=0)

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
        for shape in arbiter.shapes:
            if(shape.body.body_type != pymunk.Body.KINEMATIC):
                if(shape_trail_length > 10): 
                    shape.parent_object.collision_aftermath(space, shape)
                    if(shape.collision_type == 1):
                        self.should_switch = True
                        self.next_game = "Rock Paper Scissors"
                    elif(shape.collision_type == 2):
                        self.should_switch = True
                        self.next_game = "Rock Paper Scissors AI"
                    elif(shape.collision_type == 99):
                        self.should_switch = True
                        self.next_game = "Main Menu"
        return True
    

