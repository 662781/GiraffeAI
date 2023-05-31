import random
import traceback
import cv2
from shared.model import YOLO
from shared.utils import Generics, CvFpsCalc, CVAssets
from shared.model import CVNinjaPlayer, CVGame
from cvninja.model import CVNinjaPlank, CVNinjaRock, CVNinjaBomb
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
          self.yolo_model = YOLO()  # load an official model

          self.wood = cv2.imread(CVAssets.IMAGE_PLANK, cv2.IMREAD_UNCHANGED)

          self.stone = cv2.imread(CVAssets.IMAGE_ROCK, cv2.IMREAD_UNCHANGED)
          self.bomb = cv2.imread(CVAssets.IMAGE_BOMB, cv2.IMREAD_UNCHANGED)
          self.size = 70
          self.objects_player_1 = [CVNinjaBomb(self.bomb, self.size)]
         

          self.background = cv2.imread(CVAssets.IMAGE_DOJO, cv2.IMREAD_UNCHANGED)
          self.background = cv2.cvtColor(self.background, cv2.COLOR_BGRA2RGBA)



     def setup(self, options):
          for object_spawner in self.objects_player_1:
               for shape in object_spawner.pymunk_objects_to_draw:
                    object_spawner.pymunk_objects_to_draw.remove(shape)
          self.space = pymunk.Space()
          self.space.gravity = (0, 980)
          self.players = []
          self.options["NUMBER_OF_PLAYERS"] = 1
          for i in range(self.options["NUMBER_OF_PLAYERS"]):
               
               player = CVNinjaPlayer(self.collision_types["limbs_player_" + str(i+1)])
               self.space.add(player.line_left_hand_body, player.line_left_hand_shape)
               self.space.add(player.line_right_hand_body, player.line_right_hand_shape)
               self.space.add(player.line_left_leg_body, player.line_left_leg_shape)
               self.space.add(player.line_right_leg_body, player.line_right_leg_shape)
               self.players.append(player)

          self.background = cv2.resize(self.background, (self.options["CAMERA_WIDTH"], self.options["CAMERA_WIDTH"]))
          handler = self.space.add_collision_handler(self.collision_types["limbs_player_1"], self.collision_types["objects_player_1"])
          handler.data["player"] = self.players[0] # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
          handler.begin = self.process_hit

          handler2 = self.space.add_collision_handler(self.collision_types["broken_objects"],self.collision_types["void"])
          handler2.separate = self.out_of_bounds

          handler3 = self.space.add_collision_handler(self.collision_types["objects_player_1"],self.collision_types["void"])
          handler3.separate = self.out_of_bounds

          # Real boundaries of the space are a bit bigger than 480p, for illusion of objects appearing in and vanishing from the screen. 
          left_segment = pymunk.Segment(self.space.static_body, (-100, 0), (-100, 800), 100)
          right_segment = pymunk.Segment(self.space.static_body, (740, 0), (740, 800), 100)
          bottom_segment = pymunk.Segment(self.space.static_body, (-100, 800), (740, 800), 100)
          bottom_segment.collision_type = 99 
          bottom_segment.sensor = True
          top_segment = pymunk.Segment(self.space.static_body, (-100, -100), (740, -100), 100)
          self.space.add(left_segment, right_segment, top_segment, bottom_segment)

          self.count = 0

     def process_hit(self, arbiter, space, data):
          # Get objects that were involved in collision
          #print("__________________ COLISION __________________")
          #print(f"{len(arbiter.shapes)} shapes collided:")
          kinematic_shape = arbiter.shapes[0]
          shape_trail_length = data["player"].get_trailing_length_by_limb(kinematic_shape.player_limb)
          # The shape attached to the player's limb has most accurate contact point. 
          contact_point = kinematic_shape.get_vertices()[1]
          #print("Hit with ", kinematic_shape.player_limb)
          #if(kinematic_shape.player_limb == "left hand" or kinematic_shape.player_limb == "right hand"):

          for shape in arbiter.shapes:
               if(shape.body.body_type != pymunk.Body.KINEMATIC):
                    # Check if you did an actual movement and not just small shifts
                    if(shape_trail_length > 10 and shape.parent_object.collision_requirements_are_met(data["player"], kinematic_shape)): 
                         try:
                              shape.parent_object.collision_aftermath(space, shape, contact_point)
                         except RuntimeError as error: # Catch specific error that occurs when two limbs collide on an object at the same time
                              print(str(error))
                              break
                         if isinstance(shape.parent_object,CVNinjaBomb):
                              # uh oh, bomba
                              data["player"].strikes +=1
                              break
                         gets_double_points =  (kinematic_shape.player_limb == "left leg" or kinematic_shape.player_limb == "right leg")
                         data["player"].score += shape.parent_object.calculate_score(shape, gets_double_points)
                         print("Player score: ", data["player"].score)
                         random_x = random.randint(100, 600)
                         self.objects_player_1[0].spawn_object(space, self.collision_types["objects_player_1"], position=(random_x, 80))
                    else:
                         print("Trail: ",shape_trail_length )
          return True

     def out_of_bounds(self, arbiter, space, data):
         #print("__________________ OUT OF BOUNDS __________________")
          object_shape = arbiter.shapes[0]
          space.remove(object_shape, object_shape.body)
          object_shape.parent_object.pymunk_objects_to_draw.remove(object_shape) # maybe method with some logic behind it. 
          #print("Shape ",arbiter.shapes[0] ," has left the screen!")
          #print("Current objects on screen: ", len(self.objects_player_1[0].pymunk_objects_to_draw) )
          return True     

     def cleanup(self):
          for object_spawner in self.objects_player_1:
               for shape in object_spawner.pymunk_objects_to_draw:
                    object_spawner.pymunk_objects_to_draw.remove(shape)
          super().cleanup()

     def update(self, frame):
          display_fps = self.cvFpsCalc.get()
          height, width, _ = frame.shape
          image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
          image = cv2.flip(image, 1)

          image.flags.writeable = False  
          results = self.yolo_model(image, max_det=self.options["NUMBER_OF_PLAYERS"], verbose=False)
          image.flags.writeable = True  

          self.space.step(1/60)
          image = Generics.overlayPNG(image, self.background, pos=[0, 0])
          if self.count == 0:
               self.objects_player_1[0].spawn_object(self.space, self.collision_types["objects_player_1"], position=(540, 80))
               self.count = 1

          try:
               for i, result in enumerate(results):
                    keypoints = result.keypoints.cpu().numpy()[0]
                    player_index = int(keypoints[2][0]) > (self.options["CAMERA_WIDTH"] / self.options["NUMBER_OF_PLAYERS"]) 
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
          image = Generics.put_text_with_custom_font(image, "Score: " + str(self.players[0].score), (400,20), CVAssets.FONT_FRUIT_NINJA,
                                                       25, (0,0,0), outline_color = (255, 255, 255), outline_width=2)
          image = self._draw_amount_of_strikes(image,self.players[0].strikes)
          # For debugging bugged objects 
          # print("Current objects on screen: ", len(self.objects_player_1[0].pymunk_objects_to_draw) )
          # for broken_object in self.objects_player_1[0].pymunk_objects_to_draw:
          #      print(broken_object.body.position)
          if cv2.waitKey(1) & 0xFF == ord('q'):
               #self.should_switch = True
               #self.next_game = "Main Menu"
               self.objects_player_1[0].spawn_object(self.space, self.collision_types["objects_player_1"], position=(540, 80))
               self.players[0].strikes +=1
          
          return image
        
     def _draw_amount_of_strikes(self, image, strikes):
          """Draws the strike crosses and colors them red if the player has a strike"""
          font_color_white = (255,255,255)
          font_color_red = (0, 0,255)
          outline_color = (0,0,0)
          image = Generics.put_text_with_custom_font(image, "X", (10,50), CVAssets.FONT_FRUIT_NINJA,
                                                       25, font_color = font_color_red if strikes >= 1 else  font_color_white
                                                       , outline_color = outline_color, outline_width=3)
          image = Generics.put_text_with_custom_font(image, "X", (35,50), CVAssets.FONT_FRUIT_NINJA,
                                                       40, font_color = font_color_red if strikes >= 2 else  font_color_white 
                                                       , outline_color = outline_color, outline_width=3)
          image = Generics.put_text_with_custom_font(image, "X", (70,50), CVAssets.FONT_FRUIT_NINJA,
                                                       60, font_color = font_color_red if strikes >= 3 else  font_color_white 
                                                       , outline_color = outline_color, outline_width=3)
          return image