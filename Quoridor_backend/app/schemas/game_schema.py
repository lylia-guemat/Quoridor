from pydantic import BaseModel
from typing import List, Optional

class Position(BaseModel):
    x: int  
    y: int

class Wall(BaseModel):
    position: Position
    orientation: str  # "horizontal" ou "vertical"

class Player(BaseModel):
    id: int
    pawn: Position
    remaining_walls: int

class GameState(BaseModel):
    board: List[List[str]]
    players: List[Player]
    walls: List[Wall]
    current_turn: int

class Move(BaseModel):
    move_type: str  # "move" ou "wall"
    new_position: Optional[Position] = None  # Pour un déplacement de pion
    wall: Optional[Wall] = None              # Pour la pose d'un mur
