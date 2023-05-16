import time
import cv2
from utils import Generics
import math
from shapely.geometry import LineString, Polygon
class CVNinjaPlayer:

    def __init__(self):
        score = 0
        spawn_time = time.time()
        # Init tracking
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

    def update_tracking(self, keypoints):
        left_wrist = (int(keypoints[9][0]), int(keypoints[9][1]))
        left_elbow = (int(keypoints[7][0]), int(keypoints[7][1]))
        
        right_wrist = (int(keypoints[10][0]), int(keypoints[10][1]))
        right_elbow = (int(keypoints[8][0]), int(keypoints[8][1]))

        left_ankle = (int(keypoints[15][0]), int(keypoints[15][1]))
        left_knee = (int(keypoints[13][0]), int(keypoints[13][1]))

        right_ankle = (int(keypoints[16][0]), int(keypoints[16][1]))
        right_knee = (int(keypoints[14][0]), int(keypoints[14][1]))

        new_left_hand_coords = Generics.create_additional_keypoint(left_wrist, left_elbow)
        new_right_hand_coords =  Generics.create_additional_keypoint(right_wrist, right_elbow)
        new_left_foot_coords =  Generics.create_additional_keypoint(left_ankle, left_knee)
        new_right_foot_coords = Generics.create_additional_keypoint(right_ankle, right_knee)

        # Calculate distance between each limb's coordinates
        distance_left_hand = math.hypot(
            new_left_hand_coords[0]-self.left_hand_track_previous_point[0], 
            new_left_hand_coords[1]-self.left_hand_track_previous_point[1]
            )
        distance_right_hand = math.hypot(
            new_right_hand_coords[0]-self.right_hand_track_previous_point[0], 
            new_right_hand_coords[1]-self.right_hand_track_previous_point[1]
            )
        distance_right_foot = math.hypot(
            new_right_foot_coords[0]-self.right_foot_track_previous_point[0], 
            new_right_foot_coords[1]-self.right_foot_track_previous_point[1]
            )
        distance_left_foot = math.hypot(
            new_left_foot_coords[0]-self.left_foot_track_previous_point[0], 
            new_left_foot_coords[1]-self.left_foot_track_previous_point[1]
            )

        self.left_hand_track_points.append(new_left_hand_coords)
        self.right_hand_track_points.append(new_right_hand_coords)
        self.right_foot_track_points.append(new_right_foot_coords)
        self.left_foot_track_points.append(new_left_foot_coords)

        self.left_hand_track_lengths.append(distance_left_hand)
        self.right_hand_track_lengths.append(distance_right_hand)
        self.right_foot_track_lengths.append(distance_right_foot)
        self.left_foot_track_lengths.append(distance_left_foot)

        self.left_hand_track_current += distance_left_hand
        self.right_hand_track_current += distance_right_hand
        self.right_foot_track_current += distance_right_foot
        self.left_foot_track_current += distance_left_foot

        self.left_hand_track_previous_point = new_left_hand_coords 
        self.right_hand_track_previous_point =  new_right_hand_coords
        self.right_foot_track_previous_point = new_right_foot_coords
        self.left_foot_track_previous_point =  new_left_foot_coords 

       
    def addScore(self, current_time):
        hitTime = (current_time - self.spawn_time)
        self.score += int(100 - hitTime * 5) 
        self.spawn_time = time.time()

    # def draw_tracking_lines(self, image):
    #     for i, point in enumerate(self.left_hand_track_points): # any track point will do
    #         if i != 0:
    #             cv2.line(image, self.left_hand_track_points[i-1], self.left_hand_track_points[i], (0,0,255),2)
    #             cv2.line(image, self.right_hand_track_points[i-1], self.right_hand_track_points[i], (0,0,255),2)
    #             cv2.line(image, self.right_foot_track_points[i-1], self.right_foot_track_points[i], (0,0,255),2)
    #             cv2.line(image, self.left_foot_track_points[i-1], self.left_foot_track_points[i], (0,0,255),2)

    def get_trailing(self, image):
        for i, point in enumerate(self.left_hand_track_points): # any track point will do
                if i != 0:
                    cv2.line(image, self.left_hand_track_points[i-1], self.left_hand_track_points[i], (0,0,255),5)
                    cv2.line(image, self.right_hand_track_points[i-1], self.right_hand_track_points[i], (0,0,255),5)
                    cv2.line(image, self.right_foot_track_points[i-1], self.right_foot_track_points[i], (0,0,255),5)
                    cv2.line(image, self.left_foot_track_points[i-1], self.left_foot_track_points[i], (0,0,255),5)
        

    def check_hit(self, image, woodLine):
        
        line_left_hand = LineString([self.left_hand_track_points[-1], self.left_hand_track_points[0]])
        line_right_hand = LineString([self.right_hand_track_points[-1], self.right_hand_track_points[0]])
        line_right_foot = LineString([self.right_foot_track_points[-1], self.right_foot_track_points[0]])
        line_left_foot = LineString([self.left_foot_track_points[-1], self.left_foot_track_points[0]])

        if(line_left_hand.intersects(woodLine) or line_right_hand.intersects(woodLine) 
            or line_right_foot.intersects(woodLine) or line_left_foot.intersects(woodLine)):
            
            self.left_hand_track_points = []
            self.left_hand_track_lengths = []

            self.right_hand_track_points = []
            self.right_hand_track_lengths = []

            self.right_foot_track_points = []
            self.right_foot_track_lengths = []

            self.left_foot_track_points = []
            self.left_foot_track_lengths = []
            return True

        self.left_hand_track_points = self.left_hand_track_points[-2:]
        self.left_hand_track_lengths = self.left_hand_track_lengths [-2:]

        self.right_hand_track_points = self.right_hand_track_points[-2:]
        self.right_hand_track_lengths = self.right_hand_track_lengths[-2:]

        self.right_foot_track_points = self.right_foot_track_points[-2:]
        self.right_foot_track_lengths = self.right_foot_track_lengths[-2:]

        self.left_foot_track_points = self.left_foot_track_points[-2:]
        self.left_foot_track_lengths = self.left_foot_track_lengths[-2:]
        return False