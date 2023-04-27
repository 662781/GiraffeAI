from ultralytics.yolo.utils.plotting import Annotator
import itertools
import copy
class KeypointService:
    def show_keypoint_nrs(ann: Annotator, keypoints: list):
        for i, kp in enumerate(keypoints):
            # print("x=" + str(kp[0]) + " y=" + str(kp[1]))
            if (type(kp[0]) == list or type(kp[1]) == list):
                continue
            x = int(kp[0])
            y = int(kp[1])
            ann.text((x, y), str(i))

    def pre_process_keypoints(self, keypoints):
        temp_keypoint_list = copy.deepcopy(keypoints)

        # Remove confidence rate from individual keypoints (index 2)
        KeypointService.__remove_conf_rate(temp_keypoint_list)

        # Convert to relative coordinates (based on the first keypoint --> in this case the NOSE)
        base_x, base_y = 0, 0
        for index, keypoint in enumerate(temp_keypoint_list):
            if index == 0:
                base_x, base_y = keypoint[0], keypoint[1]

            temp_keypoint_list[index][0] = temp_keypoint_list[index][0] - base_x
            temp_keypoint_list[index][1] = temp_keypoint_list[index][1] - base_y

        # Convert to a one-dimensional list
        temp_keypoint_list = list(
            itertools.chain.from_iterable(temp_keypoint_list))

        # Normalization
        max_value = max(list(map(abs, temp_keypoint_list)))

        def normalize_(n):
            return n / max_value

        temp_keypoint_list = list(map(normalize_, temp_keypoint_list))

        return temp_keypoint_list
    
    def __remove_conf_rate(keypoints):
        for kp in keypoints:
            del kp[2]