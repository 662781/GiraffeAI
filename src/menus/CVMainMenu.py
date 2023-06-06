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



class CVMainMenu(CVGame):
    

    def __init__(self):
        super().__init__()
        self.cvninja_image = cv2.imread(CVAssets.IMAGE_MENU_CVNINJA, cv2.IMREAD_UNCHANGED) 
        self.warming_up_image = cv2.imread(CVAssets.IMAGE_MENU_WARMING_UP, cv2.IMREAD_UNCHANGED)
        self.fight_simulator_image = cv2.imread(CVAssets.IMAGE_MENU_FIGHT_SIMULATOR, cv2.IMREAD_UNCHANGED)
        self.rock_paper_scissors_image = cv2.imread(CVAssets.IMAGE_MENU_ROCK_PAPER_SCISSORS, cv2.IMREAD_UNCHANGED)

        self.game_options = []
        self.yolo_model = YOLO(CVAssets.YOLO_MODEL_L)  # load an official model
        self.background = cv2.imread(CVAssets.IMAGE_DOJO, cv2.IMREAD_UNCHANGED)
        self.background = cv2.cvtColor(self.background, cv2.COLOR_BGRA2RGBA)

    def setup(self, options):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        # todo: game menu options need new images but the design has terrible images except for the CVNinja one. Have Bas edit them on figma and download them 
        self.warming_up_item = MainMenuObject(self.warming_up_image, 150)
        self.warming_up_item.spawn_object(self.space, 1, position=(50,50))

        self.ninja_item = MainMenuObject(self.cvninja_image, 150)
        self.ninja_item.spawn_object(self.space, 2, position=(450,50))
        
        
        self.fight_simulator_item = MainMenuObject(self.fight_simulator_image, 150)
        self.fight_simulator_item.spawn_object(self.space, 4, position=(50,320))

        self.rock_paper_scissors_item = MainMenuObject(self.rock_paper_scissors_image, 150)
        self.rock_paper_scissors_item.spawn_object(self.space, 5, position=(450,320))

        self.game_options.extend([self.warming_up_item, self.ninja_item, self.fight_simulator_item, self.rock_paper_scissors_item])
        
        self.background = cv2.resize(self.background, (self.options["CAMERA_WIDTH"], self.options["CAMERA_WIDTH"]))
        self.player = CVNinjaPlayer(6)
        self.space.add(self.player.line_left_hand_body, self.player.line_left_hand_shape)
        self.space.add(self.player.line_right_hand_body, self.player.line_right_hand_shape)
        self.space.add(self.player.line_left_leg_body, self.player.line_left_leg_shape)
        self.space.add(self.player.line_right_leg_body, self.player.line_right_leg_shape)

        # todo: dit kan makkelijker, maar ik maak dit op Zondag 03:45
        handler = self.space.add_collision_handler(6, 1)  
        handler.data["player"] = self.player # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
        handler.begin = self.process_hit

        handler = self.space.add_collision_handler(6, 2)
        handler.data["player"] = self.player # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
        handler.begin = self.process_hit

        handler = self.space.add_collision_handler(6, 4) 
        handler.data["player"] = self.player # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
        handler.begin = self.process_hit

        handler = self.space.add_collision_handler(6, 5) 
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
        image = Generics.put_text_with_ninja_font(image, " CV \nDOJO",(250, 5),(0, 0, 0)) 
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        try:
            for i, result in enumerate(results):
                self.keypoints = result.keypoints.cpu().numpy()[0]
                self.player.update_tracking(self.keypoints)
                Generics.get_player_trailing(self.player, image)
                Generics.draw_stick_figure(image, self.keypoints)
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
        shape = next((obj for obj in arbiter.shapes if obj.body.body_type != pymunk.Body.KINEMATIC), None)
          
          # Check if you did an actual movement and not just small shifts
        if(shape_trail_length > 20 and shape.parent_object.collision_requirements_are_met(data["player"], kinematic_shape)): 
            shape.parent_object.collision_aftermath(space, shape)
            self.should_switch = True
            # DON'T HAVE A MENU FOR YOUR GAME? SET YOUR OPTIONS IN THE CORRECT IF STATEMENT: self.next_game_options["OPTION"] = "something"
            if(shape.collision_type == 1):
                self.next_game = "Warming-up"
            elif(shape.collision_type == 2):
                self.next_game = "CVNinja Menu"
            elif(shape.collision_type == 4):
                self.next_game = "Fight Simulator"
            elif(shape.collision_type == 5):
                self.next_game = "Rock Paper Scissors Menu"
            else:
                self.next_game = None
        return True
    
    def is_in_the_middle(self,keypoints):
        head = (int(keypoints[0][0]), int(keypoints[0][1]))
        x = head[0] 
        x_start = 0
        x_end = 640

        fifth = (x_end - x_start) / 5
        middle_part_start = x_start + 2 * fifth
        middle_part_end = x_start + 3 * fifth

        if middle_part_start <= x <= middle_part_end:
            return True
        else:
            return False
        # method to make sure decisions are made in the middle
        



