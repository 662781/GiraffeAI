from utils import Generics
import pymunk

class CVNinjaPlank(CVNinjaObject):

    def __init__(self, image, size)
        super().__init__(image, size)
        self._define_objects()
    
    def _define_objects(self):
        # Cut image diagonally 
        diagonal_splice_left = np.zeros_like(self.image, dtype=np.uint8)
        diagonal_splice_right = np.zeros_like(self.image, dtype=np.uint8)
        for i in range(self.size):
            diagonal_splice_right[i, :self.size-i] = self.image[i, :self.size-i]
            diagonal_splice_left[i, self.size-i:] = self.image[i, self.size-i:]
        # Vertices for diagonal image split
        body = pymunk.Body(1, 100)
        shape = pymunk.Poly(body, Generics.get_vertices_by_image(diagonal_splice_left))
        self.pymunk_objects_broken.append("DIAGONAL_SPLICE_LEFT":(diagonal_splice_left,shape))

        body = pymunk.Body(1, 100)
        shape = pymunk.Poly(body, Generics.get_vertices_by_image(diagonal_splice_right))
        self.pymunk_objects_broken.append("DIAGONAL_SPLICE_RIGHT":(diagonal_splice_right,shape))
        
        # Vertices for vertical image split
        horizontal_splice_left =  wood[:,:size//2]
        horizontal_splice_right = wood[:,size//2:]

        body = pymunk.Body(1, 100)
        shape = pymunk.Poly(body, Generics.get_vertices_by_image(horizontal_splice_left))
        self.pymunk_objects_broken.append("HORIZONTAL_SPLICE_LEFT":(horizontal_splice_left,shape))

        body = pymunk.Body(1, 100)
        shape = pymunk.Poly(body, Generics.get_vertices_by_image(horizontal_splice_right))
        self.pymunk_objects_broken.append("HORIZONTAL_SPLICE_RIGHT":(horizontal_splice_right,shape))

    def collision_aftermath(self, space, shape, contact_point):
        # ignore contact point for now

        # remove the main object from spawn list
        self.pymunk_objects_to_spawn = []
        # take the cut object and set it to spawn 
        piece1 =  self.pymunk_objects_broken["HORIZONTAL_SPLICE_LEFT"]
        piece1_body = piece1[1].body

        piece2 = self.pymunk_objects_broken["HORIZONTAL_SPLICE_RIGHT"]
        piece2_body = piece2[1].body

        piece1_body.collision_type = 3 #collision_types["broken_objects"]
        piece2_body.collision_type = 3 #collision_types["broken_objects"]

        space.add(piece1[1], piece1_body)
        space.add(piece2[1], piece2_body)

        piece1_body.position = shape.body.position
        piece2_body.position = shape.body.position

        # set cut wood part in correct place 
        piece2_body.position.x = int(piece2_body.position.x + self.image.shape[1]//2)

        piece1_body.apply_impulse_at_local_point((-100, 0))

        self._append_object_to_spawn(piece1[0], piece1[1] )
        self._append_object_to_spawn(piece2[0], piece2[1] )
