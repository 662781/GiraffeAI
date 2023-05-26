import cv2
from utils import Generics
import pymunk
import numpy as np

'''
The goal of this object is to be created once and used constantly (at random)
Once created it will be called to spawn its specific object into the space and add it to the list of items to be drawn by opencv.
Each "Whole" pymunk_object has a reference to its parent called "patent_object".
From that we can call the collision_aftermath method from the collisionHandler in pymunk
The class will then:
    - remove the collided object from the list of objects to draw
    - spawn the broken object's pieces into the given space 
    - add the pieces to the list of objects to draw. 
'''

class CVNinjaObject():
    
    

    def __init__(self, image, size: int):
        # list of items that need to be drawn on frame for the object.
        self.pymunk_objects_to_draw = [] 
    
        # list of vertices and spliced images for the object and its pieces, All predefined by the child object's constructor
        self.images_vertices =  {} # denoted as "key": vertices
        
        self.size = size # for now width and height will be the same
        self.image = cv2.resize(image, (self.size, self.size), interpolation=cv2.INTER_LINEAR)

    def collision_aftermath(self, space, shape, contact_point):
        # Used to handle interactions specific to objects (wood is cut, rock is crushed, bomb explodes)
        pass

    def _get_images_vertices(self):
        # base implementation gets vertices for the "whole" object
        self.images_vertices["WHOLE"] = (self.image, Generics.get_vertices_by_image(self.image))

    def spawn_object(self, space, collision_type, position=(50,50)):
        # todo: shoot up physics.
        # Set the "whole" object as standard object to spawn
        body = pymunk.Body(1, 100)
        body.position = position
        
        shape = pymunk.Poly(body, self.images_vertices["WHOLE"][1])
        shape.parent_object = self # For retrieval during collision
        shape.collision_type = collision_type
        space.add(shape, body)
        shape.image = self.image
        self.pymunk_objects_to_draw.append(shape)
