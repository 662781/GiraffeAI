import cv2
import argparse
import torch
import numpy as np

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).autoshape()

# Set confidence threshold
confidence_threshold = 0.5

# Set non-maximum suppression threshold
nms_threshold = 0.5

# Load video file
cap = cv2.VideoCapture("pushups.mp4")

# Initialize counter and flag
count = 0
start_count = False

while cap.isOpened():
    # Read frame
    ret, frame = cap.read()

    # Break loop if video ends
    if not ret:
        break

    # Resize frame
    height, width, _ = frame.shape
    new_height, new_width = int(height / 2), int(width / 2)
    frame_resized = cv2.resize(frame, (new_width, new_height))

    # Convert frame to tensor
    frame_tensor = torch.from_numpy(frame_resized).permute(2, 0, 1).float().div(255.0).unsqueeze(0)

    # Run model on frame
    results = model(frame_tensor)

    # Extract boxes, scores, and classes
    boxes = results.xyxy[0]
    scores = results.xyxy[0][:, 4]
    classes = results.xyxy[0][:, 5]

    # Filter boxes by confidence threshold
    boxes_filtered = boxes[scores >= confidence_threshold]

    # Apply non-maximum suppression
    indices = cv2.dnn.NMSBoxes(boxes_filtered, scores[scores >= confidence_threshold], confidence_threshold, nms_threshold)

    # Check for push-up position
    for i in indices:
        if int(classes[i]) == 0: # person class
            x1, y1, x2, y2 = boxes_filtered[i].tolist()
            x1, y1, x2, y2 = int(x1 * width / new_width), int(y1 * height / new_height), int(x2 * width / new_width), int(y2 * height / new_height)
            if y1 < height // 2 and start_count == False:
                start_count = True
            elif y1 > height // 2 and start_count == True:
                start_count = False
                count += 1

    # Display frame
    cv2.imshow("Push-Ups", frame)

    # Exit loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Print number of push-ups
print("Number of push-ups:", count)

# Release video capture and close windows
cap.release()
cv2.destroyAllWindows()
