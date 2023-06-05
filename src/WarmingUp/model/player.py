class Player:
    score: int
    poses_hist: list
    keypoints: list
    pushup_seq = set([0, 1, 0])

    def __init__(self) -> None:
        self.score = 0
        self.poses_hist = []
        self.keypoints = []
    
    def does_exercise(self, ex_name: str, pred_class: int) -> bool:
        # Check if the chosen exercise is "PushUp"
        if (ex_name == "PushUp"):
            # Add the current predicted pose to the poses list
            self.poses_hist.append(pred_class)
            # If there are 3 poses saved & 
            # the poses list contains the predicted classes PushUp_Up, PushUp_Down and PushUp_Up 
            # (in that exact sequence), clear the list and return true
            if self.pushup_seq.issubset(self.poses_hist):
            # if len(self.poses_hist) > 3 and self.poses_hist == [0, 1, 0]:
                self.poses_hist.clear()
                return True
            # If the list has 3 items in the incorrect order, clear the list and return false
            # elif len(self.poses_hist) > 3 and self.poses_hist != [0, 1, 0]:
            #     self.poses_hist.clear()
            #     return False
        return False