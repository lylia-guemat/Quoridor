from fastapi import FastAPI
from app.controllers import game_controller

app = FastAPI(title="Quoridor Game API")

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Quoridor. Pour la documentation, accédez à /docs"}

app.include_router(game_controller.router, prefix="/api")

# Pour lancer le serveur, exécutez par exemple :
# uvicorn app.main:app --reload
