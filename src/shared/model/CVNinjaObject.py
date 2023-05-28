import cv2
from shared.utils import Generics
import pymunk
import numpy as np

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

    def spawn_object(self, space, collision_type, position=(50,50)):
        """Spawn an object and append it to the list of objects to be drawn.

        This method spawns a physics object in the given pymunk space with the specified
        collision_type and position. The object is associated with the "whole"
        image and added to the 'pymunk_objects_to_draw' list for rendering.

        Args:
            space (pymunk.Space): The physical space or environment in which to spawn the object.
            collision_type (int): The collision type associated with the object.
            position (Tuple[float,float]): The position of the object (default: (50, 50)).
            
        Returns:
            None
        """
        body = pymunk.Body(1, 100)
        body.position = position
        
        shape = pymunk.Poly(body, self.images_vertices["WHOLE"][1])
        shape.parent_object = self # For retrieval during collision
        shape.collision_type = collision_type
        space.add(shape, body)
        shape.image = self.image
        self.pymunk_objects_to_draw.append(shape)
