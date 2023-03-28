class PoseDetector:
    def does_push_up(results, mp):
        if results.pose_landmarks is not None:
            # Get the landmarks for the hips, shoulders and elbows
            left_hip = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP]
            right_hip = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_HIP]
            left_shoulder = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
            left_elbow = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_ELBOW]
            right_elbow = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW]

            # Check if the hips are above the shoulders
            if left_hip.y < left_shoulder.y and right_hip.y < right_shoulder.y:
                # Check if the elbows are below the shoulders
                if left_elbow.y > left_shoulder.y and right_elbow.y > right_shoulder.y:
                    return True
        return False
