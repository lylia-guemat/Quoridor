import random
import logging
from collections import deque
# from Quoridor_backend.app.schemas.game_schema import Position, Wall, GameState, Player
from app.schemas.game_schema import Position, Wall, GameState, Player

import heapq  # Import the heapq module
from typing import List,Tuple,Optional
logger = logging.getLogger("quoridor")
import math
import copy
#python -m app.models.run_ais_timed

#fix print_board / has_path pour prendre en compte les saut et diag + compatibilité avec 4 joueurs / fix buggs de wall_block (en créant meth interne)
# On sort plus de la borne de la grille
class QuoridorGame:
    print("===> game.py correctement chargé")

    def __init__(self, num_players: int = 2, walls_per_player: int = None):
        """
        Initialise le plateau et les joueurs.
        :param num_players: 2 ou 4
        :param walls_per_player: nombre de murs par joueur (si None, utilise la valeur par défaut selon num_players)
        """
        self.board = [["" for _ in range(9)] for _ in range(9)]
        self.walls: List = []
        self.num_players = num_players
        self.game_over = False
        self.winner_id = None

        # Détermine le nombre de murs par joueur
        if walls_per_player is None:
            walls_per_player = 10 if num_players == 2 else 5

        # Initialisation des joueurs selon le nombre
        if num_players == 2:
            self.players = [
                Player(id=1, pawn=Position(x=4, y=0), remaining_walls=walls_per_player),
                Player(id=2, pawn=Position(x=4, y=8), remaining_walls=walls_per_player)
            ]
        elif num_players == 4:
            self.players = [
                Player(id=1, pawn=Position(x=4, y=0), remaining_walls=walls_per_player),
                Player(id=2, pawn=Position(x=4, y=8), remaining_walls=walls_per_player),
                Player(id=3, pawn=Position(x=0, y=4), remaining_walls=walls_per_player),
                Player(id=4, pawn=Position(x=8, y=4), remaining_walls=walls_per_player)
            ]
        else:
            raise ValueError("Le nombre de joueurs supporté est 2 ou 4 uniquement.")

        self.current_turn = 1

    def get_game_state(self) :

        return GameState(board=self.board,
                         players=self.players,
                         walls=self.walls,
                         current_turn=self.current_turn,
                         game_over=self.game_over,
                         winner_id=self.winner_id)

    def is_valid_move(self, player: Player, new_pos: Position) -> bool:
        # Vérification des bornes du plateau
        if not (0 <= new_pos.x < 9 and 0 <= new_pos.y < 9):
            return False

        from_x, from_y = player.pawn.x, player.pawn.y
        dx = abs(new_pos.x - from_x)
        dy = abs(new_pos.y - from_y)

        # Déplacement simple (une case orthogonale)
        if (dx + dy) == 1:

            # Vérifier que la case n'est pas occupée par un autre pion
            for p in self.players:
                if p.id != player.id and p.pawn.x == new_pos.x and p.pawn.y == new_pos.y:
                    return False

            # Vérifier qu'aucun mur ne bloque le déplacement
            if self.wall_blocks_move(player.pawn, new_pos):
                return False

            return True

        # Sinon, vérifier si c'est un déplacement face-à-face (saut direct ou diagonal)
        if self.is_valid_face_to_face_move(player, new_pos):
            return True

        return False
    def is_valid_face_to_face_move(self, player: Player, new_pos: Position) -> bool:
        # Vérifie si le déplacement est face à face avec un autre joueur
        opponent = self.get_opponent(player)
        if (new_pos.x, new_pos.y) == (opponent.pawn.x, opponent.pawn.y):
            # Tentative de saut par-dessus l'adversaire
            jump_x = opponent.pawn.x + (opponent.pawn.x - player.pawn.x)
            jump_y = opponent.pawn.y + (opponent.pawn.y - player.pawn.y)
            jump_pos = Position(x=jump_x, y=jump_y)

            # Vérifie si le saut direct est bloqué par un mur
            if self.wall_blocks_move(player.pawn, opponent.pawn) or self.wall_blocks_move(opponent.pawn, jump_pos):
                return False

            # Vérifie si le saut direct est valide
            if self.is_valid_move(player, jump_pos):
                return True

            # Vérifie les diagonales
            for dx, dy in [(-1, 1), (1, 1), (-1, -1), (1, -1)]:
                diag_x = opponent.pawn.x + dx
                diag_y = opponent.pawn.y + dy
                diag_pos = Position(x=diag_x, y=diag_y)

                # Vérifie si un mur bloque le saut diagonal
                if self.wall_blocks_move(opponent.pawn, diag_pos):
                    continue

                if self.is_valid_move(player, diag_pos):
                    return True

        return False

    def wall_blocks_move(self, from_pos: Position, to_pos: Position) -> bool:
        # Pour chaque mur, vérifier s'il bloque le déplacement entre les deux cases
        for wall in self.walls:
            if wall.orientation == "horizontal":
                # Un mur horizontal bloque un déplacement vertical s'il se trouve entre les deux cases [wall.x, wall.x+2]
                if from_pos.x == to_pos.x:
                    min_y = min(from_pos.y, to_pos.y)
                    if wall.position.y == min_y and wall.position.x <= from_pos.x < wall.position.x + 2:
                        return True
            elif wall.orientation == "vertical":
                # Un mur vertical bloque un déplacement horizontal s'il se trouve entre les deux cases [wall.y, wall.y+2]
                if from_pos.y == to_pos.y:
                    min_x = min(from_pos.x, to_pos.x)
                    if wall.position.x == min_x and wall.position.y <= from_pos.y < wall.position.y + 2:
                        return True
        return False

    def move_pawn(self, player_id: int, new_pos: dict) -> bool:
        logger.info(f"Déplacement demandé pour le joueur {player_id} vers {new_pos}")
        
        if self.game_over:
            raise Exception("La partie est terminée, aucun autre coup n'est accepté.")

        new_position = Position(**new_pos)
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            raise Exception("Joueur non trouvé")
        if not self.is_valid_move(player, new_position):
            raise Exception("Déplacement invalide")

        player.pawn = new_position

        if self.has_won(player):
            print(f"Le joueur {player.id} a gagné!")
            self.game_over = True
            self.winner_id = player.id
            return True  # signaler que la partie est finie

        self.switch_turn()
        return False  # partie continue


    # def move_pawn(self, player_id: int, new_pos: dict):
    #     logger.info(
    #         f"Déplacement demandé pour le joueur {player_id} vers {new_pos}")

    #     if self.game_over:
    #         raise Exception(
    #             "La partie est terminée, aucun autre coup n'est accepté.")

    #     # new_pos est un dictionnaire contenant x et y
    #     new_position = Position(**new_pos)
    #     player = next((p for p in self.players if p.id == player_id), None)
    #     if not player:
    #         raise Exception("Joueur non trouvé")
    #     if not self.is_valid_move(player, new_position):
    #         raise Exception("Déplacement invalide")

    #     # Déplacement du pion
    #     player.pawn = new_position

    #     # Vérifier la condition de victoire pour le joueur actuel
    #     if self.has_won(player):
    #         print(f"Le joueur {player.id} a gagné!")
    #         self.game_over = True
    #         self.winner_id = player.id
    #         return

    #     self.switch_turn()

    def has_won(self, player: Player) -> bool:
        """
        Détermine si le joueur a atteint le côté opposé.
        Pour 2 joueurs, le joueur 1 doit atteindre y=8 et le joueur 2 y=0.
        Pour 4 joueurs, on définit :
        - Joueur 1 (haut) : victoire si y == 8
        - Joueur 2 (bas)  : victoire si y == 0
        - Joueur 3 (gauche): victoire si x == 8
        - Joueur 4 (droite): victoire si x == 0
        """
        if self.num_players == 2:
            if player.id == 1 and player.pawn.y == 8:
                return True
            if player.id == 2 and player.pawn.y == 0:
                return True

        elif self.num_players == 4:
            if player.id == 1 and player.pawn.y == 8:
                return True
            if player.id == 2 and player.pawn.y == 0:
                return True
            if player.id == 3 and player.pawn.x == 8:
                return True
            if player.id == 4 and player.pawn.x == 0:
                return True
        return False
    
    def is_valid_wall_new(self, wall: Wall, walls: Optional[List[Wall]] = None) -> bool:
        walls = walls if walls is not None else self.walls

        if wall.orientation not in ["horizontal", "vertical"]:
            return False

        # Le mur de référence doit être dans les bornes de la grille 9x9
        if not (0 <= wall.position.x < 8 and 0 <= wall.position.y < 8):
            return False

        # Empêche les murs qui sortiraient de la grille
        if wall.orientation == "horizontal" and wall.position.x >= 8 - 1:
            return False
        if wall.orientation == "vertical" and wall.position.y >= 8 - 1:
            return False

        # Vérifier superposition exacte
        for w in walls:
            if wall.position == w.position and wall.orientation == w.orientation:
                return False

        # Vérifier croisement interdit (croix)
        for w in walls:
            if wall.orientation == "horizontal" and w.orientation == "vertical":
                if (w.position.x == wall.position.x or w.position.x == wall.position.x + 1) and \
                (w.position.y == wall.position.y or w.position.y == wall.position.y + 1):
                    return False
            if wall.orientation == "vertical" and w.orientation == "horizontal":
                if (w.position.y == wall.position.y or w.position.y == wall.position.y + 1) and \
                (w.position.x == wall.position.x or w.position.x == wall.position.x + 1):
                    return False

        return True


    def is_valid_wall_old(self, wall: Wall, walls: Optional[List[Wall]] = None) -> bool:
        # Utiliser self.walls par défaut si aucun mur simulé n’est passé
        walls = walls if walls is not None else self.walls

        if wall.orientation not in ["horizontal", "vertical"]:
            return False

        # Pour un mur, la position de référence doit être dans les bornes (entre 0 et 7)
        if not (0 <= wall.position.x < 8 and 0 <= wall.position.y < 8):
            return False

        # Ajout de conditions pour ne pas sortir de la grille
        # un mur horizontal couvre (x,y) et (x+1,y),
        # un mur vertical couvre (x,y) et (x,y+1)
        if wall.orientation == "horizontal" and wall.position.x >= 7:
            return False
        if wall.orientation == "vertical" and wall.position.y >= 7:
            return False

        # Empêcher le chevauchement de murs
        for w in walls:
            if w.orientation == wall.orientation:
                if wall.orientation == "horizontal":
                    # Un mur horizontal placé à (x, y) bloque les passages entre
                    # (x,y)<->(x,y+1) et (x+1,y)<->(x+1,y+1)
                    # Deux murs horizontaux sur la même ligne se chevauchent
                    # si la distance entre leurs positions x est <= 1.
                    # if w.position.y == wall.position.y and abs(w.position.x - wall.position.x) <= 1:
                    if w.position.y == wall.position.y and w.position.x == wall.position.x:
                        return False
                elif wall.orientation == "vertical":
                    # Un mur vertical placé à (x, y) bloque les passages entre
                    # (x,y)<->(x+1,y) et (x,y+1)<->(x+1,y+1)
                    # Deux murs verticaux sur la même colonne se chevauchent
                    # si la distance entre leurs positions y est <= 1.
                    # if w.position.x == wall.position.x and abs(w.position.y - wall.position.y) <= 1:
                    if w.position.x == wall.position.x and w.position.y == wall.position.y:
                        return False
            else:
                # ajouter une vérification pour empêcher l'intersection
                # (empêcher qu'un mur horizontal et un mur vertical se croisent
                # de manière à couvrir le même segment. les murs ne doivent pas
                # se chevaucher, même en travers.
                if wall.orientation == "horizontal" and w.orientation == "vertical":
                    # Cas 1
                    if wall.position.x == w.position.x and wall.position.y == w.position.y:
                        return False
                    # Cas 2 (attention à ne pas sortir de la grille)
                    if wall.position.x + 1 == w.position.x and wall.position.y - 1 == w.position.y and wall.position.y - 1 >= 0:
                        return False
                elif wall.orientation == "vertical" and w.orientation == "horizontal":
                    # Cas 3
                    if wall.position.x == w.position.x and wall.position.y == w.position.y:
                        return False
                    # Cas 4 (attention à ne pas sortir de la grille)
                    if wall.position.x - 1 == w.position.x and wall.position.y + 1 == w.position.y and wall.position.x - 1 >= 0:
                        return False

        return True

   
  
    def is_valid_wall(self, wall: Wall, walls: Optional[List[Wall]] = None) -> bool:
        walls = walls if walls is not None else self.walls
        # print(f"[DEBUG] Testing wall at {wall.position.x},{wall.position.y} orientation={wall.orientation} against {len(walls)} existing walls")

        if wall.orientation not in ["horizontal", "vertical"]:
            #print(f"[DEBUG] Invalid orientation: {wall.orientation}")
            return False

        # Bornes de la grille (0 <= x,y < 8)
        if not (0 <= wall.position.x < 8 and 0 <= wall.position.y < 8):
            #print(f"[DEBUG] Out of bounds: x={wall.position.x}, y={wall.position.y}")
            return False

        # Les checks de sortie de grille pour orientation ne sont plus nécessaires

        for w in walls:
            # --- Cas 1 : même orientation => chevauchement interdit
            if w.orientation == wall.orientation:
                if wall.orientation == "horizontal":
                    # Empêche tout chevauchement ou contiguïté horizontale
                    if w.position.y == wall.position.y and abs(w.position.x - wall.position.x) <= 1:
                        #print(f"[DEBUG] Overlap horizontal with existing at x={w.position.x}, y={w.position.y}")
                        return False
                elif wall.orientation == "vertical":
                    if w.position.x == wall.position.x and abs(w.position.y - wall.position.y) <= 1:
                        #print(f"[DEBUG] Overlap vertical with existing at x={w.position.x}, y={w.position.y}")
                        return False

            # --- Cas 2 : orientations différentes => croisement interdit
            else:
                # Croisement interdit: murs se croisent en T
                # Horizontal vs Vertical
                if wall.orientation == "horizontal" and w.orientation == "vertical":
                    # Interdiction si vertical commence dans l’intervalle du horizontal
                    if (wall.position.x <= w.position.x <= wall.position.x + 1 and
                        w.position.y == wall.position.y):
                        #print(f"[DEBUG] Crossing detected at {wall.position.x},{wall.position.y} with vertical {w.position.x},{w.position.y}")
                        return False

                elif wall.orientation == "vertical" and w.orientation == "horizontal":
                    if (wall.position.x == w.position.x and
                        wall.position.y <= w.position.y <= wall.position.y + 1):
                        #print(f"[DEBUG] Crossing detected at {wall.position.x},{wall.position.y} with horizontal {w.position.x},{w.position.y}")
                        return False

        #print(f"[DEBUG] Wall valid at {wall.position.x},{wall.position.y}")
        return True


    def place_wall(self, player_id: int, wall_data: dict):
        wall = Wall(**wall_data)
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            raise Exception("Joueur non trouvé")
        if player.remaining_walls <= 0:
            raise Exception("Plus de murs disponibles")
        
        # Utiliser self.walls explicitement comme contexte
        if not self.is_valid_wall(wall, walls=self.walls):
            raise Exception("Placement de mur invalide")

        # On pose le mur 
        self.walls.append(wall)
        player.remaining_walls -= 1

        # Vérifier que chaque joueur a toujours un chemin
        if not self.players_have_path():
            # Annuler la pose si cela bloque totalement un joueur
            self.walls.pop()
            player.remaining_walls += 1
            raise Exception("Le mur bloque complètement le chemin d'un joueur")

        self.switch_turn()

    

    def players_have_path(self) -> bool:
        """
        Vérifie que tous les joueurs ont un chemin vers leur ligne d'arrivée.
        """
        for p in self.players:
            if not self.has_path(p.pawn, p.id):
                return False
        return True



    # def has_path(self, start: Position, player_id: int) -> bool:
    #     """
    #     BFS (Breadth-First Search) pour vérifier qu'il existe un chemin depuis la position 'start'
    #     jusqu'à la ligne opposée (y=8 pour le joueur 1, y=0 pour le joueur 2, etc.)
    #     """
    #     goal_row = 8 if player_id == 1 else 0  
    #     visited = set()
    #     queue = deque()
    #     queue.append((start.x, start.y))
    #     visited.add((start.x, start.y))

    #     while queue:
    #         cx, cy = queue.popleft()
    #         # Condition de victoire : atteindre la ligne opposée
    #         if cy == goal_row:
    #             return True

    #         for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
    #             nx, ny = cx + dx, cy + dy
    #             if 0 <= nx < 9 and 0 <= ny < 9:
    #                 if (nx, ny) not in visited:
    #                     # Vérifier qu'aucun mur ne bloque le déplacement
    #                     if not self.wall_blocks_move(Position(x=cx, y=cy),
    #                                                  Position(x=nx, y=ny)):
    #                         visited.add((nx, ny))
    #                         queue.append((nx, ny))
    #     return False
    def has_path(self, start: Position, player_id: int, game_state: Optional[GameState] = None) -> bool:
        """
        Vérifie s’il existe un chemin légal (selon les règles Quoridor)
        pour le joueur d’id vers sa ligne d’arrivée.
        Version étendue pour supporter un GameState simulé.
        """
        # Créer un faux joueur avec juste la position
        player = Player(id=player_id, pawn=start, remaining_walls=0)
        game_state = game_state if game_state else self.get_game_state()

        visited = set()
        queue = deque()
        queue.append(start)
        visited.add((start.x, start.y))

        # Définir la condition de victoire
        if self.num_players == 2:
            goal_check = lambda pos: (pos.y == 8 if player_id == 1 else pos.y == 0)
        else:
            if player_id == 1:
                goal_check = lambda pos: pos.y == 8
            elif player_id == 2:
                goal_check = lambda pos: pos.y == 0
            elif player_id == 3:
                goal_check = lambda pos: pos.x == 8
            elif player_id == 4:
                goal_check = lambda pos: pos.x == 0

        while queue:
            current_pos = queue.popleft()
            if goal_check(current_pos):
                return True

            player.pawn = current_pos  # Mettre à jour la position courante

            # Obtenir tous les mouvements légaux selon les vraies règles
            for move in self.get_valid_pawn_moves(player, game_state):
                if (move.x, move.y) not in visited:
                    visited.add((move.x, move.y))
                    queue.append(move)

        return False


    def switch_turn(self):
        self.current_turn = (self.current_turn % self.num_players) + 1


    def ai_move(self, difficulty: str = "easy"):
        """
        Point d’entrée unique pour un coup IA.
        difficulty : "easy"|"medium"|"hard"
        """
        if self.game_over:
            return

        # Choix de la stratégie selon la difficulté
        if difficulty == "easy":
            # IA très simple, aléatoire
            self.ai_move_random(self.get_game_state())
        elif difficulty == "medium":
            # A* heuristique
            self.ai_move_a_star(self.get_game_state())
        elif difficulty == "hard":
            # Minimax alpha-beta (profondeur par ex. 2)
            self.ia_move_minmax_ab(depth=2)
        else:
            raise ValueError(f"Difficulté inconnue : {difficulty}")

        # après le coup IA, on passe au joueur suivant
        #if not self.game_over:
        #   self.switch_turn()
    

    def ai_move_a_star(self, game_state: GameState):
        if self.game_over:
            return  # Ne rien faire si la partie est déjà finie

        idx = self.current_turn - 1
        current_player = self.players[idx]
        opponent = self.players[1 - idx]

        best_move = None
        best_score = -math.inf

        # Évaluer les déplacements de pion
        move_score, best_position = self.evaluate_pawn_moves(current_player, game_state)
        if move_score > best_score:
            best_score = move_score
            best_move = ("move", best_position)

        # Évaluer les placements de mur si le joueur a encore des murs
        if current_player.remaining_walls > 0:
            wall_score, best_wall = self.evaluate_best_wall_placement(current_player, opponent, game_state)
            if wall_score > best_score:
                best_score = wall_score
                best_move = ("wall", best_wall)

        # Appliquer le meilleur coup
        if best_move:
            kind, obj = best_move
            if kind == "move":
                # Utiliser move_pawn pour déplacer et gérer la victoire
                finished = self.move_pawn(current_player.id, {"x": obj.x, "y": obj.y})
                if finished:
                    return  # Le joueur a gagné, fin du tour
            else:  # placement de mur
                self.place_wall(current_player.id, obj.dict())
        else:
            raise Exception("Aucun coup possible pour l’IA (move_a_star)")
    
    

        # #L’IA est très basique (choix aléatoire parmi les coups légaux), on va la modifier plus tard
    def ai_move_random(self, game_state: GameState):
        """
        Une IA simple qui effectue aléatoirement un coup légal.
        """
        current_player = next(
            (p for p in game_state.players if p.id == game_state.current_turn), None)
        opponent = next(
            (p for p in game_state.players if p.id != game_state.current_turn), None)
    
        legal_moves = []
    
        # Obtenir tous les déplacements valides pour le pion
        valid_pawn_moves = self.get_valid_pawn_moves(current_player, game_state)
        for move in valid_pawn_moves:
            legal_moves.append(("move", move))
    
        # Ajouter les placements de murs valides
        if current_player.remaining_walls > 0:
            for x in range(8):
                for y in range(8):
                    for orientation in ["horizontal", "vertical"]:
                        test_wall = Wall(position=Position(x=x, y=y), orientation=orientation)
                        if self.is_valid_wall(test_wall):
                            legal_moves.append(("wall", test_wall))
    
        # Si aucun coup légal n'est disponible, lever une exception
        if not legal_moves:
            raise Exception("Aucun coup légal trouvé pour l'IA")
    
        # Choisir un coup aléatoire parmi les coups légaux
        move_type, move_value = random.choice(legal_moves)
        if move_type == "move":
            if self.move_pawn(current_player.id, move_value.dict()):
                return # partie est finie 
        else:
            self.place_wall(current_player.id, move_value.dict())

    # def ai_move_random(self,gameState):

    #     # Une IA simple qui effectue aléatoirement un coup légal
    #     current_player = next(
    #         (p for p in gameState.players if p.id == gameState.current_turn), None)
    #     legal_moves = []
    #     directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    #     for dx, dy in directions:
    #         new_x = current_player.pawn.x + dx
    #         new_y = current_player.pawn.y + dy
    #         new_position = Position(x=new_x, y=new_y)
    #         if 0 <= new_x < 9 and 0 <= new_y < 9 and self.is_valid_move(
    #                 current_player, new_position):
    #             legal_moves.append(("move", new_position))
    #     if current_player.remaining_walls > 0:
    #         # tester un mur en position fixe
    #         test_wall = Wall(position=Position(x=3, y=3),
    #                             orientation="horizontal")
    #         if self.is_valid_wall(test_wall):
    #             legal_moves.append(("wall", test_wall))
    #     if not legal_moves:
            
    #         raise Exception("Aucun coup légal trouvé pour l'IA")
    #     move_type, move_value = random.choice(legal_moves)
    #     if move_type == "move":
    #         self.move_pawn(current_player.id, move_value.dict())
    #     else:
    #         self.place_wall(current_player.id, move_value.dict())

    def evaluate_pawn_moves(self, player: Player, game_state: GameState) -> Tuple[int, Position]:
        """
        Évalue tous les déplacements valides du joueur donné (avec A*)
        et retourne le meilleur déplacement accompagné de son score.
        """
        best_score = float("-inf")
        best_position = None

        valid_moves = self.get_valid_pawn_moves(player, game_state)

        for move in valid_moves:
            # Créer un faux joueur pour ne pas modifier l'état réel
            simulated_player = Player(
                id=player.id,
                pawn=move,
                remaining_walls=player.remaining_walls
            )

            path_len = self.a_star(simulated_player, game_state)

            if math.isinf(path_len):
                continue  # ce coup mène à une impasse

            score = max(0, 100 - path_len)  # plus le chemin est court, mieux c'est

            if score > best_score:
                best_score = score
                best_position = move

        return best_score, best_position


    # # Méthode pour obtenir les mouvements valides du pion
    # def get_valid_pawn_moves(self, player: Player, opponent: Player, game_state: GameState) -> List[Position]:
    #     moves = []
    #     px, py = player.pawn.x, player.pawn.y
    #     ox, oy = opponent.pawn.x, opponent.pawn.y

    #     directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # haut, droite, bas, gauche

    #     for dx, dy in directions:
    #         nx, ny = px + dx, py + dy
    #         next_pos = Position(x=nx, y=ny)

    #         # Si le déplacement vers cette position n'est pas valide, on ignore
    #         if not self.is_valid_move(player, next_pos):
    #             continue

    #         # Si l'adversaire est sur cette case
    #         if (nx, ny) == (ox, oy):
    #             jx, jy = ox + dx, oy + dy  # position derrière l’adversaire
    #             jump_pos = Position(jx, jy)

    #             # Vérifier s’il est possible de sauter directement par-dessus l’adversaire
    #             if self.is_valid_move(player, jump_pos, game_state):
    #                 moves.append(jump_pos)
    #             else:
    #                 # Sinon, tenter les sauts en diagonale
    #                 if dx == 0:  # mouvement vertical
    #                     for side in [-1, 1]:
    #                         diag_pos = Position(ox + side, oy)
    #                         if self.is_valid_move(player, diag_pos, game_state):
    #                             moves.append(diag_pos)
    #                 elif dy == 0:  # mouvement horizontal
    #                     for side in [-1, 1]:
    #                         diag_pos = Position(ox, oy + side)
    #                         if self.is_valid_move(player, diag_pos, game_state):
    #                             moves.append(diag_pos)
    #         else:
    #             # Déplacement normal
    #             moves.append(next_pos)

    #     return moves

    # def get_valid_pawn_moves(self, player: Player, opponent: Player, game_state: GameState) -> List[Position]:
    #     moves = []
    #     px, py = player.pawn.x, player.pawn.y
    #     directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # haut, droite, bas, gauche

    #     for dx, dy in directions:
    #         nx, ny = px + dx, py + dy
    #         next_pos = Position(x=nx, y=ny)

    #         # 1. Si la position est vide et atteignable (mouvement normal)
    #         if self.is_valid_move(player, next_pos):
    #             # Si cette case ne contient pas l’adversaire, c’est un mouvement normal valide
    #             if (nx, ny) != (opponent.pawn.x, opponent.pawn.y):
    #                 moves.append(next_pos)
    #             else:
    #                 # 2. Si l’adversaire est là, tester les mouvements face-à-face
    #                 # tester les sauts directs ou diagonaux
    #                 for ddx in [-2, -1, 0, 1, 2]:
    #                     for ddy in [-2, -1, 0, 1, 2]:
    #                         if abs(ddx) + abs(ddy) == 2:  # éviter diagonale pure (1,1)
    #                             face_to_face_target = Position(px + ddx, py + ddy)
    #                             if self.is_valid_face_to_face_move(player, face_to_face_target):
    #                                 moves.append(face_to_face_target)
    #     return moves

    def get_valid_pawn_moves(self, player: Player, game_state: GameState) -> List[Position]:
        """
        Retourne tous les mouvements valides du pion (y compris les sauts droits et diagonaux)
        selon les règles officielles de Quoridor, pour 2 ou 4 joueurs.
        Cette version utilise uniquement `game_state` (utile en simulation).
        """
        moves = []
        px, py = player.pawn.x, player.pawn.y
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # haut, droite, bas, gauche
        opponents = [p for p in game_state.players if p.id != player.id]

        # ajouter wall_blocks_in_simulation car wall_blocks_move dépend de self.players, ni de self.walls
        def wall_blocks_in_simulation(from_pos: Position, to_pos: Position) -> bool:
            for wall in game_state.walls:
                if wall.orientation == "horizontal":
                    if from_pos.x == to_pos.x:
                        min_y = min(from_pos.y, to_pos.y)
                        if wall.position.y == min_y and wall.position.x <= from_pos.x < wall.position.x + 2:
                            return True
                elif wall.orientation == "vertical":
                    if from_pos.y == to_pos.y:
                        min_x = min(from_pos.x, to_pos.x)
                        if wall.position.x == min_x and wall.position.y <= from_pos.y < wall.position.y + 2:
                            return True
            return False

        for dx, dy in directions:
            nx, ny = px + dx, py + dy
            neighbor = Position(x=nx, y=ny)

            if not (0 <= nx < 9 and 0 <= ny < 9):
                continue
            if wall_blocks_in_simulation(Position(x=px, y=py), neighbor):
                continue

            opponent_on_neighbor = next((opp for opp in opponents if opp.pawn.x == nx and opp.pawn.y == ny), None)

            if opponent_on_neighbor:
                # Tentative de saut droit
                jump_x, jump_y = nx + dx, ny + dy
                jump_pos = Position(x=jump_x, y=jump_y)
                if (0 <= jump_x < 9 and 0 <= jump_y < 9 and
                    not wall_blocks_in_simulation(Position(x=nx, y=ny), jump_pos) and
                    not any(opp.pawn.x == jump_x and opp.pawn.y == jump_y for opp in opponents)):
                    moves.append(jump_pos)
                    continue  # Saut direct possible, on ne regarde pas les diagonales
                
                # Sinon diagonales

                if dx == 0:  # adversaire en haut/bas → tenter gauche/droite
                    for side_dx in [-1, 1]:
                        diag_pos = Position(x=nx + side_dx, y=ny)
                        if not (0 <= diag_pos.x < 9 and 0 <= diag_pos.y < 9):
                            continue
                        if not wall_blocks_in_simulation(Position(x=nx, y=ny), diag_pos):
                            if not any(p.pawn == diag_pos for p in game_state.players):
                                moves.append(diag_pos)
                elif dy == 0:  # adversaire à gauche/droite → tenter haut/bas
                    for side_dy in [-1, 1]:
                        diag_pos = Position(x=nx, y=ny + side_dy)
                        if not (0 <= diag_pos.x < 9 and 0 <= diag_pos.y < 9):
                            continue
                        if not wall_blocks_in_simulation(Position(x=nx, y=ny), diag_pos):
                            if not any(p.pawn == diag_pos for p in game_state.players):
                                moves.append(diag_pos)
            else:
                # Déplacement simple
                if not any(p.pawn == neighbor for p in game_state.players):
                    moves.append(neighbor)

        return moves
    def evaluate_best_wall_placement(
            self, player: Player, opponent: Player,
            game_state: GameState) -> Tuple[int, Optional[Wall]]:
        best_score = float("-inf")
        best_wall = None

        # On travaille sur une copie de l'état pour ne pas polluer l'état réel
        base_walls = copy.deepcopy(game_state.walls)

        for x in range(8):  # les murs ne peuvent être posés qu’entre 0 et 7
            for y in range(8):
                for orientation in ["horizontal", "vertical"]:
                    wall = Wall(position=Position(x=x, y=y), orientation=orientation)

                    # Simuler les murs temporairement
                    simulated_walls = base_walls + [wall]
                    simulated_game_state = GameState(
                        board=game_state.board,
                        players=game_state.players,
                        walls=simulated_walls,
                        current_turn=game_state.current_turn,
                        game_over=game_state.game_over,
                        winner_id=game_state.winner_id,
                    )

                    # Vérifier si ce mur est valide dans la simulation
                    if not self.is_valid_wall(wall, walls=game_state.walls):
                        continue

                    # Vérifier si ce mur bloque complètement un joueur
                    if not self.has_path(player.pawn, player.id, simulated_game_state) or not self.has_path(opponent.pawn, opponent.id, simulated_game_state):
                        continue

                    # Évaluer les longueurs de chemin
                    my_path_len = self.a_star(player, simulated_game_state)
                    opp_path_len = self.a_star(opponent, simulated_game_state)

                    # Heuristique : on veut ralentir l'adversaire plus qu'on ne se ralentit
                    score = max(0, 100 - opp_path_len) - 0.5 * max(0, 100 - my_path_len)

                    if score > best_score:
                        best_score = score
                        best_wall = wall

        return best_score, best_wall

    # Méthode A*


    # def a_star(self, player: Player, game_state: GameState) -> int:
    #     """Implémentation de l’A* pour trouver le chemin le plus court."""
    #     start = (player.pawn.x, player.pawn.y)
    #     goal_row = 0 if player.id == 2 else 8

    #     open_set = []  # file de prioritée contenant les positions à explorer ordonnées par le score total
    #     heapq.heappush(
    #         open_set,
    #         (0 + self.heuristic(start, goal_row), 0, start
    #         ))  # chaque élément est un tuple (score_total, coût_actuel, position)
    #     #score_total = coût actuel + heuristique (estimation de la distance restante).
    #     visited = set()

    #     while open_set:
    #         _, cost, current = heapq.heappop(
    #             open_set
    #         )  #On retire la position ayant le plus petit score total (priorité la plus haute)
    #         x, y = current

    #         if y == goal_row:
    #             return cost

    #         if current in visited:
    #             continue
    #         visited.add(current)

    #         for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
    #             nx, ny = x + dx, y + dy
    #             if 0 <= nx < 9 and 0 <= ny < 9:
    #                 new_pos = Position(x=nx, y=ny)
    #                 fake_player = Player(id=player.id, pawn=new_pos,
    #                                     remaining_walls=player.remaining_walls)
    #                 if self.is_valid_move(fake_player, new_pos):
    #                     heapq.heappush(open_set, (cost + 1 + self.heuristic(
    #                         (nx, ny), goal_row), cost + 1, (nx, ny)))
    #                     #self.print_board()
    #                     #print(f"Déplacement Valide de {current} vers {new_pos}")

    #                 #else:
    #                     #print(f"Déplacement invalide de {current} vers {new_pos}")
    #                     #self.print_board()
    #     #print(f"Aucun chemin trouvé pour le joueur {player.id} depuis {start}")
    #     #self.print_board()
    #     return float("inf")

    def a_star(self, player: Player, game_state: GameState) -> int:
        """Implémentation de l’A* pour trouver le chemin le plus court."""
        start = (player.pawn.x, player.pawn.y)
        goal_y = 0 if player.id == 2 else 8
        visited = set()
        open_set = []
        heapq.heappush(open_set, (self.heuristic(start, goal_y), 0, start))

        while open_set:
            _, cost, (cx, cy) = heapq.heappop(open_set)

            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))

            if cy == goal_y:
                return cost

            # Créer un fake player pour obtenir les moves possibles depuis (cx, cy)
            simulated_player = Player(id=player.id, pawn=Position(x=cx, y=cy), remaining_walls=player.remaining_walls)
            neighbors = self.get_valid_pawn_moves(simulated_player, game_state)

            for pos in neighbors:
                if (pos.x, pos.y) not in visited:
                    heapq.heappush(
                        open_set,
                        (
                            cost + 1 + self.heuristic((pos.x, pos.y), goal_y),
                            cost + 1,
                            (pos.x, pos.y)
                        )
                    )

        return float("inf")


    # Foction d'estimation de la distance restante
    def heuristic(self, position: Tuple[int, int], goal_row: int) -> int:
        # Heuristique de Manhattan simple (pas de diagonale)
        return abs(
            position[1] - goal_row
        )  #la distance verticale entre la position actuelle (y) et goal_row






    # ──────────────── UTILITAIRES POUR MINIMAX ────────────────

    def save_state(self):
        """Sauvegarde superficielle de l’état du jeu pour backtracking."""
        return {
            "players": copy.deepcopy(self.players),
            "walls":   copy.deepcopy(self.walls),
            "turn":    self.current_turn,
            "over":    self.game_over,
            "winner":  self.winner_id,
        }

    def load_state(self, snapshot):
        """Restaure l’état précédemment sauvé."""
        self.players      = snapshot["players"]
        self.walls        = snapshot["walls"]
        self.current_turn = snapshot["turn"]
        self.game_over    = snapshot["over"]
        self.winner_id    = snapshot["winner"]

    def get_all_moves(self) -> list[tuple[str, object]]:
        """
        Construit la liste de tous les coups légaux :
        - ("move", Position) pour les déplacements,
        - ("wall", Wall) pour les placements de mur.
        """
        moves: list[tuple[str, object]] = []

        # Joueur courant
        curr = next(p for p in self.players if p.id == self.current_turn)
        state = self.get_game_state()

        # –– Déplacements de pion valides
        for pos in self.get_valid_pawn_moves(curr, state):
            moves.append(("move", pos))

        # –– Placements de mur valides
        if curr.remaining_walls > 0:
            for x in range(8):
                for y in range(8):
                    for orient in ("horizontal", "vertical"):
                        w = Wall(position=Position(x=x, y=y), orientation=orient)
                        if self.is_valid_wall(w, walls=state.walls):
                            moves.append(("wall", w))

        return moves

    def evaluate_state(self) -> float:
        """
        Heuristique simple : différence de longueur de chemin A* entre
        l'adversaire et le joueur courant.
        """
        #("debut evaluate state")
        state = self.get_game_state()
        curr = next(p for p in state.players if p.id == state.current_turn)
        opp = next(p for p in state.players if p.id != state.current_turn)

        my_len = self.a_star(curr, state)
        op_len = self.a_star(opp, state)

        # Log des valeurs calculées
        #print(f"Longueur du chemin pour le joueur {curr.id} : {my_len}")
        #print(f"Longueur du chemin pour l'adversaire {opp.id} : {op_len}")

        # Vérifiez si les valeurs sont infinies ou NaN
        if math.isinf(my_len) or math.isinf(op_len) or math.isnan(my_len) or math.isnan(op_len):
            ("Erreur : A* a retourné une valeur infinie ou NaN.")
            return float("-inf")  # Retournez une valeur par défaut pour éviter les erreurs
        
        #print("fin evaluate state")

        return float(op_len - my_len)

    def minimax_ab(self,
                    depth: int,
                    alpha: float,
                    beta: float,
                    maximizing: bool) -> float:
        """
        Retourne la valeur Minimax de l’état courant,
        avec élagage alpha‑beta.
        """
        # Cas terminal
        if depth == 0 or self.game_over:
            
            return self.evaluate_state()

        if maximizing:
            max_eval = -math.inf
            for kind, move in self.get_all_moves():
                snap = self.save_state()
                # Applique le coup
                if kind == "move":
                    self.move_pawn(self.current_turn,
                                    {"x": move.x, "y": move.y})
                else:  # "wall"
                    self.place_wall(self.current_turn,
                                    {"position": move.position.dict(),
                                        "orientation": move.orientation}) # en pydantic dict => model_dump
                val = self.minimax_ab(depth - 1, alpha, beta, False)
                self.load_state(snap)

                max_eval = max(max_eval, val)
                alpha    = max(alpha, val)
                if beta <= alpha:
                    break
            #print(f"Maximizing : valeur maximale trouvée = {max_eval}")

            return max_eval

        else:
            min_eval = math.inf
            for kind, move in self.get_all_moves():
                snap = self.save_state()
                if kind == "move":
                    self.move_pawn(self.current_turn,
                                    {"x": move.x, "y": move.y})
                else:
                    self.place_wall(self.current_turn,
                                    {"position": move.position.dict(),
                                        "orientation": move.orientation})
                val = self.minimax_ab(depth - 1, alpha, beta, True)
                self.load_state(snap)

                min_eval = min(min_eval, val)
                beta     = min(beta, val)
                if beta <= alpha:
                    break
            #print(f"Minimizing : valeur minimale trouvée = {min_eval}")

            return min_eval

    def find_best_move(self, depth: int) -> tuple[str, object]:
        """
        Retourne le coup optimal (type, objet) pour le joueur courant
        en explorant jusqu’à 'depth'
        """
        best_val  = -math.inf
        best_move = None
        for kind, move in self.get_all_moves():
            snap = self.save_state()
            if kind == "move":
                self.move_pawn(self.current_turn,
                                {"x": move.x, "y": move.y})
            else:
                self.place_wall(self.current_turn,
                                {"position": move.position.dict(),
                                    "orientation": move.orientation})
            val = self.minimax_ab(depth - 1, -math.inf, math.inf, False)
            self.load_state(snap)

            if val > best_val:
                best_val  = val
                best_move = (kind, move)

        #print(f"Meilleur coup trouvé : {best_move} avec une valeur de {best_val}")

        return best_move


    # ──────────────── MINIMAX apla beta ────────────────
    def ia_move_minmax_ab(self,depth):
        result = self.find_best_move(depth)
        # Trouver le meilleur coup pour l'IA à l'aide de Minimax
        if result is None:
            print("Aucun coup possible pour l'IA.")
            return

        kind, move = result

        # Appliquer le coup trouvé
        if kind == "move":
            if self.move_pawn(self.current_turn, {"x": move.x, "y": move.y}):
                return # partie est finie
        else:  # "wall"
            self.place_wall(self.current_turn, {
                "position": move.position.dict(),
                "orientation": move.orientation
            })
                
    def print_board(self):
        state = self.get_game_state()
        size = 9

        # Préparation de la grille d’affichage (chaque case = 3 colonnes)
        for y in reversed(range(size)):
            # Ligne des pions + murs verticaux
            line = ""
            for x in range(size):
                # Affiche pion ou vide
                pawn_here = next((p.id for p in state.players if p.pawn.x == x and p.pawn.y == y), None)
                if pawn_here:
                    line += f" {pawn_here} "
                else:
                    line += " . "

                # Mur vertical à droite ?
                if any(w.orientation == "vertical" and w.position.x == x and w.position.y == y for w in state.walls):
                    line += "|"
                else:
                    line += " "
            print(line)

            # Ligne des murs horizontaux sous les cases (sauf en bas de la grille)
            if y > 0:
                wall_line = ""
                for x in range(size):
                    if any(w.orientation == "horizontal" and w.position.x == x and w.position.y == y - 1 for w in state.walls):
                        wall_line += "---"
                    else:
                        wall_line += "   "

                    # Espacement ou jonction entre deux murs horizontaux
                    wall_line += " "
                print(wall_line)

    def evaluate_state_2(self) -> float:
        """
        Évalue l'état actuel du jeu.
        Utilise Monte Carlo pour une évaluation plus précise.
        """
        return self.monte_carlo_evaluation(simulations=10)
    
    def monte_carlo_evaluation(self, simulations: int = 10) -> float:
        """
        Évalue un état de jeu en simulant plusieurs parties aléatoires.
        :param simulations: Nombre de simulations à effectuer.
        :return: Score basé sur les résultats des simulations.
        """
        current_player_id = self.current_turn
        wins = 0

        for _ in range(simulations):
            # Sauvegarder l'état actuel
            snapshot = self.save_state()

            # Simuler une partie aléatoire jusqu'à la fin
            while not self.game_over:
                current_player = self.current_turn
                self.ai_move_random(self.get_game_state())

            # Vérifier si le joueur courant a gagné
            if self.winner_id == current_player_id:
                wins += 1
            if simulations == 49:
                print(" 49")
            # Restaurer l'état initial
            self.load_state(snapshot)

        # Retourner un score basé sur le pourcentage de victoires
        return wins / simulations










# Méthodes pour évaluation de l'ia entre elles

# def simulate_game_between_ais(difficulty_p1="easy",
#                               difficulty_p2="hard",
#                               verbose=True,
#                               nb_games=100):
#     """
#     Simule nb_games parties entre deux IA.
#     difficulty_p1 : niveau de l'IA 1 ('easy' ou 'hard')
#     difficulty_p2 : niveau de l'IA 2 ('easy' ou 'hard')
#     """
#     wins_p1 = 0
#     wins_p2 = 0

#     for i in range(nb_games):
#         game = QuoridorGame()
#         max_turns = 200
#         turn_count = 0

#         while not game.game_over and turn_count < max_turns:
#             current_player_id = game.current_turn
#             if current_player_id == 1:
#                 play_ai_turn(game, 1, difficulty=difficulty_p1)
#             else:
#                 play_ai_turn(game, 2, difficulty=difficulty_p2)

#             if verbose:
#                 print(
#                     f"Partie {i+1} - Tour {turn_count + 1} : Joueur {current_player_id} a joué."
#                 )
#                 self.print_board(game)

#             turn_count += 1

#         winner = game.winner_id
#         if winner == 1:
#             wins_p1 += 1
#         elif winner == 2:
#             wins_p2 += 1

#         if verbose:
#             print(
#                 f"Fin de la partie {i+1} en {turn_count} tours. Gagnant : Joueur {winner}"
#             )
#             print("-" * 40)

#     # Affichage du pourcentage
#     print(f"\nAprès {nb_games} parties :")
#     print(
#         f"IA 1 ({difficulty_p1}) : {wins_p1} victoires ({(wins_p1 / nb_games) * 100:.1f}%)"
#     )
#     print(
#         f"IA 2 ({difficulty_p2}) : {wins_p2} victoires ({(wins_p2 / nb_games) * 100:.1f}%)"
#     )
#     print(
#         f"Matchs nuls : {nb_games - wins_p1 - wins_p2} ({((nb_games - wins_p1 - wins_p2) / nb_games) * 100:.1f}%)"
#     )




# import time

# def simulate_game_with_timing(difficulty_p1="easy", difficulty_p2="hard", nb_games=100):
#     total_time_p1 = 0.0
#     total_time_p2 = 0.0
#     total_moves_p1 = 0
#     total_moves_p2 = 0
#     total_game_time = 0.0

#     for i in range(nb_games):
#         game = QuoridorGame()
#         start_game_time = time.perf_counter()
#         while not game.game_over:
#             current_player = game.current_turn
#             start_move_time = time.perf_counter()
#             if current_player == 1:
#                 play_ai_turn(game, 1, difficulty=difficulty_p1)
#                 total_time_p1 += time.perf_counter() - start_move_time
#                 total_moves_p1 += 1
#             else:
#                 play_ai_turn(game, 2, difficulty=difficulty_p2)
#                 total_time_p2 += time.perf_counter() - start_move_time
#                 total_moves_p2 += 1
#         total_game_time += time.perf_counter() - start_game_time

#     avg_time_per_game = total_game_time / nb_games
#     avg_time_per_move_p1 = total_time_p1 / total_moves_p1 if total_moves_p1 else 0
#     avg_time_per_move_p2 = total_time_p2 / total_moves_p2 if total_moves_p2 else 0

#     print(f"Durée moyenne par partie : {avg_time_per_game:.3f} secondes")
#     print(f"IA 1 ({difficulty_p1}) - Temps moyen par coup : {avg_time_per_move_p1:.3f} secondes")
#     print(f"IA 2 ({difficulty_p2}) - Temps moyen par coup : {avg_time_per_move_p2:.3f} secondes")



    #__________________________________________________________________

    # def ai_move_pawn(self):
    #     """ Méthode de déplacement d'IA """
    #     # Récupérer la position actuelle du pion de l'IA
    #     curr_row, curr_col = self.player_positions[2]

    #     possible_moves = []

    #     # Déplacements adjacents haut,bas,gauche,droite
    #     for dr, dc in [(1, 0), (0, -1), (0, 1), (-1, 0)]:
    #         new_row, new_col = curr_row + dr, curr_col + dc

    #         if 0 <= new_row < self.board_size and 0 <= new_col < self.board_size:
    #             if self.is_valid_pawn_move(curr_row, curr_col, new_row, new_col):
    #                 score = new_row  # Plus la ligne est grande, plus le score est élevé
    #                 possible_moves.append((score, new_row, new_col))

    #     # sauts par-dessus l'adversaire
    #     opponent_row, opponent_col = self.player_positions[1]
    #     if abs(opponent_row - curr_row) == 1 and abs(opponent_col - curr_col) == 0:
    #         # Le pion est en haut ou en bas
    #         jump_row = curr_row + 2 * (opponent_row - curr_row)
    #         if 0 <= jump_row < self.board_size:
    #             if self.is_valid_pawn_move(curr_row, curr_col, jump_row, opponent_col):
    #                 score = jump_row
    #                 possible_moves.append((score, jump_row, opponent_col))
    #     elif abs(opponent_row - curr_row) == 0 and abs(opponent_col - curr_col) == 1:
    #         # Le pion est à gauche ou à droite
    #         jump_col = curr_col + 2 * (opponent_col - curr_col)
    #         if 0 <= jump_col < self.board_size:
    #             if self.is_valid_pawn_move(curr_row, curr_col, opponent_row, jump_col):
    #                 score = curr_row
    #                 possible_moves.append((score, opponent_row, jump_col))

    #     # Sort desc
    #     possible_moves.sort(reverse=True)

    #     if possible_moves:
    #         # Le premier element a le score le plus haut
    #         _, best_row, best_col = possible_moves[0]
    #         return self.move_pawn(best_row, best_col)
    #     else:
    #         return False

    # def ia_evaluate_wall_placement(self, row, col, orientation):
    #     """ Évalue le score du placement d'un mur pour l'IA """

    #     player1_path_length_before = self.calculate_shortest_path_length(1)

    #     # Placer temporairement le mur
    #     if orientation == 'h':
    #         self.orientation = 1
    #     else:
    #         self.vertical_walls[row][col] = 1

    #     # Calculer la longueur du chemin après placement du mur
    #     player1_path_length_after = self.calculate_shortest_path_length(1)

    #     # Retirer le mur temporaire
    #     if orientation == 'h':
    #         self.horizontal_walls[row][col] = 0
    #     else:
    #         self.vertical_walls[row][col] = 0

    #     # Calculer le score basé sur la différence de longueur du chemin avant et après
    #     return player1_path_length_after - player1_path_length_before


    # La méthode ne prend pas en compte les saut en diag
    # def evaluate_pawn_moves_before(self, player: Player, game_state: GameState) -> Tuple[int, Position]:
    #     """Évalue tous les déplacements possibles avec A*  et retourne le meilleur."""
    #     best_score = float("-inf")
    #     best_position = None

    #     for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
    #         new_x = player.pawn.x + dx
    #         new_y = player.pawn.y + dy
    #         pos = Position(new_x, new_y) # creation de la nouvelle position
    #         if 0 <= new_x < 9 and 0 <= new_y < 9 and self.is_valid_move(player, pos, game_state):
    #             old_pos = player.pawn
    #             player.pawn = pos
    #             path_len = self.a_star(player, game_state)
    #             player.pawn = old_pos # On remet le pion à sa position initiale

    #             score = (9 - new_y if player.id == 2 else new_y) * 10 - path_len * 5

    #             if score > best_score:
    #                 best_score = score
    #                 best_position = pos

    #     return best_score, best_position

    # Méthodes utilitaires pour ai_move_hard
