import sys
from fastapi import FastAPI
import logging
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from fastapi import Request
from app.controllers import game_controller, websocket_controller


# Configuration de base du logging
logging.basicConfig(
    level=logging.INFO,  # Niveau minimal (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Affiche dans la console
        # Après, tu peux ajouter un FileHandler pour écrire dans un fichier : logging.FileHandler("quoridor.log") 
    ]
)

logger = logging.getLogger("quoridor")


app = FastAPI(title="Quoridor Game API")

# Route pour l'API
@app.get("/api")
def read_root():
    return {"message": "Bienvenue sur l'API Quoridor. Pour la documentation, accédez à /docs"}

# Configurer les fichiers statiques
app.mount("/static", StaticFiles(directory="Quoridor_front/static"), name="static")

# Configurer les templates
templates = Jinja2Templates(directory="Quoridor_front/templates")

# Route pour servir le front
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#-------------------

# Inclure les routes pour le jeu et le websocket
app.include_router(game_controller.router, prefix="/api")
app.include_router(websocket_controller.router)  # Accessible via /ws

# Démarrage de l'application
logger.info("Application Quoridor démarrée")

# Pour lancer le serveur, exécutez par exemple :
# python uvicorn app.main:app --reload
