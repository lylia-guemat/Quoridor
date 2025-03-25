import asyncio
from fastapi import APIRouter, HTTPException
from app.schemas import game_schema
from app.services.quoridor_service import game_service
from app.utils.connection_manager import manager


router = APIRouter()


@router.get("/game", response_model=game_schema.GameState)
def get_game_state():
    return game_service.get_game_state()


@router.post("/move", response_model=game_schema.GameState)
async def make_move(move: game_schema.Move, player_id: int):

    # Vérifier si la partie est déjà terminée
    if game_service.game.game_over:
        raise HTTPException(status_code=400, detail="La partie est terminée !")

    if game_service.game.current_turn != player_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre tour")
    
    try:
        if move.move_type == "move" and move.new_position:
            game_service.move_pawn(player_id, move.new_position.dict())
        elif move.move_type == "wall" and move.wall:
            game_service.place_wall(player_id, move.wall.dict())
        else:
            raise HTTPException(status_code=400, detail="Données de coup invalides")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    new_state = game_service.get_game_state()
    # Diffuser l'état du jeu mis à jour en JSON aux clients connectés via WebSocket
    asyncio.create_task(manager.broadcast(new_state.json()))

    return game_service.get_game_state()


@router.post("/ai_move", response_model=game_schema.GameState)
def ai_move():
    try:
        game_service.ai_move()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return game_service.get_game_state()
