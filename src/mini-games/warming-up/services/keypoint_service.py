from ultralytics.yolo.utils.plotting import Annotator
class KeypointService:
    def showKeypointNrs(ann: Annotator, keypoints: list):
        for i, kp in enumerate(keypoints):
            # print("x=" + str(kp[0]) + " y=" + str(kp[1]))
            if (type(kp[0]) == list or type(kp[1]) == list):
                continue
            x = int(kp[0])
            y = int(kp[1])
            ann.text((x, y), str(i))