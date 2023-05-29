from collections import deque
import cv2 as cv


class CvFpsCalc(object):
    """Helper class to calculate FPS with OpenCV

        CvFpsCalc is a class that calculates frames per second (FPS) for video processing using the OpenCV library.

        Attributes:
            _start_tick (int): The start tick value in the OpenCV timer.
            _freq (float): The frequency of the OpenCV timer in milliseconds.
            _difftimes (deque): A deque object that stores the time differences between consecutive frames.

        Methods:
            __init__(self, buffer_len=1):
                Initializes a new instance of the CvFpsCalc class.
                
                Args:
                    buffer_len (int): The maximum number of time differences to keep in the deque. Defaults to 1.

            get(self):
                Calculates and returns the rounded frames per second (FPS) value.
                
                Returns:
                    float: The rounded FPS value based on the time differences stored in the deque.
    """

    def __init__(self, buffer_len=1):
        self._start_tick = cv.getTickCount()
        self._freq = 1000.0 / cv.getTickFrequency()
        self._difftimes = deque(maxlen=buffer_len)

    def get(self):
        current_tick = cv.getTickCount()
        different_time = (current_tick - self._start_tick) * self._freq
        self._start_tick = current_tick

        self._difftimes.append(different_time)

        fps = 1000.0 / (sum(self._difftimes) / len(self._difftimes))
        fps_rounded = round(fps, 2)

        return fps_rounded
