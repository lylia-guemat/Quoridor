from typing import Dict
from app.models.game import QuoridorGame

class MultiGameService:
    def __init__(self):
        self.games: Dict[int, QuoridorGame] = {}
        self.next_game_id: int = 1

    #Crée une nouvelle partie et retourne son identifiant (game_id).
    def create_game(self, num_players: int = 2) -> int:
        game_id = self.next_game_id
        self.next_game_id += 1
        # Crée une instance de QuoridorGame (2 ou 4 joueurs)
        self.games[game_id] = QuoridorGame(num_players=num_players)
        return game_id

    #Retourne l'etat de la partie passée en argument 
    def get_game(self, game_id: int) -> QuoridorGame:
        if game_id not in self.games:
            raise ValueError(f"Partie {game_id} introuvable.")
        return self.games[game_id]


    # Supprime la partie (après la fin de partie).
    def remove_game(self, game_id: int):
        
        if game_id in self.games:
            del self.games[game_id]


# Une instance globale pour être utilisée par les endpoints
multi_game_service = MultiGameService()