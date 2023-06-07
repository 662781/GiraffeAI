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
from preferredsoundplayer import playsound
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
          self.spawn_postitions_singleplayer=  [(-70, 50),(-70, 40),(-70, 30),# left corner
                                   (710, 50), (710, 40), (710, 30), # right corner
                                   (100,-50), (300,-50), (400,-50), (490,-50)] # middle top

          self.spawn_postitions_multiplayer = [
                                             [(-70, 50),(-70, 30),(100,-50), (200,-50)],
                                             [(710, 50),(710, 30),(400,-50), (500,-50)]
                                             ]

     def setup(self, options):
          time.sleep(3)
          self.options = options
          self.NUMBER_OF_PLAYERS = self.options["NUMBER_OF_PLAYERS"]
          self.CAMERA_WIDTH = self.options["CAMERA_WIDTH"]
          self.CAMERA_HEIGHT = self.options["CAMERA_HEIGHT"]
          self.background = cv2.resize(self.background, (self.CAMERA_WIDTH, self.CAMERA_HEIGHT))
          self.region_width = self.CAMERA_WIDTH // self.NUMBER_OF_PLAYERS
          self.object_spawner_rotation = []
          self.cvninja_object_spawners ={} # Each player gets a list of object spawners assigned to them 
          self.game_duration = 90 # Seconds of play time for multiplayer 
          self.menu_options = [MainMenuObject(self.image_play_again, 100), MainMenuObject(self.image_main_menu, 100)]

          self.players = []
          self.bomb_tutorial_done = False # singleplayer only 
          self.stop_threads = False
          self.state_end_game = False
          for i in range(self.NUMBER_OF_PLAYERS):
               self.object_spawner_rotation.append([CVNinjaRock(self.rock, 80), CVNinjaPlank(self.plank, 70), CVNinjaMicha(self.micha, 160)])
          if(self.NUMBER_OF_PLAYERS == 1):
               for rotation in self.object_spawner_rotation: # Add bomb to the rotation
                    rotation.insert(0, CVNinjaBomb(self.bomb, 100))

          self._setup_space()
          self._create_players()
          self._startup_object_spawners()
          self.start_time = time.time()

     def _startup_object_spawners(self):
          threads = []
          if(self.NUMBER_OF_PLAYERS == 1):
               threads.append(threading.Thread(
                                   target=lambda: self._handle_spawns_singleplayer(
                                             self.players[0],
                                             self.cvninja_object_spawners["Player-1"], 
                                             self.spawn_postitions_singleplayer
                                             )
                                        )
                                   )
          else:
               # use i=i in lambda so the index is taken by value instead of reference
               for i in range(self.NUMBER_OF_PLAYERS):
                    threads.append(threading.Thread(
                                        target=lambda i=i: self._handle_spawns_multiplayer(
                                             self.players[i],
                                             self.cvninja_object_spawners["Player-" + str(i+1)], 
                                             self.spawn_postitions_multiplayer[i]
                                             )
                                        )
                                   )
          
          for thread in threads:
               print("spawning Thread")
               thread.start()

     def _setup_space(self):
          self.space = pymunk.Space()
          self.space.gravity = (0, 980)
          # Real boundaries of the space are a bit bigger than 480p, for illusion of objects appearing in and vanishing from the screen. 
          left_segment = pymunk.Segment(self.space.static_body, (-200, 0), (-200, 800), 100)
          right_segment = pymunk.Segment(self.space.static_body, (840, 0), (840, 800), 100)
          bottom_segment = pymunk.Segment(self.space.static_body, (-200, 800), (840, 800), 100)
          bottom_segment.collision_type = 99 
          bottom_segment.sensor = True
          top_segment = pymunk.Segment(self.space.static_body, (-200, -100), (840, -100), 100)
          self.space.add(left_segment, right_segment, top_segment, bottom_segment)

     def _create_players(self):
          for i in range(self.NUMBER_OF_PLAYERS):
               player_index = str(i+1)
               player = CVNinjaPlayer(self.collision_types["limbs_player_" + player_index])
               print("Creating Player " + player_index, " ", player)
               self.cvninja_object_spawners["Player-" + player_index] =  self.object_spawner_rotation[i]
               self.space.add(player.line_left_hand_body, player.line_left_hand_shape)
               self.space.add(player.line_right_hand_body, player.line_right_hand_shape)
               self.space.add(player.line_left_leg_body, player.line_left_leg_shape)
               self.space.add(player.line_right_leg_body, player.line_right_leg_shape)
               self.players.append(player)
               
               print("Giving thread player: ", player, " and index: ", player_index)
               self._create_event_handlers_for_player(player_index, player)
          
     def _create_event_handlers_for_player(self,player_index, player):
          """Creates collision and out of bounds handlers for a specific player number"""
          handlers_collision = [] 
          handlers_out_of_bounds = [self.space.add_collision_handler(self.collision_types["broken_objects"],self.collision_types["void"])]
          handlers_out_of_bounds[-1].separate = self.out_of_bounds

          handlers_collision.append(self.space.add_collision_handler(self.collision_types["limbs_player_" + player_index], self.collision_types["objects_player_" + player_index]))
          handlers_collision[-1].data["player"] = player
          handlers_collision[-1].begin = self._handle_collision

          handlers_collision.append(self.space.add_collision_handler(self.collision_types["objects_player_" + player_index],self.collision_types["void"]))
          handlers_collision[-1].data["player"] = player
          handlers_collision[-1].separate = self.out_of_bounds

          # Aftergame menus
          handlers_collision.append(self.space.add_collision_handler(self.collision_types["limbs_player_" + player_index], self.collision_types["menu_option_main_menu"]))
          handlers_collision[-1].data["player"] = player # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
          handlers_collision[-1].begin = self._handle_menu

          handlers_collision.append(self.space.add_collision_handler(self.collision_types["limbs_player_" + player_index], self.collision_types["menu_option_play_again"]))
          handlers_collision[-1].data["player"] = player # Collision needs the player to determine extra conditions (long enough slice, used 2 hands, etc.)
          handlers_collision[-1].begin = self._handle_menu

     def cleanup(self):
          # todo: change into dynamic
          self.stop_threads = True
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

          result = self.yolo_model(image, max_det=self.NUMBER_OF_PLAYERS, verbose=False)[0]
          image.flags.writeable = True  
          try:
               self.space.step(1/60)
          except Exception:
               print("Error stepping into space")
               traceback.print_exc()
          image = Generics.overlayPNG(image, self.background, pos=[0, 0])
          self._update_players(image, result)
          image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
          cv2.putText(image, "FPS:" + str(display_fps), (460, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 

               #cv2.putText(image, "Time left:" + str(remaining_seconds), (400, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA) 
          for i, player in enumerate(self.players):
               image = self._draw_player_stats(image,player, x = 10 + (i * (self.CAMERA_WIDTH / 2)))
               x = self.region_width * (i+1) 
               cv2.line(image, (x, 0), (x, self.CAMERA_HEIGHT), (255, 255, 255), 4) 
          
          if (self.NUMBER_OF_PLAYERS > 1):     
               remaining_seconds = int(self.game_duration - (time.time() - self.start_time))
               image = Generics.put_text_with_ninja_font(image, "     Time\nRemaining\n       " + str(0 if remaining_seconds < 0 else remaining_seconds), (260,45),
                                   size_class = "Small",
                                   font_color = (0,0,200),
                                   outline_color = (255,255,255),
                                   outline_width=2)
               
          for player_index in range(len(self.cvninja_object_spawners)):
               for object_spawner in self.cvninja_object_spawners["Player-" + str(player_index+1)]:
                    for shape in object_spawner.pymunk_objects_to_draw:
                         image = Generics.draw_pymunk_object_in_opencv(image, shape)
          if(self._is_game_over()):
               image = self._draw_final_screen(image)
               self.stop_threads = True
               self._cleanup_object_spawners()
               for menu_item in self.menu_options:
                    for shape in menu_item.pymunk_objects_to_draw:
                         image = Generics.draw_pymunk_object_in_opencv(image, shape)

          if cv2.waitKey(1) & 0xFF == ord('q'):
               self.should_switch = True
               self.next_game = "Main Menu"
          return image

     def _is_game_over(self):
          """Depending on the amount of players, a different 'game over' condition needs to be met"""
          if(self.NUMBER_OF_PLAYERS == 1):
               return self.players[0].strikes >= 3
          else:
               return time.time() - self.start_time >= self.game_duration

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

     def _update_players(self, image, result):
          """Update and draw each player marked by the YOLO results"""
          try:
               for i in range(self.NUMBER_OF_PLAYERS):
                    keypoints = result.keypoints[i].cpu().numpy()
                    # Depending on the position in the results, we assign the results to update for a specific player
                    player_index = int(keypoints[2][0]) > (self.CAMERA_WIDTH / self.NUMBER_OF_PLAYERS) # returns boolean 1 or 0 we can use for index
                    self.players[player_index].update_tracking(keypoints)
                    Generics.get_player_trailing(self.players[player_index], image)
                    Generics.draw_stick_figure(image, keypoints)
                    self.players[player_index].reset_keypoints()
          except IndexError:
               pass
          except Exception:
               traceback.print_exc()
               pass
        
     def _draw_player_stats(self, image, player, x):
          """Draw current stats of a player based on gamemode"""
          y = 35
          black = (0,0,0)
          white = (255,255,255)
          red = (0, 0,255)
          image = Generics.put_text_with_ninja_font(image, "Score: " + str(player.score), (x,10),
                                                  size_class = "Small",
                                                  font_color = black,
                                                  outline_color = white,
                                                  outline_width=2)
          if(self.NUMBER_OF_PLAYERS == 1):
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
          self.position_play_again = (100,80) if self.NUMBER_OF_PLAYERS == 1 else (self.region_width-50 ,140)
          self.position_main_menu = (400,80) if self.NUMBER_OF_PLAYERS == 1 else (self.region_width-50 ,260)
          # Spawn menu options once
          if(not self.state_end_game):
               if(self.NUMBER_OF_PLAYERS > 1):
                    sorted_players = sorted(self.players, key=lambda player: player.score, reverse=True)
                    for i,player in enumerate(sorted_players):
                         player
                    if(sorted_players[0].score == sorted_players[1].score):
                         sorted_players[0].status ="winner"
                         sorted_players[1].status ="winner"
                    else:
                         sorted_players[0].status ="winner"
                         sorted_players[1].status ="loser"

               # for shape in self.space.shapes:
               #      if(shape.body.body_type != pymunk.Body.KINEMATIC):
               #           self.space.remove(shape)
               self.space.gravity = (0,0)
               self.menu_options[0].spawn_object(self.space, self.collision_types["menu_option_play_again"], position = self.position_play_again)
               self.menu_options[1].spawn_object(self.space, self.collision_types["menu_option_main_menu"], position = self.position_main_menu )
               self.state_end_game = True

          if(self.NUMBER_OF_PLAYERS > 1):
               for i, player in enumerate(self.players):
                    x = 130 + (i * (self.CAMERA_WIDTH // 2))
                    status = player.status
                    if(status == "winner" or status == "tie"):
                         image = Generics.put_text_with_ninja_font(image, " 1ST\n" + str(player.score), (x,130),
                                                  size_class = "Medium",
                                                  font_color = (0,215,255),
                                                  outline_color = (255,255,255),
                                                  outline_width=2)
                         #cv2.putText(image, "1ST\n" + str(player.score), (x,130), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 215, 0), 2, cv2.LINE_AA) 
                    elif(status == "loser"):
                         image = Generics.put_text_with_ninja_font(image, " 2ND\n" + str(player.score), (x,130),
                                                  size_class = "Medium",
                                                  font_color = (192, 192, 192),
                                                  outline_color = (255,255,255),
                                                  outline_width=2)
                         #cv2.putText(image, "2ND\n" + str(player.score), (x,130), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (192, 192, 192), 2, cv2.LINE_AA) 
          return image

     def _handle_spawns_singleplayer(self, player, object_spawners, spawn_postitions):
          print("Creating a thread for:", player)
          time.sleep(5)
          while self.stop_threads == False:
               random_spawn = spawn_postitions[random.randint(0,len(spawn_postitions)-1)]
               options = [0,1,2,3]
               weights = [40, 60, 60, 1] 
               
               if(player.score <= 250):
                    one_time_weights = [0, 50, 50, 5] 
                    random_object = random.choices(options, one_time_weights)[0]
                    object_spawners[random_object].spawn_object(self.space, self.collision_types["objects_player_" + str(player.collision_type)], position = random_spawn)
                      
               elif(player.score > 250 and self.bomb_tutorial_done):
                    max_objects = 5
                    scaling_factor = min(player.score // 150, max_objects)
                    for _ in range(scaling_factor):
                         
                         random_object = random.choices(options, weights)[0]
                         try:
                              object_spawners[random_object].spawn_object(
                                   self.space,
                                   self.collision_types["objects_player_" + str(player.collision_type)],
                                   position=random_spawn
                              )
                         except:
                              pass
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
               time.sleep(3)

     def _handle_spawns_multiplayer(self, player, object_spawners, spawn_postitions):
          """Handle spawning mechanics for multiplayer scenario"""
          print("Multiplayer: Creating a thread for:", player)
          print("Useing object_spawners: ", object_spawners)
          time.sleep(5)
          while self.stop_threads == False:
               if self.stop_threads:
                   break
               random_spawn = spawn_postitions[random.randint(0,len(spawn_postitions)-1)]
               options = [0,1,2]
               weights = [60, 60, 5] 
               max_objects = 4
               #scaling_factor = min(player.score // 150, max_objects)
               for _ in range(max_objects):
                    random_object = random.choices(options, weights)[0]
                    try:
                         object_spawners[random_object].spawn_object(
                              self.space,
                              self.collision_types["objects_player_" + str(player.collision_type)],
                              position=random_spawn
                         )
                    except:
                         pass
                    random_spawn = spawn_postitions[random.randint(0,len(spawn_postitions)-1)]
                    time.sleep(1.5)
               time.sleep(2.5)


     def _cleanup_object_spawners(self):
          # Cleanup an object spawner for a given player's list  of object_spawners
          for _,object_spawners in self.cvninja_object_spawners.items():
               for object_spawner in object_spawners:
                    for shape in object_spawner.pymunk_objects_to_draw:
                         try:
                              object_spawner.pymunk_objects_to_draw.remove(shape)
                         except:
                              pass
     def _handle_collision(self, arbiter, space, data):
          """Handle collision occurences and aftermath"""
          # Get objects that were involved in collision
          kinematic_shape = arbiter.shapes[0]
          shape_trail_length = data["player"].get_trailing_length_by_limb(kinematic_shape.player_limb)
          # The shape attached to the player's limb has most accurate contact point. 
          contact_point = kinematic_shape.get_vertices()[1]
          shape = next((obj for obj in arbiter.shapes if obj.body.body_type != pymunk.Body.KINEMATIC), None)
          
          # Check if you did an actual movement and not just small shifts
          if(shape_trail_length > 10 // self.NUMBER_OF_PLAYERS and shape.parent_object.collision_requirements_are_met(data["player"], kinematic_shape)): 
               try:
                    # Shape's unique aftermath (breaks, splits, explodes, etc.)
                    shape.parent_object.collision_aftermath(space, shape, contact_point)
               except RuntimeError as error: # Catch specific error that occurs when two limbs collide on an object at the same time
                    print(str(error))
                    return True
               if isinstance(shape.parent_object,CVNinjaBomb):
                    # data["player"].score -= 300
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
          contact_point = kinematic_shape.get_vertices()[1]
          shape_trail_length = data["player"].get_trailing_length_by_limb(kinematic_shape.player_limb)
          if(shape_trail_length > 20 and shape.parent_object.collision_requirements_are_met(data["player"], kinematic_shape)): 
               try:
                    shape.parent_object.collision_aftermath(space, shape, contact_point)
               except RuntimeError as error: # Catch specific error that occurs when two limbs collide on an object at the same time
                    print(str(error))
               self.should_switch = True
               if(shape.collision_type == self.collision_types["menu_option_play_again"]):
                    self.options_next_game["NUMBER_OF_PLAYERS"] = self.NUMBER_OF_PLAYERS
                    self.next_game = "CVNinja"
               elif(shape.collision_type == self.collision_types["menu_option_main_menu"]):
                    self.next_game = "Main Menu"
          return True

     def out_of_bounds(self, arbiter, space, data):
          shape = arbiter.shapes[0]
          space.remove(shape, shape.body)
          try:
               shape.parent_object.pymunk_objects_to_draw.remove(shape) # maybe method with some logic behind it. 
               if(self.NUMBER_OF_PLAYERS ==1 ):
                    if(shape.collision_type == self.collision_types["objects_player_1"] and not isinstance(shape.parent_object,CVNinjaBomb)):
                         data["player"].strikes += 1
                         playsound(CVAssets.AUDIO_STRIKE, block=False)
          except:
               print("Object was not in the list to remove")
          return True