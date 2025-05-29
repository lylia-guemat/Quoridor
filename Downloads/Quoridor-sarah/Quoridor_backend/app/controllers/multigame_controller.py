from fastapi import APIRouter, HTTPException
from app.services.multigame_service import multi_game_service

router = APIRouter()

@router.post("/games")
def create_new_game(num_players: int = 2):
    """
    Crée une nouvelle partie et retourne son identifiant.
    Par défaut, 2 joueurs. On peut passer num_players=4 pour 4 joueurs.
    """
    if num_players not in [2, 4]:
        raise HTTPException(status_code=400, detail="Le nombre de joueurs doit être 2 ou 4.")
    game_id = multi_game_service.create_game(num_players)
    return {"game_id": game_id}


@router.get("/games/{game_id}")
def get_game_state(game_id: int):
    """
    Récupère l'état de la partie correspondant à game_id.
    """
    try:
        game = multi_game_service.get_game(game_id)
        return game.get_game_state()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
