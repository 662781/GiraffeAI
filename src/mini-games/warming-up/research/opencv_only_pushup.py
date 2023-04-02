import cv2

# Load the trained XML classifiers
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
body_cascade = cv2.CascadeClassifier('haarcascade_fullbody.xml')

# Load the video capture device
cap = cv2.VideoCapture(0)

while True:
    # Read the frames from the camera
    ret, frame = cap.read()

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces and bodies in the frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    bodies = body_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    # Draw rectangles around the detected faces and bodies
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    for (x, y, w, h) in bodies:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

    # Check if someone is doing a push up
    for body in bodies:
        # Check if the person's head is close to the body
        for (x, y, w, h) in faces:
            if x > body[0] and y > body[1] and x+w < body[0]+body[2] and y+h < body[1]+body[3]:
                print('Push up detected!')
                break

    # Display the resulting frame
    cv2.imshow('frame', frame)

    # Exit the program when the 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture device and close all windows
cap.release()
cv2.destroyAllWindows()
