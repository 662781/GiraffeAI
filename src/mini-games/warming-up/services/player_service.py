class PlayerService:
    def does_pushup(keypoints):
        check = [7, 8, 9, 10]
        try:
            for i, kp in enumerate(keypoints):
                # Check if the keypoint exists
                if i in check and kp is None:
                    return False
                # Check if there's a second list in the keypoint (somehow)
                if type(kp[0]) is list:
                    return False
        except:
            return False
        left_wrist = keypoints[9] # [x (float), y (float), conf (float)]
        left_elbow = keypoints[7]
        right_wrist = keypoints[10]
        right_elbow = keypoints[8]
        right_shoulder = keypoints[5]
        left_shoulder = keypoints[6]

        # Check if wrists are below elbows and close to the body
        if left_wrist[1] > left_elbow[1] and left_wrist[0] < left_elbow[0] and \
        right_wrist[1] > right_elbow[1] and right_wrist[0] > right_elbow[0]:
            # Check if elbows are extended and aligned with shoulders
            if left_elbow[1] < right_shoulder[1] and left_elbow[0] < left_shoulder[0] and \
            right_elbow[1] < right_shoulder[1] and right_elbow[0] > left_shoulder[0]:
                return True
        return False