import cv2
from abc import ABC
import CVNinjaObjectState
from utils import Generics


class CVNinjaObject(ABC):
    pymunk_objects_to_spawn = [] # list of items that need to be drawn on frame for the object. Denoted as assoc array: {image:, shape:}
    pymunk_objects_broken =  []  # list of parts of the object, each item denoted as "key": (image,shape)
    vertices = {}
    def __init__(self, image, size: int)
        self.size = size # for now width and height will be the same
        self.image = cv2.resize(image, (self.size, self.size), interpolation=cv2.INTER_LINEAR)
        # Set the "whole" object as standard object to spawn
        body = pymunk.Body(1, 100)
        shape = pymunk.Poly(body, Generics.get_vertices_by_image(self.image))
        shape.parent_object = self # For retrieval during collision
        self._append_object_to_spawn.append(self.image, shape)

    @abstractmethod
    def _define_objects(self):
        # Define the unique object pieces for each Object
        pass

    def _append_object_to_spawn(self, image, shape):
        # made just so I don't have to type the stupid assoc key value everytime, maybe I'll change it some day
        self.pymunk_objects_to_spawn.append({"image": image, "shape": shape}) 

    @abstractmethod
    def collision_aftermath(self, space, contact_point):
        # Used to handle interactions specific to objects (wood is cut, rock is crushed, bomb explodes)
        pass