from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.connection_manager import manager


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # recevoir des messages du client si besoin, ici je les ignore
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
