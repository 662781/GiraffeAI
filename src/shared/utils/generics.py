import numpy as np
import cv2
import pymunk
from PIL import ImageFont, ImageDraw, Image

class Generics():
    """Generic class with useful methods from line functions to image manipulation

    Generics is a collection of static methods that give games acces to a variety of useful methods.

    Attributes:
        font (ImageFont): A predetermined font used throughout the games. 
    """

    # Predefined font workaround for custom font method
    font = ImageFont.truetype("shared/assets/go3v2.ttf", 80)
    
    @staticmethod
    def _create_line_function(point1, point2):
        """Creates a line function given two points.

        This method creates a line function using the two provided points.
        If the line has an infinite slope, the line function returns None for any input x-coordinate.
        Otherwise, it calculates the slope (m) and y-intercept (b) of the line using the formula y = mx + b.
        The line function takes an x-coordinate as input and calculates the corresponding y-coordinate using the slope and y-intercept.
        Args:
            point1 (tuple): The coordinates (x, y) of the first point.
            point2 (tuple): The coordinates (x, y) of the second point.

        Returns:
            function: A line function that takes an x-coordinate as input and returns the corresponding y-coordinate.
        """
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
        """Creates an additional keypoint based on two existing keypoints. 
        
        This method calculates the coordinates of a new keypoint on the palm based on the provided wrist and elbow keypoints.
        Primarily used to calculate a palm keypoint from a wrist and elbow keypoint, as YOLO models do not support hand keypoints

        Args:
            wrist (tuple): The coordinates (x, y) of the wrist keypoint.
            elbow (tuple): The coordinates (x, y) of the elbow keypoint.

        Returns:
            tuple: The coordinates (x, y) of the newly created keypoint on the palm.

        Note:
            
            It uses line function math to create a line between the two points and finds the midpoint on that line.
            If the line has an infinite slope, the new keypoint is positioned vertically between the two y-coordinates of the existing keypoints.
            The resulting coordinates are rounded to integers before being returned.
        """
        keypoint1 = wrist
        keypoint2 = elbow
        
        keypoint_x = keypoint1[0] - ((keypoint2[0] - keypoint1[0]) / 2) # divide by two to avoid overreach
        line_func = Generics._create_line_function(keypoint2, keypoint1)
        keypoint_y = line_func(keypoint_x)
        if(keypoint_y is None): # on infinite slope, take a y relative to the other y coords 
            keypoint_y = keypoint1[1] - ((keypoint2[1] - keypoint1[1]) / 2)

        new_keypoint = (int(keypoint_x), int(keypoint_y)) # coordinates are only useful as rounded integers
        return new_keypoint

    @staticmethod
    def overlayPNG(imgBack, imgFront, pos=[0, 0]):
        """Apply an image to another image.

        This function applies overlay of a PNG image on top of another image.

        Args:
            imgBack (ndarray): Background image on which the overlay is applied.
            imgFront (ndarray): PNG image to be overlaid on the background image.
            pos (list, optional): Position of the top-left corner of the overlay image on the background image.
                                Defaults to [0, 0].

        Returns:
            ndarray: The resulting image after applying the overlay.

        Note:
            This method handles out-of-bounds overlays by preventing them from occurring and returning the
            original background image. If any errors occur during the overlay process, the original background
            image is returned without the overlay.
        """

        try:
            hf, wf, cf = imgFront.shape
            hb, wb, cb = imgBack.shape
            if(pos[0] > wb or pos[1] > hb): # prevent out of bounds overlays
                return imgBack
            *_, mask = cv2.split(imgFront)
            maskBGRA = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGRA)
            maskBGR = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            imgRGBA = cv2.bitwise_and(imgFront, maskBGRA)
            imgRGB = cv2.cvtColor(imgRGBA, cv2.COLOR_BGRA2BGR)

            y1, y2 = max(0, pos[1]), min(hf + pos[1], hb)
            x1, x2 = max(0, pos[0]), min(wf + pos[0], wb)
            imgMaskFull = np.zeros((hb, wb, cb), np.uint8)
            # The original method is crap for partially visible images, I Adjusted MaskFull and MaskFull2 to function even if the image is partially out of bounds
            imgMaskFull[y1:y2, x1:x2, :] = imgRGB[(y1-pos[1]):(y2-pos[1]), (x1-pos[0]):(x2-pos[0]), :]
            imgMaskFull2 = np.ones((hb, wb, cb), np.uint8) * 255
            maskBGRInv = cv2.bitwise_not(maskBGR)
            imgMaskFull2[y1:y2, x1:x2, :] = maskBGRInv[(y1-pos[1]):(y2-pos[1]), (x1-pos[0]):(x2-pos[0]), :]

            imgBack = cv2.bitwise_and(imgBack, imgMaskFull2)
            imgBack = cv2.bitwise_or(imgBack, imgMaskFull)
            return imgBack
        except:
            # Other problems don't affect application performance so generic catch and pass it back
            return imgBack

    @staticmethod
    def get_vertices_by_image(image):
        """Get the vertices from the image

        Retrieves the contour coordinates from an image and returns them as vertices.

        Args:
            image (ndarray): The input image from which contours are extracted.

        Returns:
            list: A list of vertex coordinates representing the contours in the image.

        Note:
            This method uses the alpha channel of the image to determine the contours.
            It converts the alpha channel to a binary threshold and extracts the contours
            using OpenCV's findContours function. The resulting contour coordinates are
            added as vertices to the returned list.
        """
        vertices = []
        alpha_channel = image[:,:,3]
        _, threshold = cv2.threshold(alpha_channel, 0, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            for vertex in contour:
                x, y = vertex[0]
                vertices.append((x, y))
        return vertices


    @staticmethod
    def draw_pymunk_object_in_opencv(background, pymunk_object):
        """Draw a pymunk object with opencv on the given image
        
        This method retrieves the position of the Pymunk object and uses the `overlayPNG` method
            to draw the object's image on the background at the specified position. The modified image
            with the drawn object is returned.

        Args:
            background (ndarray): The background image on which the object will be drawn.
            pymunk_object (pymunk.Poly): The Pymunk physics object to be drawn.

        Returns:
            ndarray: The resulting image after drawing the Pymunk object.
        """
        # Uncomment to debug the created poly
        #vertices = [(v+pymunk_object.body.position) for v in pymunk_object.get_vertices()]
        #vertices = np.array(vertices, dtype=np.int32)
        #cv2.fillPoly(background, [vertices], (255, 255, 255))
        pos = pymunk_object.body.position
        x, y = int(pos.x), int(pos.y)
        background = Generics.overlayPNG(background, pymunk_object.image, [x, y])
        return background

    @staticmethod
    def put_text_with_ninja_font(image, text, position, font_color, outline_color = (255, 255, 255), outline_width=2):
        """Adds text to an image using the preset Fruit Ninja Font and Size.
        
        Sadly, opencv does not support custom fonts without recompiling the library with the required 3rd party flags. 
        This forces us to use PIL, which has the drawback that we can't dynamically set the font size. So we predefine it in the class.
        If really necessary, it can be done by recreating the font altogether, but that means you reload the font (22kb) with every frame 

        Args:
            image (ndarray): The image to which the text will be added.
            text (str): The text to be added.
            position (tuple): The position (x, y) where the text will be placed on the image.
            font_path (str): The file path to the custom font.
            font_size (int): The size of the font.
            font_color (tuple): The color of the font in RGB format.
            outline_color (tuple, optional): The color of the outline in RGB format. Defaults to (255, 255, 255).
            outline_width (int, optional): The width of the outline. Defaults to 2.
        """
        img_pil = Image.fromarray(image)
        draw = ImageDraw.Draw(img_pil)
        outline_position = (50, 50)
        draw.text(position, text, font=Generics.font, fill=font_color, stroke_width = outline_width, stroke_fill = outline_color)
        return np.array(img_pil)

    @staticmethod
    def put_text_with_custom_font(image, text, position, font_path, font_size, font_color, outline_color = (255, 255, 255), outline_width=2):
        """Adds text to an image using a custom font.
        
        This method uses the PIL library to handle image manipulation. It converts the image to a PIL Image
            object and creates a draw object. The custom font is loaded and used to draw the text on the image at
            the specified position with the provided font color. Additionally, an outline can be added to the text
            using the outline color and width parameters. The modified image with the added text is returned as a NumPy array.
        
        Args:
            image (ndarray): The image to which the text will be added.
            text (str): The text to be added.
            position (tuple): The position (x, y) where the text will be placed on the image.
            font_path (str): The file path to the custom font.
            font_size (int): The size of the font.
            font_color (tuple): The color of the font in RGB format.
            outline_color (tuple, optional): The color of the outline in RGB format. Defaults to (255, 255, 255).
            outline_width (int, optional): The width of the outline. Defaults to 2.

        Returns:
            ndarray: The resulting image after adding the text.    
        """
        img_pil = Image.fromarray(image)
        draw = ImageDraw.Draw(img_pil)
        font = ImageFont.truetype(font_path, font_size)
        draw.text(position, text, font=font, fill=font_color, stroke_width = outline_width, stroke_fill = outline_color)
        return np.array(img_pil)



    @staticmethod
    def get_player_trailing(player, image):
        """Retrieves and draws the trailing lines of a player on an image.
        
        This method updates the vertices of the player's line shapes with the latest track points.
        It then draws lines using OpenCV's line function to represent the trailing lines on the image.

        Args:
            player (CVNinjaPlayer): The player object containing the trailing line information.
            image (ndarray): The image on which the trailing lines will be drawn.
        """
        # It's considered 'unsafe' because setting new vertices might result in unexpected physics, which does not apply to our use case.   
        player.line_left_leg_shape.unsafe_set_vertices([(player.left_foot_track_points[-1]), (player.left_foot_track_points[0])])
        player.line_right_leg_shape.unsafe_set_vertices([(player.right_foot_track_points[-1]), (player.right_foot_track_points[0])])
        player.line_left_hand_shape.unsafe_set_vertices([(player.left_hand_track_points[-1]),(player.left_hand_track_points[0])])
        player.line_right_hand_shape.unsafe_set_vertices([(player.right_hand_track_points[-1]),(player.right_hand_track_points[0])])
   

        # cv2.line(image, player.left_hand_track_points[-1], player.left_hand_track_points[0], (0, 0, 255), 5)
        # cv2.line(image, player.right_hand_track_points[-1], player.right_hand_track_points[0], (0, 0, 255), 5)
        # cv2.line(image, player.right_foot_track_points[-1], player.right_foot_track_points[0], (0, 0, 255), 5)
        # cv2.line(image, player.left_foot_track_points[-1], player.left_foot_track_points[0], (0, 0, 255), 5)

        shapes = [player.line_left_hand_shape, player.line_right_hand_shape,player.line_left_leg_shape, player.line_right_leg_shape]
        for shape in shapes:
            vertices = [(v+shape.body.position) for v in shape.get_vertices()]
            vertices = np.array(vertices, dtype=np.int32)
            cv2.fillPoly(image, [vertices], (0, 255, 0))
            # x1,y1 = int(shape.get_vertices()[0].x), int(shape.get_vertices()[0].y)
            # x2,y2 = int(shape.get_vertices()[1].x), int(shape.get_vertices()[1].y)

            # cv2.line(image, (x1,y1) ,(x2,y2) , (0,255,0),1)

    @staticmethod
    def determine_collision_side(object_pos, collision_pos):
        object_x, object_y = object_pos
        collision_x, collision_y = collision_pos

        # Calculate the difference between object position and collision point
        diff_x = collision_x - object_x
        diff_y = collision_y - object_y

        # Determine the side of collision based on the differences
        if abs(diff_x) > abs(diff_y):
            if diff_x > 0:
                return 'right'
            else:
                return 'left'
        else:
            if diff_y > 0:
                return 'bottom'
            else:
                return 'top'

    @staticmethod
    def draw_stick_figure(image, keypoints):
        # Draws a stick figure

        right_wrist = (int(keypoints[9][0]), int(keypoints[9][1]))
        right_elbow = (int(keypoints[7][0]), int(keypoints[7][1]))
        
        left_wrist = (int(keypoints[10][0]), int(keypoints[10][1]))
        left_elbow = (int(keypoints[8][0]), int(keypoints[8][1]))

        right_ankle = (int(keypoints[15][0]), int(keypoints[15][1]))
        right_knee = (int(keypoints[13][0]), int(keypoints[13][1]))

        left_ankle = (int(keypoints[16][0]), int(keypoints[16][1]))
        left_knee = (int(keypoints[14][0]), int(keypoints[14][1]))

        left_shoulder = (int(keypoints[6][0]), int(keypoints[6][1]))
        right_shouler = (int(keypoints[5][0]), int(keypoints[5][1]))

        left_hip = (int(keypoints[12][0]), int(keypoints[12][1]))
        right_hip = (int(keypoints[11][0]), int(keypoints[11][1]))

        new_left_hand_coords = Generics.create_additional_keypoint(left_wrist, left_elbow)
        new_right_hand_coords =  Generics.create_additional_keypoint(right_wrist, right_elbow)
        new_left_foot_coords =  Generics.create_additional_keypoint(left_ankle, left_knee)
        new_right_foot_coords = Generics.create_additional_keypoint(right_ankle, right_knee)
        width = 20
        color = (255, 255, 255)

        # Body
        cv2.line(image, left_shoulder, right_shouler, color, width-10)
        cv2.line(image, left_shoulder, left_hip, color, width-10)

        cv2.line(image, right_shouler, right_hip, color, width-10)
        cv2.line(image, right_hip, left_hip, color, width-10)

        # Head
        cv2.circle(image, (int(keypoints[0][0]), int(keypoints[0][1])), 20, color, -1)
        cv2.circle(image, (int(keypoints[1][0]), int(keypoints[1][1]) + 10), 4, (0,0,0), -1)
        cv2.circle(image, (int(keypoints[2][0]), int(keypoints[2][1]) + 10), 4, (0,0,0), -1)

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
