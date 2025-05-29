import asyncio
from fastapi import APIRouter, HTTPException
from app.schemas import game_schema
from app.services.multigame_service import multi_game_service
from app.utils.multi_connection_manager import multi_manager  
from typing import Optional

router = APIRouter()

@router.post("/games/{game_id}/move", response_model=game_schema.GameState)
async def make_move(game_id: int, move: game_schema.Move, player_id: int):
    """
    Effectue un coup (déplacement ou pose de mur) pour la partie `game_id`.
    """
    try:
        game = multi_game_service.get_game(game_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if game.game_over:
        raise HTTPException(status_code=400, detail="La partie est terminée.")
    if game.current_turn != player_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre tour")

    # Appliquer le coup
    try:
        if move.move_type == "move" and move.new_position:
            game.move_pawn(player_id, move.new_position.dict())
        elif move.move_type == "wall" and move.wall:
            game.place_wall(player_id, move.wall.dict())
        else:
            raise HTTPException(status_code=400, detail="Données de coup invalides")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_state = game.get_game_state()

    # Diffusion en temps réel : j'envoie l'état du jeu à tous les WS connectés pour ce game_id
    await multi_manager.broadcast(game_id, new_state.json())

    # Vérifier si le coup a terminé la partie
    if game.game_over:
        # Supprimer immédiatement la partie afin d'empêcher tout autre coup 
        multi_game_service.remove_game(game_id)
        final_state = new_state.dict()
        final_state["message"] = f"Le joueur {game.winner_id} a gagné. La partie est terminée."
        return final_state

    return new_state
