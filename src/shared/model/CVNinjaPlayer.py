import time
import cv2
import math
import pymunk
from shared.utils import Generics


class CVNinjaPlayer:
    """Represents a player in the CV Ninja game.

    The CVNinjaPlayer is primarily used as a player class for the CVNinjaGame, it gained an additional use as the player in the Menus.
    The class tracks the limbs of the player and keeps their score.
    Using the collected tracking, the player leaves behind 'trails' which can be used to determine whether the player performed a slashing motion. 

    """


    def __init__(self, collision_type):
        self.score = 0
        self.strikes = 0 # Ammount of strikes, at 3 it's game over.
        self.collision_type = collision_type
        self.status = "" # used to determine winner or loser for fruitninja

        self._setup_shapes(collision_type)
        
        self.left_hand_track_points = []
        self.left_hand_track_lengths = []
        self.left_hand_track_current = 0
        self.left_hand_track_previous_point = 0,0
        
        self.right_hand_track_points = []
        self.right_hand_track_lengths = []
        self.right_hand_track_current = 0
        self.right_hand_track_previous_point = 0,0

        self.right_foot_track_points = []
        self.right_foot_track_lengths = []
        self.right_foot_track_current = 0
        self.right_foot_track_previous_point = 0,0

        self.left_foot_track_points = []
        self.left_foot_track_lengths = []
        self.left_foot_track_current = 0
        self.left_foot_track_previous_point = 0,0

        self.distance_right_foot = 0
        self.distance_left_foot = 0
        self.distance_right_hand = 0
        self.distance_left_hand = 0 

    def _setup_shapes(self, collision_type):
        # Initialize the shapes used in the background for collision. 
        self.line_left_hand_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.line_left_hand_shape = pymunk.Poly(self.line_left_hand_body, [(10000, 0), (10001, 0)])
        self.line_left_hand_shape.collision_type = collision_type
        self.line_left_hand_shape.player_limb = "left hand"

        self.line_right_hand_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.line_right_hand_shape = pymunk.Poly(self.line_right_hand_body, [(10000, 0), (10001, 0)])
        self.line_right_hand_shape.collision_type = collision_type
        self.line_right_hand_shape.player_limb = "right hand"

        # Left leg 
        self.line_left_leg_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.line_left_leg_shape = pymunk.Poly(self.line_left_leg_body, [(10000, 0), (10001, 0)])
        self.line_left_leg_shape.collision_type = collision_type
        self.line_left_leg_shape.player_limb = "left leg"


        self.line_right_leg_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.line_right_leg_shape = pymunk.Poly(self.line_right_leg_body, [(10000, 0), (10001, 0)])
        self.line_right_leg_shape.collision_type = collision_type
        self.line_right_leg_shape.player_limb = "right leg"

    def update_tracking(self, keypoints):
        right_wrist = (int(keypoints[9][0]), int(keypoints[9][1]))
        right_elbow = (int(keypoints[7][0]), int(keypoints[7][1]))
        
        left_wrist = (int(keypoints[10][0]), int(keypoints[10][1]))
        left_elbow = (int(keypoints[8][0]), int(keypoints[8][1]))

        right_ankle = (int(keypoints[15][0]), int(keypoints[15][1]))
        right_knee = (int(keypoints[13][0]), int(keypoints[13][1]))

        left_ankle = (int(keypoints[16][0]), int(keypoints[16][1]))
        left_knee = (int(keypoints[14][0]), int(keypoints[14][1]))

        new_left_hand_coords = Generics.create_additional_keypoint(left_wrist, left_elbow)
        new_right_hand_coords =  Generics.create_additional_keypoint(right_wrist, right_elbow)
        new_left_foot_coords =  Generics.create_additional_keypoint(left_ankle, left_knee)
        new_right_foot_coords = Generics.create_additional_keypoint(right_ankle, right_knee)

        # Calculate distance between each limb's coordinates
        self.distance_left_hand = math.hypot(
            new_left_hand_coords[0]-self.left_hand_track_previous_point[0], 
            new_left_hand_coords[1]-self.left_hand_track_previous_point[1]
            )
        self.distance_right_hand = math.hypot(
            new_right_hand_coords[0]-self.right_hand_track_previous_point[0], 
            new_right_hand_coords[1]-self.right_hand_track_previous_point[1]
            )
        self.distance_right_foot = math.hypot(
            new_right_foot_coords[0]-self.right_foot_track_previous_point[0], 
            new_right_foot_coords[1]-self.right_foot_track_previous_point[1]
            )
        self.distance_left_foot = math.hypot(
            new_left_foot_coords[0]-self.left_foot_track_previous_point[0], 
            new_left_foot_coords[1]-self.left_foot_track_previous_point[1]
            )

        self.left_hand_track_points.append(new_left_hand_coords)
        self.right_hand_track_points.append(new_right_hand_coords)
        self.right_foot_track_points.append(new_right_foot_coords)
        self.left_foot_track_points.append(new_left_foot_coords)

        self.left_hand_track_lengths.append(self.distance_left_hand)
        self.right_hand_track_lengths.append(self.distance_right_hand)
        self.right_foot_track_lengths.append(self.distance_right_foot)
        self.left_foot_track_lengths.append(self.distance_left_foot)

        self.left_hand_track_current += self.distance_left_hand
        self.right_hand_track_current += self.distance_right_hand
        self.right_foot_track_current += self.distance_right_foot
        self.left_foot_track_current += self.distance_left_foot

        self.left_hand_track_previous_point = new_left_hand_coords 
        self.right_hand_track_previous_point =  new_right_hand_coords
        self.right_foot_track_previous_point = new_right_foot_coords
        self.left_foot_track_previous_point =  new_left_foot_coords 

       
    def addScore(self, current_time):
        hitTime = (current_time - self.spawn_time)
        self.score += int(100 - hitTime * 5) 
        self.spawn_time = time.time()

    def get_trailing(self, image):
        for i, point in enumerate(self.left_hand_track_points): # any track point will do
                if i != 0:
                    cv2.line(image, self.left_hand_track_points[i-1], self.left_hand_track_points[i], (0,0,255),5)
                    cv2.line(image, self.right_hand_track_points[i-1], self.right_hand_track_points[i], (0,0,255),5)
                    cv2.line(image, self.right_foot_track_points[i-1], self.right_foot_track_points[i], (0,0,255),5)
                    cv2.line(image, self.left_foot_track_points[i-1], self.left_foot_track_points[i], (0,0,255),5)
        

    def get_trailing_length_by_limb(self,limb:str):
        if (limb == "right leg"):
            return self.distance_right_foot
        elif (limb == "left leg"):
            return self.distance_left_foot
        elif (limb == "right hand"):
            return self.distance_right_hand
        elif (limb == "left hand"):
            return self.distance_left_hand
        return 0
    
    def reset_keypoints(self):
        self.left_hand_track_points = self.left_hand_track_points[-2:]
        self.left_hand_track_lengths = self.left_hand_track_lengths [-2:]

        self.right_hand_track_points = self.right_hand_track_points[-2:]
        self.right_hand_track_lengths = self.right_hand_track_lengths[-2:]

        self.right_foot_track_points = self.right_foot_track_points[-2:]
        self.right_foot_track_lengths = self.right_foot_track_lengths[-2:]

        self.left_foot_track_points = self.left_foot_track_points[-2:]
        self.left_foot_track_lengths = self.left_foot_track_lengths[-2:]

        self.right_hand_track_current = 0
        self.left_hand_track_current = 0
        self.right_foot_track_current = 0
        self.left_foot_track_current = 0