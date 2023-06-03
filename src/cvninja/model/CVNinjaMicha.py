from shared.utils import Generics, CVAssets
from shared.model import CVNinjaObject
from playsound import playsound
import numpy as np
import pymunk
import random

class CVNinjaMicha(CVNinjaObject):

    def __init__(self, image, size):
        super().__init__(image, size)
        self._get_images_vertices()
    
    def _get_images_vertices(self):
        super()._get_images_vertices()
        # Custom variables for particular cuts of the wooden plank
        self.broken_images_shrapnel = self._get_spliced_image_vertices_combo(4, True)
        
    def spawn_object(self, space, collision_type, position=(0,700), play_sound = True):
        target = super().spawn_object(space, collision_type, position, play_sound = False)
        playsound(CVAssets.AUDIO_MICHA_INTRO, block = False)

        if(position[0] < 0):
            target.body.apply_impulse_at_local_point((250, -150))
        elif(position[0] > 640):
            target.body.apply_impulse_at_local_point((-250, -150))

    def collision_requirements_are_met(self, player = None, collided_shape = None):
        if(collided_shape.player_limb == "left hand" or collided_shape.player_limb == "right hand"):
            # x of the latest coords should be relatively near each other, the better YOLO model, the more accurate this is. 
            return abs(player.right_hand_track_points[0][0] - player.left_hand_track_points[0][0]) <= 60

        return True # Else it is done with a foot, which is always allowed

    def collision_aftermath(self, space, shape, contact_point = (0,0)):
        # ignore contact point for now
        try:
            self.pymunk_objects_to_draw.remove(shape) 
        except:
            raise RuntimeError("Object was already removed, possibly due to double collision.")
        playsound(CVAssets.AUDIO_EXPLOSION,block = False)
        broken_pymunk_objects = []
        for piece in self.broken_images_shrapnel:
            body = pymunk.Body(1, 100)
            shape_piece = pymunk.Poly(body, piece[1])
            shape_piece.collision_type = 3
            shape_piece.image = piece[0]
            shape_piece.parent_object = self
            shape_piece.body.position = shape.body.position
            space.add(shape_piece, shape_piece.body)
            broken_pymunk_objects.append(shape_piece)
        # Apply some chaos for the tsar bomba
        for broken_object in broken_pymunk_objects:
            impulse = (random.randint(-1000, 1000),random.randint(-1000, 1000))
            broken_object.body.apply_impulse_at_local_point(impulse)
        self.pymunk_objects_to_draw.extend(broken_pymunk_objects)
