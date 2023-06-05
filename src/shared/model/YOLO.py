from ultralytics import YOLO as actual_yolo
import torch
from shared.utils import CVAssets


class YOLO:
    """ YOCO (You Only Create Once)
    
        A small singleton class to ensure the YOLO model is only created once.
        At the time of writing, 2 games use the YOLO enabled models.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = actual_yolo(CVAssets.YOLO_MODEL_L)
            # print("TORCH AVAILABLE", torch.cuda.is_available())
            # actual_yolo.to('cuda')
            
        return cls._instance


