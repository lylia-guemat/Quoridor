from fastapi import APIRouter, HTTPException
from app.schemas import game_schema
from app.services.quoridor_service import game_service

router = APIRouter()

@router.get("/game", response_model=game_schema.GameState)
def get_game_state():
    return game_service.get_game_state()

@router.post("/move", response_model=game_schema.GameState)
def make_move(move: game_schema.Move, player_id: int):
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
    return game_service.get_game_state()

@router.post("/ai_move", response_model=game_schema.GameState)
def ai_move():
    try:
        game_service.ai_move()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return game_service.get_game_state()
