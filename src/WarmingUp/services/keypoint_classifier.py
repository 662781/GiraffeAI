import numpy as np
import tensorflow as tf
import csv
import os
from ultralytics.yolo.utils.plotting import Annotator


class KeyPointClassifier(object):
    def __init__(self, model_path = 'WarmingUp/assets/tflite/keypoint_classifier.tflite', num_threads=1):
        self.interpreter = tf.lite.Interpreter(model_path=model_path,num_threads=num_threads)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def __call__(self,keypoint_list):
        """Use the TensorFlow model to get the predicted class index (based on a given pre-processed keypointlist)"""
        input_details_tensor_index = self.input_details[0]['index']
        keypoint_array = np.array([[keypoint_list]], dtype=np.float32)
        self.interpreter.set_tensor(input_details_tensor_index, keypoint_array)
        self.interpreter.invoke()

        output_details_tensor_index = self.output_details[0]['index']

        result = self.interpreter.get_tensor(output_details_tensor_index)

        result_index = np.argmax(np.squeeze(result))

        return result_index

    def show_prediction(self, ann: Annotator, index: int, xy: tuple):
        """Show the prediction of the keypoint classifier in the CV window using an Annotator object from the Ultralytics library"""
        # Read classes in CSV file
        path = 'WarmingUp/assets/classifier_classes.csv'

        # Only continue if the path exists
        if (os.path.exists(path)):
            classes = []
            with open(path) as file:
                reader = csv.reader(file, delimiter=',')
                for row in reader:
                    classes.append(row[0])
            classes = [c.strip('ï»¿') for c in classes]
            # Select index of predicted class
            pred_class = ""
            for i, c in enumerate(classes):
                if i == index:
                    pred_class = c
            # Draw the predicted class on the CV window
            ann.text(xy, pred_class, txt_color=(0, 0, 0))

    def is_model_available(model_path: str):
        """Returns a boolean; checks if the model path exists"""
        return os.path.exists(model_path)
