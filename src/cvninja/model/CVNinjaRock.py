from shared.utils import Generics
from shared.model import CVNinjaObject

import numpy as np
import pymunk

class CVNinjaRock(CVNinjaObject):

    def __init__(self, image, size):
        super().__init__(image, size)
        self._get_images_vertices()
    
    def _get_images_vertices(self):
        super()._get_images_vertices()
        # Cut the image in half diagonally, these need to be saved in order to correctly handle the "breaking" of the object
        self.diagonal_splice_left = np.zeros_like(self.image, dtype=np.uint8)
        self.diagonal_splice_right = np.zeros_like(self.image, dtype=np.uint8)
        for i in range(self.size):
            self.diagonal_splice_left[i, :self.size-i] = self.image[i, :self.size-i]
            self.diagonal_splice_right[i, self.size-i:] = self.image[i, self.size-i:]
        
        # Cut left diagonal half in two
        horizontal_splice_left_part1 = self.diagonal_splice_left[:,:self.size//2]
        horizontal_splice_left_part2 = self.diagonal_splice_left[:,self.size//2:]

        # Cut right diagonal half in two  
        horizontal_splice_right_part1 =  self.diagonal_splice_right[:,:self.size//2]
        horizontal_splice_right_part2 = self.diagonal_splice_right[:,self.size//2:]

        self.images_vertices["DIAGONAL_SPLICE_LEFT_1"]  = (horizontal_splice_left_part1,Generics.get_vertices_by_image(horizontal_splice_left_part1))
        self.images_vertices["DIAGONAL_SPLICE_LEFT_2"]  = (horizontal_splice_left_part2,Generics.get_vertices_by_image(horizontal_splice_left_part2))
        
        self.images_vertices["DIAGONAL_SPLICE_RIGHT_1"] = (horizontal_splice_right_part1,Generics.get_vertices_by_image(horizontal_splice_right_part1))
        self.images_vertices["DIAGONAL_SPLICE_RIGHT_2"] = (horizontal_splice_right_part2,Generics.get_vertices_by_image(horizontal_splice_right_part2))
        
        self.pieces = [
            self.images_vertices["DIAGONAL_SPLICE_LEFT_1"], 
            self.images_vertices["DIAGONAL_SPLICE_LEFT_2"], 
            self.images_vertices["DIAGONAL_SPLICE_RIGHT_1"], 
            self.images_vertices["DIAGONAL_SPLICE_RIGHT_2"], 
            ]
    
    def collision_aftermath(self, space, shape, contact_point = (0,0)):
        # todo: handle contact point for now

        # remove the collided "whole" object from draw list

        self.pymunk_objects_to_draw.remove(shape) 
        shapes = []
        for piece in self.pieces:
            body = pymunk.Body(1, 100)
            body.position = shape.body.position
            shape_piece = pymunk.Poly(body, piece[1])
            shape_piece.image = piece[0]
            shape_piece.parent_object = self
            shape_piece.collision_type = 3
            space.add(shape_piece, shape_piece.body)
            shapes.append(shape_piece)
        
        new_position = (int(shapes[1].body.position.x + self.diagonal_splice_left.shape[1]//2), shapes[1].body.position.y)
        shapes[1].body.position = new_position
        new_position = (int(shapes[3].body.position.x + self.diagonal_splice_right.shape[1]//2), shapes[3].body.position.y)
        shapes[3].body.position = new_position
        for shape in shapes:
            shape.body.apply_impulse_at_local_point((-500, 0))

        self.pymunk_objects_to_draw.extend(shapes)

        
