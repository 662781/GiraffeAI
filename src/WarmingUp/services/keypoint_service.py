from ultralytics.yolo.utils.plotting import Annotator
import itertools
import copy
import csv
class KeypointService:
    detected_players: int = 0
    
    def __init__(self, detected_players: int) -> None:
        self.detected_players = detected_players

    def show_keypoint_nrs(self, ann: Annotator, keypoints: list):
        """Draw the keypoint numbers (indexes) on the detected people. Only for testing purposes"""
        if (self.detected_players == 1):
            for i, kp in enumerate(keypoints):
                x = int(kp[0])
                y = int(kp[1])
                ann.text((x, y), str(i))
        if (self.detected_players > 1):
            for player in keypoints:
                for i, kp in enumerate(player):
                    x = int(kp[0])
                    y = int(kp[1])
                    ann.text((x, y), str(i))
    
    def pre_process_keypoints(keypoints):
        """Pre-process the keypoints list by first removing the confidence rate (which is not necessary) and then converting them to relative coordinates"""
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
        temp_keypoint_list = list(itertools.chain.from_iterable(temp_keypoint_list))

        # Normalization
        max_value = max(list(map(abs, temp_keypoint_list)))

        def normalize_(n):
            return n / max_value

        return list(map(normalize_, temp_keypoint_list))
        
    def __remove_conf_rate(keypoints):
        for kp in keypoints:
            del kp[2]

    def write_kp_data_to_csv(self, number, mode, keypoints):
        """Write the keypoints of 1 detected person to a csv file """
        if mode == 0:
            pass
        if mode == 1 and (0 <= number <= 9):
            # Pre-process keypoints for keypoint / pose prediction input (dataset)
            csv_path = 'WarmingUp/assets/keypoint-dataset.csv'
            with open(csv_path, 'a', newline="") as f:
                writer = csv.writer(f)
                writer.writerow([number, *keypoints])
        return
    
    def select_mode(key, mode):
        """Select Application Mode. Mode 0 = default, Mode 1 = Snapshot Mode.\n
        Press 's' to enter snapshot mode.\n
        Press 'd' to enter default mode"""
        number = -1
        if key >= ord('0') and key <= ord('9'):
            number = key - ord('0')
        if key == ord('d'):
            mode = 0
        if key == ord('s'):
            mode = 1
        return number, mode
    
    def keypoints_detected(keypoints):
        """Returns a boolean; checks if there are keypoints detected"""
        if len(keypoints) == 0 or keypoints is None:
            return False
        return True
