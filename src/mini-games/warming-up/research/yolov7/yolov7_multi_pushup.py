import cv2
import numpy as np

# Define class for player
class Player:
    def __init__(self, name, color, x, y):
        self.name = name
        self.color = color
        self.score = 0
        self.x = x
        self.y = y

# Load YOLOv7 model and configuration file
net = cv2.dnn.readNet("yolov7-tiny.weights", "yolov7.cfg")

# # Load classes for YOLOv7
# classes = []
# with open("coco.names", "r") as f:
#     classes = [line.strip() for line in f.readlines()]

# Set minimum confidence threshold for detections
conf_threshold = 0.5

# Set non-maximum suppression threshold for detections
nms_threshold = 0.4

# Set up players
players = [
    Player("Player 1", (0, 255, 0), 0, 0),
    Player("Player 2", (0, 0, 255), 0, 0),
    Player("Player 3", (255, 0, 0), 0, 0),
    Player("Player 4", (255, 255, 0), 0, 0)
]

# Capture video from default webcam
cap = cv2.VideoCapture(0)

while True:
    # Read frame from video
    ret, frame = cap.read()

    # Create blob from frame
    blob = cv2.dnn.blobFromImage(frame, 1/255, (416, 416), swapRB=True, crop=False)

    # Set input for YOLOv7 network
    net.setInput(blob)

    # Get output from YOLOv7 network
    output_layers = net.getUnconnectedOutLayersNames()
    layer_outputs = net.forward(output_layers)

    # Process detections
    boxes = []
    confidences = []
    class_ids = []
    for output in layer_outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > conf_threshold and class_id == 0:
                center_x = int(detection[0] * frame.shape[1])
                center_y = int(detection[1] * frame.shape[0])
                w = int(detection[2] * frame.shape[1])
                h = int(detection[3] * frame.shape[0])
                x = center_x - w // 2
                y = center_y - h // 2
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Assign each detected push up to the closest player
    for box in boxes:
        min_distance = float('inf')
        closest_player = None
        for player in players:
            distance = np.sqrt((box[0] - player.x)**2 + (box[1] - player.y)**2)
            if distance < min_distance:
                min_distance = distance
                closest_player = player
        if min_distance < 100:
            closest_player.score += 1
            cv2.rectangle(frame, (box[0], box[1]), (box[0] + box[2], box[1] + box[3]), closest_player.color, 2)
            cv2.putText(frame, closest_player.name + ": " + str(closest_player.score),
            (closest_player.x, closest_player.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            closest_player.color, 2)
    # Display frame
    cv2.imshow("Push Up Counter", frame)

    # Wait for key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
