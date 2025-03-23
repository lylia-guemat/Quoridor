from app.models.game import QuoridorGame

class QuoridorService:
    def __init__(self):
        self.game = QuoridorGame()

    def get_game_state(self):
        return self.game.get_game_state()

    def move_pawn(self, player_id: int, new_position: dict):
        self.game.move_pawn(player_id, new_position)

    def place_wall(self, player_id: int, wall_data: dict):
        self.game.place_wall(player_id, wall_data)

    def ai_move(self):
        self.game.ai_move()

# Création d'une instance unique du service à utiliser dans le contrôleur
game_service = QuoridorService()
