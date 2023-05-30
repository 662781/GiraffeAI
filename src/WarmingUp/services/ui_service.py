import cv2
class UIService:
    frame = None

    def __init__(self, frame) -> None:
        self.frame = frame
    
    def put_score(self, players: list, xy: tuple):
        if (players is not None):
            for i, player in enumerate(players):
                cv2.putText(self.frame, "Score Player{}: {}".format(i+1, player.score), xy, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    def put_mode(self, mode: int, xy: tuple):
        if mode == 1:
            cv2.putText(self.frame, "Snapshot Mode", xy, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    def show_pause_menu():
        print("Game Paused: Not enough players detected!")