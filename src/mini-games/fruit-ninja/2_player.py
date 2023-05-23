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
object_types = {
    "wooden_plank":1,
    "rock":2,
    "wooden_plank_broken":3,
    "rock_broken":4,
}

yolo_model = YOLO('yolov8l-pose.pt')  # load an official model
number_of_players = 1 # todo: argument

space = pymunk.Space()
space.gravity = (0, 980)
players = []
for i in range(number_of_players):
    player = CVNinjaPlayer(collision_types["limbs_player_" + str(i+1)])
    space.add(player.line_left_hand_body, player.line_left_hand_shape)
    space.add(player.line_right_hand_body, player.line_right_hand_shape)
    space.add(player.line_left_leg_body, player.line_left_leg_shape)
    space.add(player.line_right_leg_body, player.line_right_leg_shape)
    players.append(player)


camera_width = 640
camera_height = 480

def get_trailing(player, image):

    # method is considered "unsafe" due to potential physics issues, not a problem with for my use case (collision detection). 
    player.line_left_leg_shape.unsafe_set_vertices([(player.left_foot_track_points[-1]), (player.left_foot_track_points[0])])
    player.line_right_leg_shape.unsafe_set_vertices([(player.right_foot_track_points[-1]), (player.right_foot_track_points[0])])
    player.line_left_hand_shape.unsafe_set_vertices([(player.left_hand_track_points[-1]),(player.left_hand_track_points[0])])
    player.line_right_hand_shape.unsafe_set_vertices([(player.right_hand_track_points[-1]),(player.right_hand_track_points[0])])

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

def prepareImage(image, size):
    image = cv2.resize(image, (size, size), interpolation=cv2.INTER_LINEAR)
    vertices = Generics.get_vertices_by_image(image)
    image_horizontal_splice_left =  image[:,:size//2]
    image_horizontal_splice_left_vertices = Generics.get_vertices_by_image(image_horizontal_splice_left)
    image_horizontal_splice_right = wood[:,size//2:]
    image_horizontal_splice_right_vertices = Generics.get_vertices_by_image(image_horizontal_splice_right)


wood = cv2.imread('resources/plank.png', cv2.IMREAD_UNCHANGED)
stone = cv2.imread('resources/rock.png', cv2.IMREAD_UNCHANGED)
bomb = cv2.imread('resources/bomb.png', cv2.IMREAD_UNCHANGED)

size = 70
wood = cv2.resize(wood, (size, size), interpolation=cv2.INTER_LINEAR)
stone = cv2.resize(stone, (size, size), interpolation=cv2.INTER_LINEAR)
bomb = cv2.resize(bomb, (size, size), interpolation=cv2.INTER_LINEAR)

# woodX=random.randint(100, camera_width-110)
# woodY=random.randint(100, 300)
# woodLine = Polygon([(woodX, woodY), (woodX, woodY+size),(woodX +size, woodY), (woodX +size, woodY +size)  ])

wood_vertices = Generics.get_vertices_by_image(wood)
stone_vertices = Generics.get_vertices_by_image(stone)
bomb_vertices = Generics.get_vertices_by_image(bomb)


wood_horizontal_splice_left = np.zeros_like(wood, dtype=np.uint8)
wood_horizontal_splice_right = np.zeros_like(wood, dtype=np.uint8)
for i in range(size):
    wood_horizontal_splice_right[i, :size-i] = wood[i, :size-i]
    wood_horizontal_splice_left[i, size-i:] = wood[i, size-i:]

wood_horizontal_splice_left =  wood[:,:size//2]
wood_horizontal_splice_left_vertices = Generics.get_vertices_by_image(wood_horizontal_splice_left)


wood_horizontal_splice_right = wood[:,size//2:]
wood_horizontal_splice_right_vertices = Generics.get_vertices_by_image(wood_horizontal_splice_right)

random_objects = [wood, stone, bomb]
# shapes, really
pymunk_objects = []
def spawn_object(space1, object_type, collision_type=2, position=(0,0), previous_object=None):
    
    if (object_type == object_types["wooden_plank"]):
        print("Spawning Wooden plank on: ", position)
        wood_body = pymunk.Body(1, 100)
        wood_shape = pymunk.Poly(wood_body, wood_vertices)
        wood_shape.collision_type = int(collision_type)
        space1.add(wood_body, wood_shape)
        wood_body.position = position
        wood_shape.object_type = object_type
        pymunk_objects.append(wood_shape)
        print("Current amount of objects: ", len(pymunk_objects))
    elif (object_type == object_types["wooden_plank_broken"]):
        wood_piece_1_body = pymunk.Body(1, 100)
        wood_piece_1_shape = pymunk.Poly(wood_piece_1_body, wood_horizontal_splice_left_vertices)
        wood_piece_1_shape.collision_type = collision_types["broken_objects"]
        space1.add(wood_piece_1_body, wood_piece_1_shape)
        wood_piece_1_body.position = previous_object.body.position 
        wood_piece_1_shape.image = wood_horizontal_splice_left
        wood_piece_1_shape.object_type = object_type
        wood_piece_1_shape.image_side = "left"
        wood_piece_1_body.apply_impulse_at_local_point((-100, 0))

        wood_piece_2_body = pymunk.Body(1, 100)
        wood_piece_2_shape = pymunk.Poly(wood_piece_2_body, wood_horizontal_splice_right_vertices)
        wood_piece_2_shape.collision_type = collision_types["broken_objects"]
        space1.add(wood_piece_2_body, wood_piece_2_shape)
        wood_piece_2_body.position = previous_object.body.position 
        wood_piece_2_shape.object_type = object_type
        wood_piece_2_shape.image = wood_horizontal_splice_right
        wood_piece_2_shape.image_side = "right"
        wood_piece_2_body.apply_impulse_at_local_point((100, 0))
        pymunk_objects.extend([wood_piece_1_shape,wood_piece_2_shape])

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
            spawn_object(space, object_types["wooden_plank_broken"], position, previous_object=shape)


    shape1, shape2 = arbiter.shapes
    body1, body2 = shape1.body, shape2.body
    print("Collision occurred between", body1, "and", body2)
    print("Wood location: ", body2.position  )
    

    random_x = random.randint(100, 600)
    spawn_object(space, object_types["wooden_plank"], collision_type=2, position=(random_x,80), previous_object=None)
    #force = pymunk.Vec2d(5000,0)
    #body2.apply_force_at_local_point(force, (0, 0))
    return True

def out_of_bounds(arbiter, space, data):
    print("__________________ OUT OF BOUNDS __________________")
    object_shape = arbiter.shapes[0]
    space.remove(object_shape, object_shape.body)
    pymunk_objects.remove(object_shape)
    print("Shape ",arbiter.shapes[0] ," has left the screen!")
    return True

def draw_pymunk_object_in_opencv(image, pymunk_object): 
    if isinstance(pymunk_object, pymunk.Poly):
        if (pymunk_object.object_type == object_types["wooden_plank"]):
            vertices = [(v+pymunk_object.body.position) for v in pymunk_object.get_vertices()]
            vertices = np.array(vertices, dtype=np.int32)
            #cv2.fillPoly(image, [vertices], (255, 255, 255))
            pos = pymunk_object.body.position
            x, y = int(pos.x), int(pos.y)
            #print("Drawing ", pymunk_object," on: ", pymunk_object.body.position)
            image = Generics.overlayPNG(image, wood, [x,y] )
        elif(pymunk_object.object_type == object_types["wooden_plank_broken"]):
            # todo: maybe map all image objects predefined stuff and do lookups instead of IFs
            vertices = [(v+pymunk_object.body.position) for v in pymunk_object.get_vertices()]
            vertices = np.array(vertices, dtype=np.int32)
            #cv2.fillPoly(image, [vertices], (255, 255, 255))
            pos = pymunk_object.body.position
            x, y = int(pos.x), int(pos.y)
            #print("Drawing ", pymunk_object," on: ", pymunk_object.body.position)
            if pymunk_object.image_side == "right":
                x = int(x + wood.shape[1]//2)
            image = Generics.overlayPNG(image, pymunk_object.image, [x,y] )



    else:
        pos = pymunk_object.body.position
        x, y = int(pos.x), int(pos.y)
        cv2.circle(image, (x, y), 25, (255, 255, 255), -1)
    return image


collision_type = 1
handler = space.add_collision_handler(collision_types["limbs_player_1"], collision_types["objects_player_1"])
handler.begin = process_hit

handler2 = space.add_collision_handler(collision_types["broken_objects"],collision_types["void"])
handler2.separate = out_of_bounds

handler3 = space.add_collision_handler(collision_types["objects_player_1"],collision_types["void"])
handler3.separate = out_of_bounds

left_segment = pymunk.Segment(space.static_body, (0, 0), (0, 580), 1)
right_segment = pymunk.Segment(space.static_body, (640, 0), (640, 580), 1)
bottom_segment = pymunk.Segment(space.static_body, (0, 380), (640, 800), 1) # below screen size for collision + removal effort
bottom_segment.collision_type = 99 
bottom_segment.sensor = True
top_segment = pymunk.Segment(space.static_body, (0, 0), (640, 0), 1)

space.add(left_segment, right_segment, top_segment,bottom_segment)

background = cv2.imread("resources/dojo.png", cv2.IMREAD_UNCHANGED)
background = cv2.cvtColor(background, cv2.COLOR_BGRA2RGBA)
background = cv2.resize(background,(camera_width,camera_height))
#original_background = cv2.flip(original_background,1)
count = 0
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
    if(count ==0):
        spawn_object(space, object_type=object_types["wooden_plank"], position=(540, 80))
        count = 1
    
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
            players[player_index].reset_keypoints()
            # end of an era
            # if(players[player_index].check_hit(image, woodLine)):
            #     woodX=random.randint(100, width-110)
            #     woodY=random.randint(100, 300)
            #     woodLine = Polygon([(woodX, woodY), (woodX, woodY+size),(woodX +size, woodY), (woodX +size, woodY +size)])
                 
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
    
    for pymunk_object in pymunk_objects:
        pymunk_object.body.angle+=0.023
        image = draw_pymunk_object_in_opencv(image, pymunk_object)
    cv2.imshow('webcam', image)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        spawn_object(space, object_type= object_types["wooden_plank"], position=(540, 80) )


cap.release()
cv2.destroyAllWindows()

