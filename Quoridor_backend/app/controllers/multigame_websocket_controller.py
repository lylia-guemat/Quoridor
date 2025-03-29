from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.services.multigame_service import multi_game_service
from app.utils.multi_connection_manager import multi_manager

router = APIRouter()

@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: int):
    # Vérifier que la partie existe
    try:
        multi_game_service.get_game(game_id)
    except ValueError as e:
        # Si la partie n'existe pas, on refuse la connexion
        await websocket.close(code=1003)
        return

    await multi_manager.connect(game_id, websocket)
    try:
        while True:
            
            await websocket.receive_text()
    except WebSocketDisconnect:
        multi_manager.disconnect(game_id, websocket)

