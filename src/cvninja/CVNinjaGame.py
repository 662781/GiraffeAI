import random
import traceback
import cv2
from shared.model import YOLO
from shared.utils import Generics, CvFpsCalc, CVAssets
from shared.model import CVNinjaPlayer, CVGame
from cvninja.model import CVNinjaPlank, CVNinjaRock, CVNinjaBomb, CVNinjaMicha
from menus.model import MainMenuObject
import pymunk
import threading
import time
from playsound import playsound
import pandas as pd


class CVNinjaGame(CVGame):
     def __init__(self):
          super().__init__()
          # Collision types used all over the game to handle events such as object collision and object out of bounds events
          self.collision_types = {
               "limbs_player_1": 1,
               "limbs_player_2" : 2,
               "broken_objects" : 3,
               "objects_player_1" : 4,
               "objects_player_2": 5,
               "menu_option_main_menu": 6,
               "menu_option_play_again": 7,
               "void": 99, 
          }
          self._initialize_assets()

          # set left,right and middle spawn positions
          # todo: multiplayer will need different spawn locations for each player
          self.spawn_postitions=  [(-70, 50),(-70, 40),(-70, 30),# left corner
                                   (710, 50), (710, 40), (710, 30), # right corner
                                   (100,-50), (300,-50), (500,-50)] # middle top


     def setup(self, options):
          #self.options = options
          self.options["NUMBER_OF_PLAYERS"] = 2 # todo, dynamic
          
          self.cvninja_object_spawners ={} # Each player gets a list of object spawners assigned to him 
          # Setup 
          self.menu_options = [MainMenuObject(self.image_main_menu, 150), MainMenuObject(self.image_play_again, 150)]

          if(self.options["NUMBER_OF_PLAYERS"] == 1):
               self.object_spawner_rotation = [CVNinjaBomb(self.bomb, 100),CVNinjaRock(self.rock, 80), CVNinjaPlank(self.plank, 70),CVNinjaMicha(self.micha, 160)]
          else:
               self.object_spawner_rotation = [CVNinjaRock(self.rock, 80), CVNinjaPlank(self.plank, 70),CVNinjaMicha(self.micha, 160)]

          self.bomb_tutorial_done = False # singleplayer only 
          self.stop_threads = False

          for player_object_spawners in self.cvninja_object_spawners:
               for object_spawner in player_object_spawners:
                    for shape in object_spawner.pymunk_objects_to_draw:
                         object_spawner.pymunk_objects_to_draw.remove(shape)

          self.space = pymunk.Space()
          self.space.gravity = (0, 980)
          self.players = []
          self.state_end_game = False
          

 
          for i in range(self.options["NUMBER_OF_PLAYERS"]):
               player_index = str(i+1)
               
               player = CVNinjaPlayer(self.collision_types["limbs_player_" + player_index])
               print("Creating Player " + player_index, " ", player)
               self.cvninja_object_spawners["Player-" + player_index] =  self.object_spawner_rotation
               self.space.add(player.line_left_hand_body, player.line_left_hand_shape)
               self.space.add(player.line_right_hand_body, player.line_right_hand_shape)
               self.space.add(player.line_left_leg_body, player.line_left_leg_shape)
               self.space.add(player.line_right_leg_body, player.line_right_leg_shape)
               self.players.append(player)
               
               print("Giving thread player: ", player, " and index: ", player_index)
               self._create_event_handlers_for_player(player_index, player)
          
      
          # Determine all the options, use the first player for it 
          self.object_options = [index for index, _ in enumerate(self.cvninja_object_spawners["Player-1"])]
          

          # Real boundaries of the space are a bit bigger than 480p, for illusion of objects appearing in and vanishing from the screen. 
          left_segment = pymunk.Segment(self.space.static_body, (-200, 0), (-200, 800), 100)
          right_segment = pymunk.Segment(self.space.static_body, (840, 0), (840, 800), 100)
          bottom_segment = pymunk.Segment(self.space.static_body, (-200, 800), (840, 800), 100)
          bottom_segment.collision_type = 99 
          bottom_segment.sensor = True
          top_segment = pymunk.Segment(self.space.static_body, (-200, -100), (840, -100), 100)
          self.space.add(left_segment, right_segment, top_segment, bottom_segment)


          # Adding this dynamically seems to result into the last player getting all threads for himself, so manual adding for now
          self.thread1 = threading.Thread(target=lambda: self._handle_spawns_multiplayer(self.players[0], self.cvninja_object_spawners["Player-1"], self.spawn_postitions))
          self.thread2 = threading.Thread(target=lambda: self._handle_spawns_multiplayer(self.players[1], self.cvninja_object_spawners["Player-2"], self.spawn_postitions))
          self.thread1.start()
          self.thread2.start()

     def _draw_countdown(self):
          return
     def _create_event_handlers_for_player(self,player_index, player):
          """Creates collision and out of bounds handlers for a specific player number"""
          handlers_collision = [] 
          handlers_out_of_bounds = [self.space.add_collision_handler(self.collision_types["broken_objects"],self.collision_types["void"])]
          handlers_out_of_bounds[-1].separate = self.out_of_bounds

          handlers_collision.append(self.space.add_collision_handler(self.collision_types["limbs_player_" + player_index], self.collision_types["objects_player_" + player_index]))
          handlers_collision[-1].data["player"] = player
          handlers_collision[-1].begin = self.handle_collision

          handlers_collision.append(self.space.add_collision_handler(self.collision_types["objects_player_" + player_index],self.collision_types["void"]))
          handlers_collision[-1].data["player"] = player
          handlers_collision[-1].separate = self.out_of_bounds

          # Aftergame menus
          handlers_collision.append(self.space.add_collision_handler(self.collision_types["limbs_player_" + player_index], self.collision_types["menu_option_main_menu"]))
          handlers_collision[-1].data["player"] = self.players[0] # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
          handlers_collision[-1].begin = self._handle_menu

          handlers_collision.append(self.space.add_collision_handler(self.collision_types["limbs_player_" + player_index], self.collision_types["menu_option_play_again"]))
          handlers_collision[-1].data["player"] = self.players[0] # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
          handlers_collision[-1].begin = self._handle_menu

     def cleanup(self):
          # todo: change into dynamic
          self.stop_threads == False
          for player_index in range(len(self.cvninja_object_spawners)):
               for object_spawner in self.cvninja_object_spawners["Player-" + str(player_index+1)]:
                    for shape in object_spawner.pymunk_objects_to_draw:
                         object_spawner.pymunk_objects_to_draw.remove(shape)
          super().cleanup()

     def update(self, frame):
          display_fps = self.cvFpsCalc.get()
          image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
          image = cv2.flip(image, 1)
          image.flags.writeable = False  

          results = self.yolo_model(image, max_det=self.options["NUMBER_OF_PLAYERS"], verbose=False)
          image.flags.writeable = True  
          self.space.step(1/60)
          image = Generics.overlayPNG(image, self.background, pos=[0, 0])

          # Setup a Split screen for multiplayer
          region_width = self.options["CAMERA_WIDTH"] // self.options["NUMBER_OF_PLAYERS"]
          for i in range(1, self.options["NUMBER_OF_PLAYERS"]):
               x = region_width * i
               cv2.line(image, (x, 0), (x, self.options["CAMERA_HEIGHT"]), (0, 0, 0), 2) 

          self._update_players(image, results)

          image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
          cv2.putText(image, "FPS:" + str(display_fps), (460, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 

          for i, player in enumerate(self.players):
               image = self._draw_stats(image,player, 10 + (i * (self.options["CAMERA_WIDTH"] / 2)))
               if(player.strikes >= 10000):
                    image = self._draw_final_screen(image)
                    self.stop_threads = True
                    for menu_item in self.menu_options:
                         for shape in menu_item.pymunk_objects_to_draw:
                              image = Generics.draw_pymunk_object_in_opencv(image, shape)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                         self.should_switch = True
                         self.next_game = "Main Menu"
                    return image
              
          for player_index in range(len(self.cvninja_object_spawners)):
               for object_spawner in self.cvninja_object_spawners["Player-" + str(player_index+1)]:
                    for shape in object_spawner.pymunk_objects_to_draw:
                         image = Generics.draw_pymunk_object_in_opencv(image, shape)

          if cv2.waitKey(1) & 0xFF == ord('q'):
               self.should_switch = True
               self.next_game = "Main Menu"
          return image

     def _initialize_assets(self):
          """Load and setup the assets required to play the game"""
          self.yolo_model = YOLO()  # load an official model

          self.plank = cv2.imread(CVAssets.IMAGE_PLANK, cv2.IMREAD_UNCHANGED)
          self.rock = cv2.imread(CVAssets.IMAGE_ROCK, cv2.IMREAD_UNCHANGED)
          self.bomb = cv2.imread(CVAssets.IMAGE_BOMB, cv2.IMREAD_UNCHANGED)
          self.micha = cv2.imread(CVAssets.IMAGE_MISHA, cv2.IMREAD_UNCHANGED)
          self.image_play_again = cv2.imread(CVAssets.IMAGE_MENU_CVNINJA_PLAY_AGAIN, cv2.IMREAD_UNCHANGED)
          self.image_main_menu = cv2.imread(CVAssets.IMAGE_MENU_CVNINJA_MAIN_MENU, cv2.IMREAD_UNCHANGED)

          self.background = cv2.imread(CVAssets.IMAGE_DOJO, cv2.IMREAD_UNCHANGED)
          self.background = cv2.cvtColor(self.background, cv2.COLOR_BGRA2RGBA)
          self.background = cv2.resize(self.background, (self.options["CAMERA_WIDTH"], self.options["CAMERA_WIDTH"]))


     def _update_players(self, image, results):
          """Update and draw each player marked by the YOLO results"""
          try:
               some_count = 0

               for result in results:
                    for i in range(2):
                         print("Result ",i, ": ",result)
                         
                         #print("player: ", i)
                         keypoints = result.keypoints[i].cpu().numpy()
                         # some_count +=1
                         # Depending on the position in the results, we assign the results to update for a specific player
                         player_index = int(keypoints[2][0]) > (self.options["CAMERA_WIDTH"] / self.options["NUMBER_OF_PLAYERS"]) 
                         cv2.putText(image, "Player-" + str(int(player_index)+1), (int(keypoints[2][0]), int(keypoints[2][1])), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 

                         self.players[player_index].update_tracking(keypoints)
                         Generics.get_player_trailing(self.players[player_index], image)
                         Generics.draw_stick_figure(image, keypoints)
                         self.players[player_index].reset_keypoints()
          except Exception:
               traceback.print_exc()
               pass
        
     def _draw_stats(self, image, player, x):
          """Draws the strike crosses and colors them red if the player has a strike"""
          y = 35
          black = (0,0,0)
          white = (255,255,255)
          red = (0, 0,255)
          image = Generics.put_text_with_ninja_font(image, "Score: " + str(player.score), (x,10),
                                                  size_class = "Small",
                                                  font_color = black,
                                                  outline_color = white,
                                                  outline_width=2)
          if(self.options["NUMBER_OF_PLAYERS"] == 1):
               strikes = player.strikes
               image = Generics.put_text_with_ninja_font(image, "X", (x,y),
                                                            size_class = "Small",
                                                            font_color = red if strikes >= 1 else  white,
                                                            outline_color = black, 
                                                            outline_width=3)
               image = Generics.put_text_with_ninja_font(image, "X", (x+25,y),
                                                            size_class = "Medium", 
                                                            font_color = red if strikes >= 2 else  white,
                                                            outline_color = black,
                                                            outline_width=3)
               image = Generics.put_text_with_ninja_font(image, "X", (x +60,y),
                                                            size_class = "Large", 
                                                            font_color = red if strikes >= 3 else  white, 
                                                            outline_color = black, 
                                                            outline_width=3)
          return image
     
     def _draw_final_screen(self, image):
          if(not self.state_end_game):
               self.space.gravity = (0,0)
               self.menu_options[0].spawn_object(self.space, self.collision_types["menu_option_main_menu"], position = (100, 80))
               self.menu_options[1].spawn_object(self.space, self.collision_types["menu_option_play_again"], position = (400,80))
               self.state_end_game = True
          return image

     def _handle_spawns(self, player, object_spawners, spawn_postitions):
          print("Creating a thread for:", player)
          while self.stop_threads == False:
               
               time.sleep(5)

               random_spawn = spawn_postitions[random.randint(0,len(spawn_postitions)-1)]
               options = [0,1,2,3]
               weights = [40, 60, 60, 5] 
               
               if(player.score <= 250):
                    one_time_weights = [0, 50, 50, 5] 
                    random_object = random.choices(options, one_time_weights)[0]
                    object_spawners[random_object].spawn_object(self.space, self.collision_types["objects_player_" + str(player.collision_type)], position = random_spawn)
                    continue  
               if(player.score > 250 and self.bomb_tutorial_done):
                    max_objects = 5
                    scaling_factor = min(player.score // 150, max_objects)
                    for _ in range(scaling_factor):
                         random_object = random.choices(options, weights)[0]
                         object_spawners[random_object].spawn_object(
                              self.space,
                              self.collision_types["objects_player_" + str(player.collision_type)],
                              position=random_spawn
                         )
                         random_spawn = spawn_postitions[random.randint(0,len(spawn_postitions)-1)]
                         time.sleep(.8)
               else:
                    bomb_only_weights = [100, 0, 0, 0]
                    random_object = random.choices(options, bomb_only_weights)[0]
                    random_spawn = spawn_postitions[random.randint(0,len(spawn_postitions)-1)]
                    object_spawners[random_object].spawn_object(
                         self.space, 
                         self.collision_types["objects_player_" + str(player.collision_type)], 
                         position = random_spawn
                    )
                    self.bomb_tutorial_done = True

     def _handle_spawns_multiplayer(self, player, object_spawners, spawn_postitions):
          """Handle spawning mechanics for multiplayer scenario"""
          print("Multiplayer: Creating a thread for:", player)
          while self.stop_threads == False:
               time.sleep(4)

               random_spawn = spawn_postitions[random.randint(0,len(spawn_postitions)-1)]
               options = [0,1,2]
               weights = [60, 60, 5] 
               
               if(player.score <= 250):
                    random_object = random.choices(options, weights)[0]
                    object_spawners[random_object].spawn_object(self.space, self.collision_types["objects_player_" + str(player.collision_type)], position = random_spawn)

               else:
                    max_objects = 4
                    scaling_factor = min(player.score // 150, max_objects)
                    for _ in range(scaling_factor):
                         random_object = random.choices(options, weights)[0]
                         object_spawners[random_object].spawn_object(
                              self.space,
                              self.collision_types["objects_player_" + str(player.collision_type)],
                              position=random_spawn
                         )
                         random_spawn = spawn_postitions[random.randint(0,len(spawn_postitions)-1)]
                         time.sleep(.8)

     def _cleanup_object_spawners(self, object_spawners):
          # Cleanup an object spawner for a given player's list  of object_spawners
          for object_spawner in object_spawners:
               for shape in object_spawner.pymunk_objects_to_draw:
                    object_spawner.pymunk_objects_to_draw.remove(shape)
     def handle_collision(self, arbiter, space, data):
          # Get objects that were involved in collision
          #print("__________________ COLISION __________________")
          kinematic_shape = arbiter.shapes[0]
          shape_trail_length = data["player"].get_trailing_length_by_limb(kinematic_shape.player_limb)
          # The shape attached to the player's limb has most accurate contact point. 
          contact_point = kinematic_shape.get_vertices()[1]
          shape = next((obj for obj in arbiter.shapes if obj.body.body_type != pymunk.Body.KINEMATIC), None)
          
          # Check if you did an actual movement and not just small shifts
          if(shape_trail_length > 8 and shape.parent_object.collision_requirements_are_met(data["player"], kinematic_shape)): 
               try:
                    # Shape's unique aftermath (breaks, splits, explodes, etc.)
                    shape.parent_object.collision_aftermath(space, shape, contact_point)
               except RuntimeError as error: # Catch specific error that occurs when two limbs collide on an object at the same time
                    print(str(error))
                    return True
               if isinstance(shape.parent_object,CVNinjaBomb):
                    data["player"].strikes +=1
                    return True
               # Double points if player used a leg
               gets_double_points = (kinematic_shape.player_limb == "left leg" or kinematic_shape.player_limb == "right leg")
               data["player"].score += shape.parent_object.calculate_score(shape, gets_double_points)
          #else:
               #print("Trail: ",shape_trail_length )
          return True
     def _handle_menu(self, arbiter, space, data):
          shape = next((obj for obj in arbiter.shapes if obj.body.body_type != pymunk.Body.KINEMATIC), None)
          kinematic_shape = arbiter.shapes[0]
          shape_trail_length = data["player"].get_trailing_length_by_limb(kinematic_shape.player_limb)
          if(shape_trail_length > 10): 
               shape.parent_object.collision_aftermath(space, shape)
               self.should_switch = True
               if(shape.collision_type == self.collision_types["menu_option_play_again"]):
                    self.options_next_game["NUMBER_OF_PLAYERS"] = self.options["NUMBER_OF_PLAYERS"]
                    self.next_game = "CVNinja"
               elif(shape.collision_type == self.collision_types["menu_option_main_menu"]):
                    self.next_game = "Main Menu"
          return True
     def out_of_bounds(self, arbiter, space, data):
          print("__________________ OUT OF BOUNDS __________________")
          shape = arbiter.shapes[0]
          space.remove(shape, shape.body)
          try:
               shape.parent_object.pymunk_objects_to_draw.remove(shape) # maybe method with some logic behind it. 
               if(shape.collision_type == self.collision_types["objects_player_1"] and not isinstance(shape.parent_object,CVNinjaBomb)):
                    data["player"].strikes += 1
                    playsound(CVAssets.AUDIO_STRIKE, block=False)
          except:
               print("Object was not in the list to remove")
          
          #print("Current objects on screen: ", len(self.cvninja_object_spawners["Player-1"][0].pymunk_objects_to_draw) )
          #print("Shape ",arbiter.shapes[0] ," has left the screen!")
          
          return True