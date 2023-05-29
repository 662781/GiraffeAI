import cv2
class FPSCounterService:
    # used to record the time when we processed last frame
    prev_frame_time = 0
    # used to record the time at which we processed current frame
    new_frame_time = 0
    def show_fps(frame, time, self):
        # font which we will be using to display FPS
        font = cv2.FONT_HERSHEY_SIMPLEX
        # time when we finish processing for this frame
        self.new_frame_time = time
    
        # Calculating the fps
    
        # fps will be number of frame processed in given time frame
        # since their will be most of time error of 0.001 second
        # we will be subtracting it to get more accurate result
        fps = 1/(self.new_frame_time-self.prev_frame_time)
        self.prev_frame_time = self.new_frame_time
    
        # converting the fps into integer
        fps = int(fps)
    
        # converting the fps to string so that we can display it on frame
        # by using putText function
        fps = str(fps)
    
        # putting the FPS count on the frame
        cv2.putText(frame, fps, (7, 70), font, 3, (100, 255, 0), 3, cv2.LINE_AA)