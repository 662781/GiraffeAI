import cv2
import numpy as np
from shared.utils import Generics

# Load the original image
image = cv2.imread('cvninja/assets/rock.png', cv2.IMREAD_UNCHANGED)
size = 70
image = cv2.resize(image, (size, size), interpolation=cv2.INTER_LINEAR)

original_coordinate = (100, 100)
diagonal_splice_left = np.zeros_like(image, dtype=np.uint8)
diagonal_splice_right = np.zeros_like(image, dtype=np.uint8)
for i in range(size):
    diagonal_splice_left[i, :size-i] = image[i, :size-i]
    diagonal_splice_right[i, size-i:] = image[i, size-i:]

# 2 halves of the diagonal right splice
horizontal_splice_1_left =  diagonal_splice_left[:,:size//2]
horizontal_splice_1_right = diagonal_splice_left[:,size//2:]

new_position_1_right = (int(original_coordinate[0] + diagonal_splice_left.shape[1]//2), original_coordinate[1])

new_position_2_right = (int(original_coordinate[0] + diagonal_splice_right.shape[1]//2), original_coordinate[1])


# 2 halves of the diagonal left splice
horizontal_splice_2_left =  diagonal_splice_right[:,:size//2]
horizontal_splice_2_right = diagonal_splice_right[:,size//2:]



# Specify the basis coordinate for all parts

# Define the number of divisions horizontally and diagonally

cap = cv2.VideoCapture(0)
camera_width = 640
camera_height = 480
cap.set(3, camera_width)
cap.set(4, camera_height)
doit = False
count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame not captured, exiting...")
        break

    if(doit):
        for i in range(count+1):
            frame = Generics.overlayPNG(frame, part_coordinates[i][0], [ part_coordinates[i][1][0],part_coordinates[i][1][1]] )
    else:
        frame = Generics.overlayPNG(frame,horizontal_splice_1_left, [original_coordinate[0], original_coordinate[1]])
        frame = Generics.overlayPNG(frame,horizontal_splice_1_right, [new_position_1_right[0], new_position_1_right[1]])


        frame = Generics.overlayPNG(frame,horizontal_splice_2_left, [original_coordinate[0], original_coordinate[1]])
        frame = Generics.overlayPNG(frame,horizontal_splice_2_right, [new_position_2_right[0], new_position_2_right[1]])
       

    cv2.putText(frame, "Hello", (0,30), cv2.FONT_HERSHEY_SIMPLEX, 1.2,  (255, 255, 255) , 2)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        if(doit):
            count +=1 
            if count == 6:
                count = 0
            print("New Count: ", count)
    # if cv2.waitKey(1) & 0xFF == ord('c'):
    #     doit = not doit
    
    cv2.imshow("Image", frame)
cap.release()
cv2.destroyAllWindows()