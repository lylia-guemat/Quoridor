
# app/services/quoridor_service.py
from app.models.game import QuoridorGame

class QuoridorService:
    def __init__(self, num_players: int = 2, walls_per_player: int = 10):
        # Initialise une partie avec le nombre de joueurs et murs spécifié
        self.num_players = num_players
        self.walls_per_player = walls_per_player
        self.game = QuoridorGame(num_players=num_players, walls_per_player=walls_per_player)

    def get_game_state(self):
        return self.game.get_game_state()

    def move_pawn(self, player_id: int, new_position: dict):
        self.game.move_pawn(player_id, new_position)

    def place_wall(self, player_id: int, wall_data: dict):
        self.game.place_wall(player_id, wall_data)

    def restart(self, num_players: int = None, walls_per_player: int = None):
        # Permet de réinitialiser la partie avec de nouveaux paramètres si fournis
        if num_players is not None:
            self.num_players = num_players
        if walls_per_player is not None:
            self.walls_per_player = walls_per_player
        # Recréer l'objet QuoridorGame avec la configuration
        self.game = QuoridorGame(num_players=self.num_players, walls_per_player=self.walls_per_player)

    def ai_move(self, difficulty: str = "easy"):
        self.game.ai_move(difficulty=difficulty)


# Création d'une instance unique du service à utiliser dans le contrôleur
# Par défaut, 2 joueurs et 10 murs chacun
game_service = QuoridorService()

