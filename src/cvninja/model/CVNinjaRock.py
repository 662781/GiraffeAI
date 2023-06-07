from shared.utils import Generics, CVAssets
from shared.model import CVNinjaObject
from playsound import playsound

import numpy as np
import pymunk

class CVNinjaRock(CVNinjaObject):

    def __init__(self, image, size):
        super().__init__(image, size)
        self._get_images_vertices()
    
    def _get_images_vertices(self):
        super()._get_images_vertices()
        # Cut the image in half diagonally, these need to be saved in order to correctly handle the "breaking" of the object
        self.broken_images_horizontal = self._get_spliced_image_vertices_combo(2, True)

    def collision_requirements_are_met(self, player = None, collided_shape = None):
        if(collided_shape.player_limb == "left hand" or collided_shape.player_limb == "right hand"):
            # x of the latest coords should be relatively near each other, the better YOLO model, the more accurate this is. 
            return (abs(player.right_hand_track_points[0][0] - player.left_hand_track_points[0][0]) <= 60)
        else:
            # Else it is done with a foot, which is always allowed
            return True

    def spawn_object(self, space, collision_type, position=(0,700)):
        target = super().spawn_object(space, collision_type, position, play_sound = True)
        if(position[0] < 0):
            target.body.apply_impulse_at_local_point((250, -150))
        elif(position[0] > 640):
            target.body.apply_impulse_at_local_point((-250, -150))

        # calls super, but adds some force depending on the positions
    
    def collision_aftermath(self, space, shape, contact_point = (0,0)):
        # remove the collided "whole" object from draw list
        try:
            self.pymunk_objects_to_draw.remove(shape) 
        except:
            raise RuntimeError("Object was already removed, possibly due to double collision.")

        playsound(CVAssets.AUDIO_ROCK_SMASH, block=False)

        space.remove(shape, shape.body)
        broken_pymunk_objects = []
        for piece in self.broken_images_horizontal:
            body = pymunk.Body(1, 100)
            shape_piece = pymunk.Poly(body, piece[1])
            shape_piece.collision_type = 3
            shape_piece.image = piece[0]
            shape_piece.parent_object = self
            shape_piece.body.position = shape.body.position
            space.add(shape_piece, shape_piece.body)
            broken_pymunk_objects.append(shape_piece)
        self.pymunk_objects_to_draw.extend(broken_pymunk_objects)

        # This area requires a genius, the contact point is not trustworthy enough to determine the force to apply
        # Depending on the side the collision was detected, we apply an arbitrary amount of force to (some of) the objects  
        collision_side = Generics.determine_collision_side(shape.body.position, contact_point)
        if(collision_side == "top"):
            broken_pymunk_objects[0].body.apply_impulse_at_local_point((0,800))
            broken_pymunk_objects[1].body.apply_impulse_at_local_point((400,1000))
            broken_pymunk_objects[2].body.apply_impulse_at_local_point((-400,1000))
        elif(collision_side == "bottom"):
            broken_pymunk_objects[0].body.apply_impulse_at_local_point((0,-300))
            broken_pymunk_objects[1].body.apply_impulse_at_local_point((400,-600))
            broken_pymunk_objects[2].body.apply_impulse_at_local_point((-400,-600))
            broken_pymunk_objects[3].body.apply_impulse_at_local_point((-200,-600))
        elif(collision_side == "left"):
            broken_pymunk_objects[0].body.apply_impulse_at_local_point((800,200))
            broken_pymunk_objects[1].body.apply_impulse_at_local_point((500,200))
            broken_pymunk_objects[2].body.apply_impulse_at_local_point((400,200))
            broken_pymunk_objects[3].body.apply_impulse_at_local_point((600,200))
        elif(collision_side == "right"):
            broken_pymunk_objects[0].body.apply_impulse_at_local_point((-800,200))
            broken_pymunk_objects[1].body.apply_impulse_at_local_point((-500,200))
            broken_pymunk_objects[2].body.apply_impulse_at_local_point((-400,200))
            broken_pymunk_objects[3].body.apply_impulse_at_local_point((-600,200))
