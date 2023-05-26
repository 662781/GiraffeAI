from shared.utils import Generics
import pymunk
from shared.model import CVNinjaObject
import numpy as np

class MainMenuObject(CVNinjaObject):

    def __init__(self, image, size):
        super().__init__(image, size)
        self._get_images_vertices()
    
    def _get_images_vertices(self):
        super()._get_images_vertices()
        # images_vertices for vertical image split
        horizontal_splice_left =  self.image[:,:self.size//2]
        horizontal_splice_right = self.image[:,self.size//2:]

        self.images_vertices["HORIZONTAL_SPLICE_LEFT"]  = (horizontal_splice_left,Generics.get_vertices_by_image(horizontal_splice_left))
        self.images_vertices["HORIZONTAL_SPLICE_RIGHT"] = (horizontal_splice_right,Generics.get_vertices_by_image(horizontal_splice_right))
    
    def spawn_object(self, space, collision_type, position=(50,50)):
        body = pymunk.Body(1, float('inf'))
        body.position = position
        shape = pymunk.Poly(body, self.images_vertices["WHOLE"][1])
        shape.parent_object = self # For retrieval during collision
        shape.collision_type = collision_type
        space.add(shape, body)
        shape.image = self.image
        self.pymunk_objects_to_draw.append(shape)

    def collision_aftermath(self, space, shape, contact_point = (0,0)):
        # ignore contact point for now

        # remove the collided "whole" object from draw list
        self.pymunk_objects_to_draw.remove(shape) 
        # take the cut object and set it to spawn 
        body = pymunk.Body(1, 100)
        shape_piece1 = pymunk.Poly(body, self.images_vertices["HORIZONTAL_SPLICE_LEFT"][1])
        shape_piece1.image = self.images_vertices["HORIZONTAL_SPLICE_LEFT"][0]
        shape_piece1.parent_object = self
        
        body = pymunk.Body(1, 100)
        shape_piece2 = pymunk.Poly(body, self.images_vertices["HORIZONTAL_SPLICE_RIGHT"][1])
        shape_piece2.image = self.images_vertices["HORIZONTAL_SPLICE_RIGHT"][0]
        shape_piece2.parent_object = self

        shape_piece1.collision_type = 3 #collision_types["broken_objects"]
        shape_piece2.collision_type = 3 #collision_types["broken_objects"]

        space.add(shape_piece1, shape_piece1.body)
        space.add(shape_piece2, shape_piece2.body)

        shape_piece1.body.position = shape.body.position
        shape_piece2.body.position = shape.body.position

        # set cut wood part in correct place 
        new_position = (int(shape_piece2.body.position.x + self.image.shape[1]//2), shape_piece2.body.position.y)
        shape_piece2.body.position = new_position

        shape_piece1.body.apply_impulse_at_local_point((-500, 0))
        shape_piece2.body.apply_impulse_at_local_point((500, 0))

        self.pymunk_objects_to_draw.extend([shape_piece1, shape_piece2])
