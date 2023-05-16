class Generics():

    @staticmethod
    def _create_line_function(point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        if(x2 - x1) == 0: # Slope would be infinte, let the other method handle it
            def line_function(x):
                return None
        else:
            m = (y2 - y1) / (x2 - x1)
            b = y1 - m * x1
            def line_function(x):
                y = m * x + b
                return y
        return line_function

    @staticmethod
    def create_additional_keypoint(wrist, elbow):
        keypoint1 = wrist
        keypoint2 = elbow
        
        keypoint_x = keypoint1[0] - ((keypoint2[0] - keypoint1[0]) / 2) # divide by two to avoid overreach
        line_func = Generics._create_line_function(keypoint2, keypoint1)
        keypoint_y = line_func(keypoint_x)
        if(keypoint_y is None): # on infinite slope, take an y relative to the other y coords 
            keypoint_y = keypoint1[1] - ((keypoint2[1] - keypoint1[1]) / 2)

        new_keypoint = (int(keypoint_x), int(keypoint_y)) # coordinates are only useful as rounded integers
        return new_keypoint

