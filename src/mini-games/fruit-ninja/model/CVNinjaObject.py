import cv2
from abc import ABC
import CVNinjaObjectState
from utils import Generics


class CVNinjaObject(ABC):

    pymunk_objects =  []  # Denoted as tuple: (image, body_object)
    vertices = {}
    def __init__(self, image_path: str, size: int, object_state: CVNinjaObjectState )
        self._setup(image_path, size)
        self.object_state = object_state

    def _setup(self, image_path, size):
        self.image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        self.image = cv2.resize(self.image, (size, size), interpolation=cv2.INTER_LINEAR)
        self.size = size # for now width and height will be the same
        self._insert_vertices()
        body = pymunk.Body(1, 100)
        shape = pymunk.Poly(body, self.vertices["whole"])
        pymunk_objects.append((self.image, shape))

    def _insert_vertices(self):
        self.vertices.append("whole": Generics.get_vertices_by_image(self.image))

    @abstractmethod
    def collision_aftermath(self, contact_point):
        # Used to handle interactions specific to objects (wood is cut, rock is crushed, bomb explodes)
        pass