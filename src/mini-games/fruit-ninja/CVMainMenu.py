import cv2
from model import CVGame
from CVNinja import CVNinja
from model import MainMenuObject
import pymunk
import numpy as np
from utils import Generics
from CVNinjaPlayer import CVNinjaPlayer
from ultralytics import YOLO
import traceback


class CVMainMenu(CVGame):
    games = [CVNinja()]
    options = []
    next_game = None
    def __init__(self):
        super().__init__()

    def setup(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        cvninja_image = cv2.imread('resources/Menu-Item-CVNinja.png', cv2.IMREAD_UNCHANGED) 
        self.ninja_item = MainMenuObject(cvninja_image, 150)
        self.ninja_item.spawn_object(self.space, 1, position=(100,50))
        self.ninja_item.spawn_object(self.space, 2, position=(400,50))
        self.ninja_item.spawn_object(self.space, 3, position=(100,350))
        self.ninja_item.spawn_object(self.space, 4, position=(400,350))
        self.options.append(self.ninja_item)
        self.yolo_model = YOLO('resources/models/yolov8l-pose.pt')  # load an official model
        self.background = cv2.imread("resources/dojo.png", cv2.IMREAD_UNCHANGED)
        self.background = cv2.cvtColor(self.background, cv2.COLOR_BGRA2RGBA)
        self.background = cv2.resize(self.background, (self.camera_width, self.camera_height))
        self.player = CVNinjaPlayer(5)
        self.space.add(self.player.line_left_hand_body, self.player.line_left_hand_shape)
        self.space.add(self.player.line_right_hand_body, self.player.line_right_hand_shape)
        self.space.add(self.player.line_left_leg_body, self.player.line_left_leg_shape)
        self.space.add(self.player.line_right_leg_body, self.player.line_right_leg_shape)
        handler = self.space.add_collision_handler(5, 1)
        handler.data["player"] = self.player # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
        handler.begin = self.process_hit


        

        print("Setting up")
    def update(self, image):

        height, width, _ = image.shape
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.flip(image, 1)

        image.flags.writeable = False  
        results = self.yolo_model(image, max_det=1, verbose=False)
        image.flags.writeable = True  

        self.space.step(1/60)
        image = Generics.overlayPNG(image, self.background, pos=[0, 0])
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

        for object_spawner in self.options:
               for shape in object_spawner.pymunk_objects_to_draw:
                    image = Generics.draw_pymunk_object_in_opencv(image, shape)

        
        if cv2.waitKey(1) & 0xFF == 27:
            self.should_switch = True
            self.next_game = None
        return cv2.putText(image, "Main Menu", (10, 30),
                         cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 

    def cleanup(self):
        pass

    def get_next_game(self):
        return self.next_game

    def process_hit(self, arbiter, space, data):
        # Get objects that were involved in collision
        kinematic_shape = arbiter.shapes[0]
        shape_trail_length = data["player"].get_trailing_length_by_limb(kinematic_shape.player_limb)
        print("Hit with ", kinematic_shape.player_limb)
        for shape in arbiter.shapes:
            if(shape.body.body_type != pymunk.Body.KINEMATIC):
                if(shape_trail_length > 10): 
                    self.should_switch = True
                    self.next_game = self.games[shape.collision_type-1]
                    print(shape.collision_type)
                else:
                    print("Trail not long enough: ",shape_trail_length )
        return True
    

