from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
from typing import Dict, List

class MultiConnectionManager:
    def __init__(self):
        # Dictionnaire : game_id -> liste de WebSocket
        self.active_connections: Dict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, game_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[game_id].append(websocket)

    def disconnect(self, game_id: int, websocket: WebSocket):
        if websocket in self.active_connections[game_id]:
            self.active_connections[game_id].remove(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]  # optionnel, si on veut nettoyer

    async def broadcast(self, game_id: int, message: str):
        if game_id not in self.active_connections:
            return
        for connection in self.active_connections[game_id]:
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(game_id, connection)

multi_manager = MultiConnectionManager()
