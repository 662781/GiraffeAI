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
    - remove the collided object from the list of objects to spawn
    - spawn the broken object's pieces into the given space 
    - add the pieces as to the list of objects to spawn. 
'''

class CVNinjaObject():
    pymunk_objects_to_draw = [] # list of items that need to be drawn on frame for the object. Denoted as assoc array: {image:, shape:}
    pymunk_objects_broken =  {} # list of parts of the object, each item denoted as "key": (image,shape)
    
    def __init__(self, image, size: int):
        self.size = size # for now width and height will be the same
        self.image = cv2.resize(image, (self.size, self.size), interpolation=cv2.INTER_LINEAR)
       

    def _append_object_to_spawn(self, image, shape):
        # made just so I don't have to type the stupid assoc key value everytime, maybe I'll change it some day
        self.pymunk_objects_to_draw.append({"image": image, "shape": shape}) 

    def collision_aftermath(self, space, shape, contact_point):
        # Used to handle interactions specific to objects (wood is cut, rock is crushed, bomb explodes)
        pass

    def spawn_object(self, space):
        # Set the "whole" object as standard object to spawn
        body = pymunk.Body(1, 100)
        body.position = (50,200)
        shape = pymunk.Poly(body, Generics.get_vertices_by_image(self.image))
        shape.parent_object = self # For retrieval during collision
        self._append_object_to_spawn(self.image, shape)
