class PlayerService:
    def does_pushup(keypoints):
        check = [0, 1, 2, 3]
        for index, item in enumerate(keypoints):
            if index in check and item is None:
                return False
        left_wrist = keypoints[0]
        left_elbow = keypoints[1]
        right_wrist = keypoints[2]
        right_elbow = keypoints[3]

        # Check if wrists are below elbows and close to the body
        if left_wrist[1] > left_elbow[1] and left_wrist[0] < left_elbow[0] and \
        right_wrist[1] > right_elbow[1] and right_wrist[0] > right_elbow[0]:
            # Check if elbows are extended and aligned with shoulders
            if left_elbow[1] < keypoints[5][1] and left_elbow[0] < keypoints[6][0] and \
            right_elbow[1] < keypoints[5][1] and right_elbow[0] > keypoints[6][0]:
                return True
        return False