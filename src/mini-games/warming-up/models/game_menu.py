from services.game_menu_service import GameMenuService

class GameMenu:
    chosen_exercise = GameMenuService.get_exercise()
    
    def __init__(self) -> None:
        pass