import random
import traceback
import numpy as np
import cv2
import time
from ultralytics import YOLO
from utils import CvFpsCalc
from utils import Generics
from CVNinjaPlayer import CVNinjaPlayer
from shapely.geometry import LineString, Polygon
import pymunk


collision_types = {
    "limbs_player_1": 1,
    "objects_player_1" : 2,
    "broken_objects" : 3,
    "void": 99, 
}
yolo_model = YOLO('yolov8m-pose.pt')  # load an official model
number_of_players = 1 # todo: argument

players = []
for i in range(number_of_players):
    players.append(CVNinjaPlayer())


camera_width = 640
camera_height = 480

def get_trailing(player, image):
    line_left_hand_shape.unsafe_set_vertices([(player.left_hand_track_points[-1]),(player.left_hand_track_points[0])])
    line_right_hand_shape.unsafe_set_vertices([(player.right_hand_track_points[-1]),(player.right_hand_track_points[0])])
    #hand_circle_body.velocity = (1000, 0)
    cv2.line(image, player.left_hand_track_points[-1], player.left_hand_track_points[0], (0,0,255),5)
    cv2.line(image, player.right_hand_track_points[-1], player.right_hand_track_points[0], (0,0,255),5)
    cv2.line(image, player.right_foot_track_points[-1], player.right_foot_track_points[0], (0,0,255),5)
    cv2.line(image, player.left_foot_track_points[-1], player.left_foot_track_points[0], (0,0,255),5)

cap = cv2.VideoCapture(0)
cap.set(3, camera_width)
cap.set(4, camera_height)

cv2.namedWindow("webcam", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("webcam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cvFpsCalc = CvFpsCalc(buffer_len=10)
current_player = "none"

wood = cv2.imread('resources/wood.png', cv2.IMREAD_UNCHANGED)
size = 80
wood = cv2.resize(wood, (size, size), interpolation=cv2.INTER_LINEAR)
img2gray = cv2.cvtColor(wood, cv2.COLOR_BGR2GRAY)
ret, mask = cv2.threshold(img2gray, 1, 255, cv2.THRESH_BINARY)
woodX=random.randint(100, camera_width-110)
woodY=random.randint(100, 300)
woodLine = Polygon([(woodX, woodY), (woodX, woodY+size),(woodX +size, woodY), (woodX +size, woodY +size)  ])

plankie = cv2.imread("resources/wood.png")

print("Plankie shape: ", plankie.shape)
#plankie = cv2.bitwise_not(plankie)
#contours, hierarchy = cv2.findContours(plankie, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# shapes, really
pymunk_objects = []
def spawn_object(space1):
    print("Spawning object")
    circle_body = pymunk.Body(1, 100)
    circle_shape = pymunk.Circle(circle_body, 20)
    circle_shape.collision_type = collision_types["objects_player_1"]
    space1.add(circle_body, circle_shape)
    circle_body.position = (320, 240)  
    pymunk_objects.append(circle_shape)

def process_hit(arbiter, space, data):
    # Get objects that were involved in collision
    print("__________________ COLISION __________________")

    print(f"{len(arbiter.shapes)} shapes collided:")
    kinematic_shapes = []
    for shape in arbiter.shapes:
        if(shape.body.body_type != pymunk.Body.KINEMATIC):
            position = shape.body.position
            space.remove(shape, shape.body)
            pymunk_objects.remove(shape)
            radius = shape.radius
            body = pymunk.Body(1, 100)
            body.position = (320, 240)

            vertices = []
            for contour in contours:
                contour = np.squeeze(contour)
                for point in contour:
                    vertices.append((point[0], plankie.shape[0]-point[1]))


            #vertices1 = [(0, 0), (0, radius), (-radius, radius), (-radius, 0)]
            vertices2 = [(0, 0), (0, radius), (radius, radius), (radius, 0)]
            poly1 = pymunk.Poly(body, vertices)
            poly1.collision_type = collision_types["broken_objects"]
            poly1.body.position = position
            poly2 = pymunk.Poly(None, vertices2)
            poly2.collision_type = collision_types["broken_objects"]

            space.add(body,poly1)
            pymunk_objects.extend([poly1])


    shape1, shape2 = arbiter.shapes
    body1, body2 = shape1.body, shape2.body
    print("Collision occurred between", body1, "and", body2, "on: ", body1.position)
    #force = pymunk.Vec2d(5000,0)
    #body2.apply_force_at_local_point(force, (0, 0))
    return True

def out_of_bounds(arbiter, space, data):
    print("__________________ OUT OF BOUNDS __________________")
    object_shape = arbiter.shapes[0]
    space.remove(object_shape, object_shape.body)
    pymunk_objects.remove(object_shape)
    print("Circle ",arbiter.shapes[0] ," has left the screen!")
    return True

def draw_pymunk_object_in_opencv(image, pymunk_object): # for now only circles
    print("Drawing ", pymunk_object," on: ", pymunk_object.body.position)
    if isinstance(pymunk_object, pymunk.Poly):
        # Poly shapes are relative to the body position, so for opencv use add it as offset
        vertices = [(v+pymunk_object.body.position) for v in pymunk_object.get_vertices()]
        vertices = np.array(vertices, dtype=np.int32)
        #cv2.fillPoly(image, [vertices], (255, 255, 255))
        cv2.drawContours(image, contours, -1, 128, 2)

    else:
        pos = pymunk_object.body.position
        x, y = int(pos.x), int(pos.y)
        cv2.circle(image, (x, y), 25, (255, 255, 255), -1)


space = pymunk.Space()
space.gravity = (0, 980)
collision_type = 1
handler = space.add_collision_handler(collision_types["limbs_player_1"], collision_types["objects_player_1"])
handler.begin = process_hit

#handler2 = space.add_collision_handler(4,99)
#handler2.separate = out_of_bounds

left_segment = pymunk.Segment(space.static_body, (0, 0), (0, 580), 1)
right_segment = pymunk.Segment(space.static_body, (640, 0), (640, 580), 1)
bottom_segment = pymunk.Segment(space.static_body, (0, 380), (640, 380), 1) # below screen size for collision + removal effort
bottom_segment.collision_type = 99 
#bottom_segment.sensor = True
top_segment = pymunk.Segment(space.static_body, (0, 0), (640, 0), 1)

space.add(left_segment, right_segment, top_segment,bottom_segment)


line_left_hand_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
line_left_hand_shape = pymunk.Poly(line_left_hand_body, [(-100, 0), (100, 0)])
line_left_hand_shape.collision_type = collision_type
space.add(line_left_hand_body, line_left_hand_shape)
line_left_hand_shape.player_limb = "left hand"

line_right_hand_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
line_right_hand_shape = pymunk.Poly(line_right_hand_body, [(-1000, 0), (1000, 0)])
line_right_hand_shape.collision_type = collision_type
space.add(line_right_hand_body, line_right_hand_shape)
line_right_hand_shape.player_limb = "right hand"

background = cv2.imread("resources/dojo.png", cv2.IMREAD_UNCHANGED)
background = cv2.cvtColor(background, cv2.COLOR_BGRA2RGBA)
background = cv2.resize(background,(camera_width,camera_height))
#original_background = cv2.flip(original_background,1)

while cap.isOpened():    
    display_fps = cvFpsCalc.get()
    ret, frame = cap.read()
    if not ret:
      break

    height, width, _ = frame.shape
    # if (number_of_players == 1):
    #     frame = frame[:,100:width-100, :] # singleplayer
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = cv2.flip(image,1)
    

    #making image writeable to false improves prediction
    image.flags.writeable = False  
    results = []  
    results = yolo_model(image, max_det=number_of_players, verbose=False)
    image.flags.writeable = True  

    space.step(1/60)
    image = Generics.overlayPNG(image, background, pos=[0, 0])
    for pymunk_object in pymunk_objects:
        draw_pymunk_object_in_opencv(image, pymunk_object)
    # image = Generics.overlayPNG(image,background, [0,0])
    

    try:
        for i,result in enumerate(results):
            #print("Result: ") todo: debug with person
            keypoints = result.keypoints.cpu().numpy()[0]
            # Depending on the boolean statement and number of players, update a person's tracking
            player_index = int(keypoints[2][0]) > (camera_width / number_of_players) 
            players[player_index].update_tracking(keypoints)
            get_trailing(players[player_index], image)
            Generics.draw_stick_figure(image, keypoints)

            if(players[player_index].check_hit(image, woodLine)):
                woodX=random.randint(100, width-110)
                woodY=random.randint(100, 300)
                woodLine = Polygon([(woodX, woodY), (woodX, woodY+size),(woodX +size, woodY), (woodX +size, woodY +size)])
                 
    except Exception:
        traceback.print_exc()
        pass
    

    #image = results[0].plot()


    # Recolor image back to BGR for rendering

    image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    cv2.putText(image, "FPS:" + str(display_fps), (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 

    # cv2.putText(image, current_player, (int(camera_width/2 -20), 30),
    #                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 
    #cv2.line(image, (width // 2,0), (width // 2, height), (0,255,0), 2)
    image = Generics.overlayPNG(image, wood, pos=[woodX, woodY])
    
    cv2.imshow('webcam', image)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        spawn_object(space)

cap.release()
cv2.destroyAllWindows()

