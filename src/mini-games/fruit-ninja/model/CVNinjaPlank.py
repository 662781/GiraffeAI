from utils import Generics

class CVNinjaPlank(CVNinjaObject):

    def __init__(self, image_path, size)
        super.__init__(image_path, size)
        self._insert_vertices()
    
    def _insert_vertices(self):
        # Cut image diagonally 
        diagonal_splice_left = np.zeros_like(self.image, dtype=np.uint8)
        diagonal_splice_right = np.zeros_like(self.image, dtype=np.uint8)
        for i in range(self.size):
            diagonal_splice_right[i, :self.size-i] = self.image[i, :self.size-i]
            diagonal_splice_left[i, self.size-i:] = self.image[i, self.size-i:]
        # Vertices for diagonal image split
        self.vertices["DIAGONAL_SPLICE_LEFT"] = Generics.get_vertices_by_image(diagonal_splice_left)
        self.vertices["DIAGONAL_SPLICE_RIGHT"] = Generics.get_vertices_by_image(diagonal_splice_right)
        
        # Vertices for vertical image split
        horizontal_splice_left =  wood[:,:size//2]
        horizontal_splice_right = wood[:,size//2:]

        self.vertices["HORIZONTAL_SPLICE_LEFT"] = Generics.get_vertices_by_image(horizontal_splice_left)
        self.vertices["HORIZONTAL_SPLICE_LEFT"] = Generics.get_vertices_by_image(horizontal_splice_right)

    def collision_aftermath(self, contact_point):
        # Depending on the contact point, 
        pass