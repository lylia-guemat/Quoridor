
import sys
from fastapi import FastAPI
import logging
from app.controllers import game_controller, websocket_controller
from app.controllers import multigame_controller, multigame_moves_controller, multigame_websocket_controller

# Configuration de base du logging
logging.basicConfig(
    level=logging.INFO,  # Niveau minimal (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Affiche dans la console
        # apre je vais voir si j'ajoute un FileHandler pour écrire dans un fichier logging.FileHandler("quoridor.log") 
    ]
)

logger = logging.getLogger("quoridor")


app = FastAPI(title="Quoridor Game")

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Quoridor. Pour la documentation, accédez à /docs"}

#app.include_router(game_controller.router, prefix="/api")
#app.include_router(websocket_controller.router)  # Accessible via /ws


#Nouveaux routeur : 
# création et récupération de parties
app.include_router(multigame_controller.router, prefix="/api")

# endpoint pour jouer un coup dans une partie
app.include_router(multigame_moves_controller.router, prefix="/api")

# WebSocket pour chaque partie
app.include_router(multigame_websocket_controller.router)

# démarrage de l'application
logger.info("Application Quoridor démarrée")


# Pour lancer le serveur, exécutez par exemple :
# python -m uvicorn app.main:app --reload
