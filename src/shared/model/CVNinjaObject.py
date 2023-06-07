import cv2
from shared.utils import Generics, CVAssets
import pymunk
import numpy as np
import time
from preferredsoundplayer import playsound


'''
The goal of this object is to be created once and used constantly (at random), primarily for the CVNinja game
Once created it will be called to spawn its specific object into the space and add it to the list of items to be drawn by opencv.
Each "Whole" pymunk_object has a reference to its spawner class called "parent_object".
From that we can call the collision_aftermath method from the collisionHandler in pymunk
The class will then:
    - remove the collided object from the list of objects to draw
    - spawn the broken object's pieces into the given space 
    - add the pieces to the list of objects to draw. 
'''

class CVNinjaObject():
    """An abstract class used as the base for all objects in CVNinja, overtime it has found use as a generic menu object as well.

    Originally, the CVNinjaObject was an absract class meant for objects used the the CVNinja game.
    Now it serves an additional purpose in the form of interactive buttons used in CVGame Menus.
    The objects use the Pymunk library to simulate object physics in the background, which will be used by opencv to draw to the screen  

    Attributes:
        pymunk_objects_to_draw (array): An array of pymunk objects that opencv must draw to the screen every frame.
        images_vertices (Dict[str, array]): An array of vertices required to make make the shape of the object the same as the used image
        size (int): the size the object needs to be. For now, width and height share the same value.
        image (np.ndarray): the base image that the object will be drawn as.  
    """

    def __init__(self, image, size: int):
        """Intialize the CVNinjaObject

        Args:
            image (np.ndarray): The base image for the object
            size (int): The size of the object 
        """
        self.pymunk_objects_to_draw = [] 
        self.images_vertices =  {}
        self.size = size 
        self.image = cv2.resize(image, (self.size, self.size), interpolation=cv2.INTER_LINEAR)

    def collision_aftermath(self, space, shape, contact_point):
        """Handle interactions specific to objects after a collision occurs.

        This method is used to handle interactions that are specific to objects,
        such as cutting wood, crushing rocks, or exploding bombs, after a collision
        has occurred.

        Args:
            space (pymunk.Space): The pymunk space in which the collision occurred.
            shape (pymunk.Poly): The shape object representing the colliding object.
            contact_point (Tuple[float,float]): The point of contact between the colliding objects.

        Returns:
            None
        """
        pass

    def _get_images_vertices(self):
        """Get the vertices of the image for the object.

            This is the base implementation that retrieves the vertices for the "whole"
            object image. The vertices are obtained using the 'Generics.get_vertices_by_image()' method.
            Each object has a "whole" and a "broken" form. A broken form requires multiple images and multiple shape to draw
            Objects will define these forms here and they will be applied when spawning the object

            Returns:
                None
        """
        self.images_vertices["WHOLE"] = (self.image, Generics.get_vertices_by_image(self.image))

    def spawn_object(self, space, collision_type, position=(50,50), play_sound = False):
        """Spawn an object and append it to the list of objects to be drawn.

        This method spawns a physics object in the given pymunk space with the specified
        collision_type and position. The object is associated with the "whole"
        image and added to the 'pymunk_objects_to_draw' list for rendering.

        Args:
            space (pymunk.Space): The physical space or environment in which to spawn the object.
            collision_type (int): The collision type associated with the object.
            position (Tuple[float,float]): The position of the object (default: (50, 50)).
            
        Returns:
            The pymunk_shape that was spawned 
        """
        body = pymunk.Body(1, 100)
        body.position = position
        
        shape = pymunk.Poly(body, self.images_vertices["WHOLE"][1])
        shape.parent_object = self # For retrieval during collision
        shape.collision_type = collision_type
        space.add(shape, body)
        shape.image = self.image
        shape.spawn_time= time.time()
        self.pymunk_objects_to_draw.append(shape)
        if play_sound:
            playsound(CVAssets.AUDIO_OBJECT_SPAWN, block = False)
        # optional return of the object
        return shape

    def collision_requirements_are_met(self, player = None, collided_shape = None):
        """Used by an child object to set their own requirements before the object hit is valid"""
        return True

    def calculate_score(self, shape, double_points:bool = False):
        """Calculate score based on the time it took to cut the object, score can be doubled"""
        baseline_score = 10
        max_time_limit = 10
        time_taken =  time.time() - shape.spawn_time
        time_taken = round(time_taken, 2)
        if (time_taken < 0.09): # must be lucky hit, too lucky
            time_taken += 0.2
        time_factor = max_time_limit / time_taken
        
        score = int(time_factor * baseline_score * (double_points+1)) # double_points is either 0 or 1, + 1 means score is doubled or remains the same
        print("With a time of ", time_taken, " Score is calculated as:")
        print(time_factor, " * ", baseline_score, " * ", "(", double_points+1, ")" )
        print("Yields ", score)
        return score


    def _get_spliced_image_vertices_combo(self, amount_of_slices: int = 2, start_diagonally: bool = False):
        """Helper method to calculate to get the sliced images and their vertices in one array
           Originally we setup pieces of the image by cutting them out of the image and adjusting the position of the pieces relative
            to where the cut was made.
           Now we figured out that by keeping the original image size with zeros copy, we can put the part of the image on it,
           and now the original position can stay the same, which saves a lot of headaches calculating new postions. 
        
        Args:
            amount_of_slices (int): The amount of slices of the object you want to have

            start_diagonally (bool): Tell the function to first cut the object in two diagonally (bottom left to top right). 
                                     This will result in double the amount_of_slices you request: 2 slices will result in 4 etc. 
        """
        results = []
        height = self.image.shape[0]
        width = self.image.shape[1]
        # Depending on whether we start diagonal or not, we use either the width (shape[1]) or height (shape[0])
        
        slice_metric = height // amount_of_slices
        base_images = [self.image]
        if start_diagonally:
            # An initial splice diagonally, each of which will be cut into the number of slices requested
            diagonal_splice_left = np.zeros_like(self.image, dtype=np.uint8)
            diagonal_splice_right = np.zeros_like(self.image, dtype=np.uint8)
            for i in range(self.size):
                diagonal_splice_left[i, :self.size-i] = self.image[i, :self.size-i]
                diagonal_splice_right[i, self.size-i:] = self.image[i, self.size-i:]
            base_images = [diagonal_splice_left, diagonal_splice_right]
        
            for base_image in base_images:
                for i in range(amount_of_slices):
                    horizontal_slice = np.zeros_like(base_image, dtype=np.uint8)
                    start_row = i * slice_metric
                    end_row = (i + 1) * slice_metric
                    horizontal_slice[start_row:end_row, :] = base_image[start_row:end_row, :]
                    results.append((horizontal_slice, Generics.get_vertices_by_image(horizontal_slice)))
        else:
            slice_width = width // amount_of_slices
            for i in range(0, width, slice_width):
                vertical_slice = np.zeros_like(self.image, dtype=np.uint8)
                # Calculate the start and end coordinates of the slice
                start_x = i
                end_x = i + slice_width

                # Extract the slice from the image
                vertical_slice[:, start_x:end_x, :] = self.image[:, start_x:end_x, :]
                results.append((vertical_slice, Generics.get_vertices_by_image(vertical_slice)))

        return results
            