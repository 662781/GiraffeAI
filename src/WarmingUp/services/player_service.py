from WarmingUp.model.player import Player
from WarmingUp.services.ui_service import UIService
from WarmingUp.services.keypoint_service import KeypointService
class PlayerService:
    players: list
    no_players_set: int
    no_players_detected: int

    def __init__(self, no_players_set: int) -> None:
        self.players = []
        self.no_players_set = no_players_set

    """
    Creates new Player object list, with a length of the no_players_set. This only happens if the set amount of players are detected
    """
    def create_players(self):                
        self.players = [Player()] * self.no_players_set
        return self.players

    """
    Adds the keypoints of each detected person to the Player objects in the list
    """
    def append_preprocessed_keypoints_to_players(self, keypoints: list):
        if (self.no_players_set == 1):
            self.players[0].keypoints = KeypointService.pre_process_keypoints(keypoints)       
        if (self.no_players_set > 1):
            for i, player in enumerate(keypoints):
                self.players[i].keypoints = KeypointService.pre_process_keypoints(player)

    """
    Returns a boolean; checks if the no_players_set is the same as the detected amount of players
    """
    def all_players_present(self) -> bool:
        return self.no_players_set == self.no_players_detected
    
    def clear_players(self):
        self.players.clear()