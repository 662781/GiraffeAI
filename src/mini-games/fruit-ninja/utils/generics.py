import numpy as np
import cv2

class Generics():

    @staticmethod
    def _create_line_function(point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        if(x2 - x1) == 0: # Slope would be infinte, let the other method handle it
            def line_function(x):
                return None
        else:
            m = (y2 - y1) / (x2 - x1)
            b = y1 - m * x1
            def line_function(x):
                y = m * x + b
                return y
        return line_function

    @staticmethod
    def create_additional_keypoint(wrist, elbow):
        keypoint1 = wrist
        keypoint2 = elbow
        
        keypoint_x = keypoint1[0] - ((keypoint2[0] - keypoint1[0]) / 2) # divide by two to avoid overreach
        line_func = Generics._create_line_function(keypoint2, keypoint1)
        keypoint_y = line_func(keypoint_x)
        if(keypoint_y is None): # on infinite slope, take an y relative to the other y coords 
            keypoint_y = keypoint1[1] - ((keypoint2[1] - keypoint1[1]) / 2)

        new_keypoint = (int(keypoint_x), int(keypoint_y)) # coordinates are only useful as rounded integers
        return new_keypoint

    @staticmethod
    def overlayPNG(imgBack, imgFront, pos=[0, 0]):
        hf, wf, cf = imgFront.shape
        hb, wb, cb = imgBack.shape
        *_, mask = cv2.split(imgFront)
        maskBGRA = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGRA)
        maskBGR = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        imgRGBA = cv2.bitwise_and(imgFront, maskBGRA)
        imgRGB = cv2.cvtColor(imgRGBA, cv2.COLOR_BGRA2BGR)

        imgMaskFull = np.zeros((hb, wb, cb), np.uint8)
        imgMaskFull[pos[1]:hf + pos[1], pos[0]:wf + pos[0], :] = imgRGB
        imgMaskFull2 = np.ones((hb, wb, cb), np.uint8) * 255
        maskBGRInv = cv2.bitwise_not(maskBGR)
        imgMaskFull2[pos[1]:hf + pos[1], pos[0]:wf + pos[0], :] = maskBGRInv

        imgBack = cv2.bitwise_and(imgBack, imgMaskFull2)
        imgBack = cv2.bitwise_or(imgBack, imgMaskFull)

        return imgBack

    @staticmethod
    def draw_stick_figure(image, keypoints):
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
        width = 20
        color = (255, 255, 255)
        # Head
        cv2.circle(image, (int(keypoints[0][0]), int(keypoints[0][1])), 20, color, -1)
        # Right arm
        cv2.line(image, right_elbow, (int(keypoints[5][0]), int(keypoints[5][1])), color, width)
        cv2.line(image, right_wrist, right_elbow, color, width)
        cv2.line(image, right_wrist, new_right_hand_coords,color, width)
        # Left arm
        cv2.line(image, left_elbow, (int(keypoints[6][0]), int(keypoints[6][1])), color, width)
        cv2.line(image, left_wrist, left_elbow, color, width)
        cv2.line(image, left_wrist, new_left_hand_coords, color, width)
        # Right leg
        cv2.line(image, right_knee, (int(keypoints[11][0]), int(keypoints[11][1])), color, width)
        cv2.line(image, right_ankle, right_knee, color, width)
        cv2.line(image, right_ankle, new_right_foot_coords, color, width)
        # Left leg
        cv2.line(image, left_knee, (int(keypoints[12][0]), int(keypoints[12][1])), color, width)
        cv2.line(image, left_ankle, left_knee, color, width)
        cv2.line(image, left_ankle, new_left_foot_coords, color, width)
