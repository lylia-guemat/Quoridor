import sys
import pathlib
import logging

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.controllers.game_controller import get_game_state

from app.controllers import (
    game_controller,
    websocket_controller,
    multigame_controller,
    multigame_moves_controller,
    multigame_websocket_controller,
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


@app.get("/game/{mode}", response_class=HTMLResponse)
async def read_game(request: Request, mode: str):
    if mode == "2players":
        return templates.TemplateResponse("game_2players.html", {"request": request})
    elif mode == "4players":
        return templates.TemplateResponse("game_4players.html", {"request": request})
    else:
        return templates.TemplateResponse("404.html", {"request": request})  # ou une redirection

@app.get("/rules", response_class=HTMLResponse)
async def read_rules(request: Request):
    return templates.TemplateResponse("rules.html", {"request": request})

# ─── Routes pour l'ancien mode de jeu ──────────────────────────────────────
app.include_router(game_controller.router, prefix="/api")
app.include_router(websocket_controller.router)

# ─── Routes pour le mode multijoueur ───────────────────────────────────────
app.include_router(multigame_controller.router, prefix="/api")
app.include_router(multigame_moves_controller.router, prefix="/api")
app.include_router(multigame_websocket_controller.router)

# ─── Démarrage de l'application ────────────────────────────────────────────
logger.info("Application Quoridor démarrée")
