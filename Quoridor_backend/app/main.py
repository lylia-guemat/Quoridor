import sys
import pathlib
import logging


from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.controllers.game_controller import get_game_state
from fastapi import HTTPException

from pydantic import BaseModel
from typing import List


from pydantic import BaseModel
from typing import List
from fastapi import HTTPException
from app.services.quoridor_service import game_service

from app.controllers import (
    game_controller,
    websocket_controller
)

# ─── Configuration de base du logging ────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("quoridor")

# ─── Instance FastAPI ───────────────────────────────────────────────────────
app = FastAPI(title="Quoridor Game")

# ── Calcul du chemin absolu du projet et pointage vers le front ────────────
ROOT = pathlib.Path(__file__).parent.parent.parent  # remonte jusqu'à Quoridor/
FRONT = ROOT / "Quoridor_front"

# ─── Route pour l'API racine ────────────────────────────────────────────────
@app.get("/api")
def read_root():
    return {"message": "Bienvenue sur l'API Quoridor. Pour la documentation, accédez à /docs"}

# ─── Configurer les fichiers statiques ──────────────────────────────────────
app.mount(
    "/static",
    StaticFiles(directory=FRONT / "static"),
    name="static",
)

# ─── Configurer les templates ───────────────────────────────────────────────
templates = Jinja2Templates(directory=str(FRONT / "templates"))

# ─── Route pour servir le front principal ──────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ─── Routes pour les pages HTML additionnelles ─────────────────────────────
@app.get("/play", response_class=HTMLResponse)
async def read_play(request: Request):
    return templates.TemplateResponse("play.html", {"request": request})

# ─── Route pour le choix de difficulté IA ───────────────────────────────────
@app.get("/ai-difficulty", response_class=HTMLResponse)
async def read_ai_difficulty(request: Request):
    return templates.TemplateResponse("ai-difficulty.html", {"request": request})

@app.get("/game/ai", response_class=HTMLResponse)
async def read_game_ai(request: Request,
                       difficulty: str = Query(..., regex="^(easy|medium|hard)$")):
    """
    Lance une partie Humain vs IA (2 joueurs) au niveau de difficulté choisi.
    """
    return templates.TemplateResponse(
        "game_2players.html",
        {
            "request": request,
            "isVsAI": True,
            "aiDifficulty": difficulty,
            "mode": "2players"
        }
    )

@app.get("/game/{mode}", response_class=HTMLResponse)
async def read_game(request: Request, mode: str):
    if mode == "2players":
        return templates.TemplateResponse("game_2players.html", {"request": request})
    elif mode == "4players":
        return templates.TemplateResponse("game_4players.html", {"request": request})
    elif mode == "ai":
        return templates.TemplateResponse("ai-difficulty.html", {"request": request})
    else:
        return templates.TemplateResponse("404.html", {"request": request})  # ou une redirection
    
    

class PlayerIDRequest(BaseModel):
    player_id: int

class Move(BaseModel):
    x: int
    y: int

from fastapi import FastAPI, HTTPException
from typing import List
from app.schemas.game_schema import Position, GameState, Player
from app.services.quoridor_service import game_service
from pydantic import BaseModel

class PlayerIDRequest(BaseModel):
    player_id: int

class Move(BaseModel):
    x: int
    y: int

from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel

# N’importe quelle importation de QuoridorGame n’est plus nécessaire ici
from app.services.quoridor_service import game_service
from app.schemas.game_schema import Position, GameState, Player

class PlayerIDRequest(BaseModel):
    player_id: int

class Move(BaseModel):
    x: int
    y: int

@app.post("/api/showValidMoves", response_model=List[Move])
def show_valid_moves(request_data: PlayerIDRequest):
    # 1) Récupère l’instance de jeu depuis le service
    game = game_service.game

    # 2) Transforme au besoin en GameState Pydantic
    #    Si game.get_game_state() renvoie déjà un GameState, inutile de reconstruire
    game_state: GameState = game.get_game_state()

    # 3) Récupère le joueur
    player = next((p for p in game_state.players if p.id == request_data.player_id), None)
    if not player:
        raise HTTPException(status_code=404, detail="Joueur introuvable")

    # 4) Calcule les mouvements valides
    valid_positions: List[Position] = game.get_valid_pawn_moves(player, game_state)

    # 5) Retourne les coordonnées
    return [{"x": pos.x, "y": pos.y} for pos in valid_positions]




@app.get("/rules", response_class=HTMLResponse)
async def read_rules(request: Request):
    return templates.TemplateResponse("rules.html", {"request": request})

# ─── Routes pour le mode de jeu ──────────────────────────────────────
app.include_router(game_controller.router, prefix="/api")
app.include_router(websocket_controller.router)



# ─── Démarrage de l'application ────────────────────────────────────────────
logger.info("Application Quoridor démarrée")


#python -m uvicorn app.main:app --reload
