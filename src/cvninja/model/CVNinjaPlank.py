from shared.utils import Generics
from shared.model import CVNinjaObject

import numpy as np
import pymunk

class CVNinjaPlank(CVNinjaObject):

    def __init__(self, image, size):
        super().__init__(image, size)
        self._get_images_vertices()
    
    def _get_images_vertices(self):
        super()._get_images_vertices()
        # Custom variables for particular cuts of the wooden plank
        self.broken_images_horizontal = self._get_spliced_image_vertices_combo(2)
        self.broken_images_diagonal = self._get_spliced_image_vertices_combo(1, True)
    
    def collision_aftermath(self, space, shape, contact_point = (0,0)):
        # ignore contact point for now
        try:
            self.pymunk_objects_to_draw.remove(shape) 
        except:
            raise RuntimeError("Object was already removed, possibly due to double collision.")
        
        
        collision_side = Generics.determine_collision_side(shape.body.position, contact_point)
        if(collision_side == "bottom"):
            chosen_splice = self.broken_images_diagonal
        else:
            chosen_splice = self.broken_images_horizontal
        broken_pymunk_objects = []
        for piece in chosen_splice:
            body = pymunk.Body(1, 100)
            shape_piece = pymunk.Poly(body, piece[1])
            shape_piece.collision_type = 3
            shape_piece.image = piece[0]
            shape_piece.parent_object = self
            shape_piece.body.position = shape.body.position
            space.add(shape_piece, shape_piece.body)
            broken_pymunk_objects.append(shape_piece)
        # Apply some force to make it seam like the cut did something
        broken_pymunk_objects[0].body.apply_impulse_at_local_point((-250, 0))
        broken_pymunk_objects[1].body.apply_impulse_at_local_point((250, 0))
        self.pymunk_objects_to_draw.extend(broken_pymunk_objects)
