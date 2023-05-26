import random
import traceback
import cv2
from ultralytics import YOLO
from shared.utils import CvFpsCalc
from shared.utils import Generics
from shared.model import CVNinjaPlayer, CVGame
from cvninja.model import CVNinjaPlank
import pymunk

class CVNinjaGame(CVGame):
     def __init__(self):
          super().__init__()
          self.collision_types = {
               "limbs_player_1": 1,
               "objects_player_1" : 2,
               "broken_objects" : 3,
               "void": 99, 
          }
          self.object_types = {
               "wooden_plank":1,
               "rock":2,
               "wooden_plank_broken":3,
               "rock_broken":4,
          }
          self.yolo_model = YOLO('resources/models/yolov8l-pose.pt')  # load an official model
          self.number_of_players = 1 # todo: argument
          self.space = pymunk.Space()
          self.space.gravity = (0, 980)
          self.players = []
          self.background = None
          self.objects_player_1 = None

          self.wood = cv2.imread('cvninja/assets/plank.png', cv2.IMREAD_UNCHANGED)

          self.stone = cv2.imread('cvninja/assets/rock.png', cv2.IMREAD_UNCHANGED)
          self.bomb = cv2.imread('cvninja/assets/bomb.png', cv2.IMREAD_UNCHANGED)

          self.size = 70
          self.objects_player_1 = [CVNinjaPlank(self.wood, self.size)]

          self.background = cv2.imread("shared/assets/dojo.png", cv2.IMREAD_UNCHANGED)
          self.background = cv2.cvtColor(self.background, cv2.COLOR_BGRA2RGBA)
          self.background = cv2.resize(self.background, (self.camera_width, self.camera_height))


     def setup(self):
          self.current_player = "none"
          
          for i in range(self.number_of_players):
               player = CVNinjaPlayer(self.collision_types["limbs_player_" + str(i+1)])
               self.space.add(player.line_left_hand_body, player.line_left_hand_shape)
               self.space.add(player.line_right_hand_body, player.line_right_hand_shape)
               self.space.add(player.line_left_leg_body, player.line_left_leg_shape)
               self.space.add(player.line_right_leg_body, player.line_right_leg_shape)
               self.players.append(player)

          handler = self.space.add_collision_handler(self.collision_types["limbs_player_1"], self.collision_types["objects_player_1"])
          handler.data["player"] = self.players[0] # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
          handler.begin = self.process_hit

          handler2 = self.space.add_collision_handler(self.collision_types["broken_objects"],self.collision_types["void"])
          handler2.separate = self.out_of_bounds

          handler3 = self.space.add_collision_handler(self.collision_types["objects_player_1"],self.collision_types["void"])
          handler3.separate = self.out_of_bounds


          left_segment = pymunk.Segment(self.space.static_body, (0, 0), (0, 580), 1)
          right_segment = pymunk.Segment(self.space.static_body, (640, 0), (640, 580), 1)
          bottom_segment = pymunk.Segment(self.space.static_body, (0, 380), (640, 800), 1)
          bottom_segment.collision_type = 99 
          bottom_segment.sensor = True
          top_segment = pymunk.Segment(self.space.static_body, (0, 0), (640, 0), 1)

          self.space.add(left_segment, right_segment, top_segment, bottom_segment)

          self.count = 0




     def process_hit(self, arbiter, space, data):
          # Get objects that were involved in collision
          print("__________________ COLISION __________________")
          print(f"{len(arbiter.shapes)} shapes collided:")
          kinematic_shape = arbiter.shapes[0]
          shape_trail_length = data["player"].get_trailing_length_by_limb(kinematic_shape.player_limb)
          print("Hit with ", kinematic_shape.player_limb)
          for shape in arbiter.shapes:
               if(shape.body.body_type != pymunk.Body.KINEMATIC):
                    if(shape_trail_length > 10): # If you did an actual movement and not just small shifts
                         shape.parent_object.collision_aftermath(space, shape)
                         space.remove(shape, shape.body)
                         random_x = random.randint(100, 600)
                         self.objects_player_1[0].spawn_object(space, self.collision_types["objects_player_1"], position=(random_x, 80))
                    else:
                         print("Trail not long enough: ",shape_trail_length )
                    #shape.parent_object.spawn_object(space, collision_types["objects_player_1"],position=(random_x, 80))

          shape1, shape2 = arbiter.shapes
          body1, body2 = shape1.body, shape2.body
          print("Collision occurred between", body1, "and", body2)
          print("Wood location: ", body2.position  )
          return True

     def out_of_bounds(self, arbiter, space, data):
          print("__________________ OUT OF BOUNDS __________________")
          object_shape = arbiter.shapes[0]
          space.remove(object_shape, object_shape.body)
          object_shape.parent_object.pymunk_objects_to_draw.remove(object_shape) # maybe method with some logic behind it. 
          #print("Shape ",arbiter.shapes[0] ," has left the screen!")
          print("Current objects on screen: ", len(self.objects_player_1[0].pymunk_objects_to_draw) )
          return True     

     def cleanup(self):
          super().cleanup()

     def update(self, frame):
          display_fps = self.cvFpsCalc.get()
          height, width, _ = frame.shape
          image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
          image = cv2.flip(image, 1)

          image.flags.writeable = False  
          results = self.yolo_model(image, max_det=self.number_of_players, verbose=False)
          image.flags.writeable = True  

          self.space.step(1/60)
          image = Generics.overlayPNG(image, self.background, pos=[0, 0])
          if self.count == 0:
               self.objects_player_1[0].spawn_object(self.space, self.collision_types["objects_player_1"], position=(540, 80))
               self.count = 1

          try:
               for i, result in enumerate(results):
                    keypoints = result.keypoints.cpu().numpy()[0]
                    player_index = int(keypoints[2][0]) > (self.camera_width / self.number_of_players) 
                    self.players[player_index].update_tracking(keypoints)
                    Generics.get_player_trailing(self.players[player_index], image)
                    Generics.draw_stick_figure(image, keypoints)
                    self.players[player_index].reset_keypoints()

          except Exception:
               traceback.print_exc()
               pass

          image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
          cv2.putText(image, "FPS:" + str(display_fps), (10, 30),
                         cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 

          for object_spawner in self.objects_player_1:
               for shape in object_spawner.pymunk_objects_to_draw:
                    image = Generics.draw_pymunk_object_in_opencv(image, shape)

          #cv2.imshow('webcam', image)

          if cv2.waitKey(1) & 0xFF == ord('q'):
               self.should_switch = True
               self.next_game = "Main Menu"
               # self.objects_player_1[0].spawn_object(self.space, self.collision_types["objects_player_1"], position=(540, 80))
          
          return image
        


