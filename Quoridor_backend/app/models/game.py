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
    
    def is_valid_face_to_face_move(self, player: Player,
                                   new_pos: Position) -> bool:
        """
        Vérifie si le déplacement de 'player' vers 'new_pos' correspond à un saut face-à-face valide.
        Gère :
        - Saut direct (2 cases orthogonales) si le pion adverse est directement adjacent,
        - Saut diagonal (1 case en diagonale) si le saut direct est bloqué par un mur.
        """
        from_x, from_y = player.pawn.x, player.pawn.y
        dx = new_pos.x - from_x
        dy = new_pos.y - from_y
        abs_dx = abs(dx)
        abs_dy = abs(dy)

        # Cas 1 : Saut direct (deux cases en ligne droite)
        if (abs_dx == 2 and dy == 0) or (abs_dy == 2 and dx == 0):
            mid_x = from_x + (dx // 2)
            mid_y = from_y + (dy // 2)

            # Vérifier qu'un adversaire occupe la case intermédiaire
            if not any(p.id != player.id and p.pawn.x == mid_x
                       and p.pawn.y == mid_y for p in self.players):
                return False

            # Vérifier que les passages ne sont pas bloqués par des murs
            if self.wall_blocks_move(player.pawn, Position(x=mid_x, y=mid_y)):
                return False
            if self.wall_blocks_move(Position(x=mid_x, y=mid_y), new_pos):
                return False
            # Vérifier que la case destination est libre
            if any(p.pawn.x == new_pos.x and p.pawn.y == new_pos.y
                   for p in self.players):
                return False
            return True

        # Cas 2 : Saut diagonal (1 case en diagonale)
        if abs_dx == 1 and abs_dy == 1:
            # On vérifie pour chaque direction cardinale si un adversaire est adjacent
            directions = {
                "north": {
                    "adjacent": (from_x, from_y + 1),
                    "behind": (from_x, from_y + 2),
                    "diagonals": [(from_x - 1, from_y + 1),
                                  (from_x + 1, from_y + 1)]
                },
                "south": {
                    "adjacent": (from_x, from_y - 1),
                    "behind": (from_x, from_y - 2),
                    "diagonals": [(from_x - 1, from_y - 1),
                                  (from_x + 1, from_y - 1)]
                },
                "east": {
                    "adjacent": (from_x + 1, from_y),
                    "behind": (from_x + 2, from_y),
                    "diagonals": [(from_x + 1, from_y - 1),
                                  (from_x + 1, from_y + 1)]
                },
                "west": {
                    "adjacent": (from_x - 1, from_y),
                    "behind": (from_x - 2, from_y),
                    "diagonals": [(from_x - 1, from_y - 1),
                                  (from_x - 1, from_y + 1)]
                }
            }

            for direction, info in directions.items():
                adj_x, adj_y = info["adjacent"]

                # Vérifier si un adversaire est bien dans la direction orthogonale
                if not any(p.id != player.id and p.pawn.x == adj_x
                           and p.pawn.y == adj_y for p in self.players):
                    continue

                behind_x, behind_y = info["behind"]
                # Si la case derrière est hors du plateau, on considère qu'elle est bloquée
                behind_blocked = not (0 <= behind_x < 9 and 0 <= behind_y < 9)
                # Sinon, vérifier si un mur bloque le passage derrière l'adversaire
                if not behind_blocked:
                    if self.wall_blocks_move(Position(x=adj_x, y=adj_y),
                                             Position(x=behind_x, y=behind_y)):
                        behind_blocked = True

                if behind_blocked:
                    for diag_x, diag_y in info["diagonals"]:
                        if (new_pos.x, new_pos.y) == (diag_x, diag_y):
                            # Vérification des bornes AVANT de vérifier les murs
                            if not (0 <= diag_x < 9 and 0 <= diag_y < 9):
                                continue
                            if self.wall_blocks_move(Position(x=from_x, y=from_y), Position(x=diag_x, y=diag_y)):
                                continue
                            if any(p.pawn.x == diag_x and p.pawn.y == diag_y for p in self.players):
                                continue
                            return True
            return False

        # Si aucun des cas face-à-face n'est satisfait, le saut n'est pas valide
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

   
  
    # def is_valid_wall(self, wall: Wall, walls: Optional[List[Wall]] = None) -> bool:
    #     walls = walls if walls is not None else self.walls
    #     # print(f"[DEBUG] Testing wall at {wall.position.x},{wall.position.y} orientation={wall.orientation} against {len(walls)} existing walls")

    #     if wall.orientation not in ["horizontal", "vertical"]:
    #         #print(f"[DEBUG] Invalid orientation: {wall.orientation}")
    #         return False

    #     # Bornes de la grille (0 <= x,y < 8)
    #     if not (0 <= wall.position.x < 8 and 0 <= wall.position.y < 8):
    #         #print(f"[DEBUG] Out of bounds: x={wall.position.x}, y={wall.position.y}")
    #         return False

    #     # Les checks de sortie de grille pour orientation ne sont plus nécessaires

    #     for w in walls:
    #         # --- Cas 1 : même orientation => chevauchement interdit
    #         if w.orientation == wall.orientation:
    #             if wall.orientation == "horizontal":
    #                 # Empêche tout chevauchement ou contiguïté horizontale
    #                 if w.position.y == wall.position.y and abs(w.position.x - wall.position.x) <= 1:
    #                     #print(f"[DEBUG] Overlap horizontal with existing at x={w.position.x}, y={w.position.y}")
    #                     return False
    #             elif wall.orientation == "vertical":
    #                 if w.position.x == wall.position.x and abs(w.position.y - wall.position.y) <= 1:
    #                     #print(f"[DEBUG] Overlap vertical with existing at x={w.position.x}, y={w.position.y}")
    #                     return False

    #         # --- Cas 2 : orientations différentes => croisement interdit
    #         else:
    #             # Croisement interdit: murs se croisent en T
    #             # Horizontal vs Vertical
    #             if wall.orientation == "horizontal" and w.orientation == "vertical":
    #                 # Interdiction si vertical commence dans l’intervalle du horizontal
    #                 if (wall.position.x <= w.position.x <= wall.position.x + 1 and
    #                     w.position.y == wall.position.y):
    #                     #print(f"[DEBUG] Crossing detected at {wall.position.x},{wall.position.y} with vertical {w.position.x},{w.position.y}")
    #                     return False

    #             elif wall.orientation == "vertical" and w.orientation == "horizontal":
    #                 if (wall.position.x == w.position.x and
    #                     wall.position.y <= w.position.y <= wall.position.y + 1):
    #                     #print(f"[DEBUG] Crossing detected at {wall.position.x},{wall.position.y} with horizontal {w.position.x},{w.position.y}")
    #                     return False

    #     #print(f"[DEBUG] Wall valid at {wall.position.x},{wall.position.y}")
    #     return True
    # def is_valid_wall(self, wall: Wall, walls: Optional[List[Wall]] = None) -> bool:
    #     """
    #     Vérifie si un mur peut être placé légalement :
    #     - Orientation correcte
    #     - Position dans la grille
    #     - Pas de superposition exacte
    #     - Pas de chevauchement partiel (même orientation)
    #     - Pas de croisement en croix (mur horizontal et vertical au même centre)
    #     """
    #     walls = walls if walls is not None else self.walls

    #     # 1. Vérifie orientation valide
    #     if wall.orientation not in ["horizontal", "vertical"]:
    #         return False

    #     # 2. Vérifie limites de la grille (0 à 7 car un mur couvre 2 cases)
    #     if not (0 <= wall.position.x < 8 and 0 <= wall.position.y < 8):
    #         return False

    #     # 3. Récupère les cellules couvertes par le mur à placer
    #     wall_cells = (
    #         {(wall.position.x, wall.position.y), (wall.position.x + 1, wall.position.y)}
    #         if wall.orientation == "horizontal"
    #         else {(wall.position.x, wall.position.y), (wall.position.x, wall.position.y + 1)}
    #     )

    #     for w in walls:
    #         # 4. Superposition exacte (même position et même orientation)
    #         if w.position == wall.position and w.orientation == wall.orientation:
    #             return False

    #         # 5. Récupère les cellules couvertes par le mur existant
    #         w_cells = (
    #             {(w.position.x, w.position.y), (w.position.x + 1, w.position.y)}
    #             if w.orientation == "horizontal"
    #             else {(w.position.x, w.position.y), (w.position.x, w.position.y + 1)}
    #         )

    #         # 6. Chevauchement partiel (si même orientation et cases partagées)
    #         if w.orientation == wall.orientation and wall_cells & w_cells:
    #             return False

    #         # 7. Croisement en croix : cas très précis d'intersection centrale
    #         # 7. Croisement exact en croix : mur horizontal et vertical se croisent au même point central
    #         if wall.orientation == "horizontal" and w.orientation == "vertical":
    #             if (wall.position.x + 1 == w.position.x and
    #                 wall.position.y == w.position.y):
    #                 return False

    #         elif wall.orientation == "vertical" and w.orientation == "horizontal":
    #             if (wall.position.x == w.position.x and
    #                 wall.position.y + 1 == w.position.y):
    #                 return False



    #     return True
    # def is_valid_wall(self, wall: Wall, walls: Optional[List[Wall]] = None) -> bool:
    #     """
    #     Vérifie la validité d’un mur à placer selon les règles officielles :
    #     - Position et orientation valides
    #     - Pas de superposition
    #     - Pas de chevauchement partiel (même orientation)
    #     - Pas de croisement central entre deux murs perpendiculaires
    #     """
    #     walls = walls if walls is not None else self.walls

    #     if wall.orientation not in ["horizontal", "vertical"]:
    #         return False

    #     if not (0 <= wall.position.x < 8 and 0 <= wall.position.y < 8):
    #         return False

    #     if wall.orientation == "horizontal":
    #         wall_cells = {(wall.position.x, wall.position.y), (wall.position.x + 1, wall.position.y)}
    #     else:
    #         wall_cells = {(wall.position.x, wall.position.y), (wall.position.x, wall.position.y + 1)}

    #     for w in walls:
    #         if w.orientation == "horizontal":
    #             w_cells = {(w.position.x, w.position.y), (w.position.x + 1, w.position.y)}
    #         else:
    #             w_cells = {(w.position.x, w.position.y), (w.position.x, w.position.y + 1)}

    #         # 1. Superposition exacte
    #         if wall.position == w.position and wall.orientation == w.orientation:
    #             return False

    #         # 2. Chevauchement partiel si même orientation (au moins une cellule en commun)
    #         if wall.orientation == w.orientation and wall_cells & w_cells:
    #             return False

    #         # 3. Croisement en croix stricte : exactement 1 cellule partagée + orientations différentes
    #         if wall.orientation == "horizontal" and w.orientation == "vertical":
    #             if wall.position.x + 1 == w.position.x and wall.position.y == w.position.y:
    #                 return False

    #         elif wall.orientation == "vertical" and w.orientation == "horizontal":
    #             if wall.position.x == w.position.x and wall.position.y + 1 == w.position.y:
    #                 return False


    #     return True
    def is_valid_wall(self, wall: Wall, walls: Optional[List[Wall]] = None) -> bool:
        """
        Vérifie si un mur est légal selon les règles officielles de Quoridor :
        - Orientation correcte (horizontal ou vertical)
        - Position dans la grille (0 <= x, y <= 7)
        - Pas de superposition exacte
        - Pas de chevauchement partiel
        - Croisement central exact en “+” autorisé
        - Autres croisements interdits
        """
        walls = walls if walls is not None else self.walls

        # 1. Orientation
        if wall.orientation not in ["horizontal", "vertical"]:
            return False

        # 2. Position dans la grille (mur couvre 2 cases)
        if not (0 <= wall.position.x < 8 and 0 <= wall.position.y < 8):
            return False

        # 3. Cases couvertes par le mur proposé
        if wall.orientation == "horizontal":
            wall_cells = {(wall.position.x, wall.position.y), (wall.position.x + 1, wall.position.y)}
        else:
            wall_cells = {(wall.position.x, wall.position.y), (wall.position.x, wall.position.y + 1)}

        for w in walls:
            # 4. Cases couvertes par un mur existant
            if w.orientation == "horizontal":
                existing_cells = {(w.position.x, w.position.y), (w.position.x + 1, w.position.y)}
            else:
                existing_cells = {(w.position.x, w.position.y), (w.position.x, w.position.y + 1)}

            # 5. Superposition exacte
            if wall.orientation == w.orientation and wall.position == w.position:
                return False

            # 6. Chevauchement partiel interdit (même direction et cases partagées)
            if wall.orientation == w.orientation and wall_cells & existing_cells:
                return False

            # 7. Croisement interdit sauf croisement central exact “+”
            if wall.orientation != w.orientation:
                intersection = wall_cells & existing_cells
                if len(intersection) == 1:
                    i = next(iter(intersection))
                    allowed = (
                        (wall.orientation == "horizontal" and i == (wall.position.x + 1, wall.position.y)) or
                        (wall.orientation == "vertical" and i == (wall.position.x, wall.position.y + 1)) or
                        (w.orientation == "horizontal" and i == (w.position.x + 1, w.position.y)) or
                        (w.orientation == "vertical" and i == (w.position.x, w.position.y + 1))
                    )
                    if not allowed:
                        return False


            
        return True

    # def is_valid_wall(self, wall: Wall, walls: Optional[List[Wall]] = None) -> bool:
    #     walls = walls if walls is not None else self.walls

    #     if wall.orientation not in ["horizontal", "vertical"]:
    #         return False

    #     if not (0 <= wall.position.x < 8 and 0 <= wall.position.y < 8):
    #         return False

    #     if wall.orientation == "horizontal":
    #         wall_cells = {(wall.position.x, wall.position.y), (wall.position.x + 1, wall.position.y)}
    #     else:
    #         wall_cells = {(wall.position.x, wall.position.y), (wall.position.x, wall.position.y + 1)}

    #     for w in walls:
    #         if w.orientation == "horizontal":
    #             existing_cells = {(w.position.x, w.position.y), (w.position.x + 1, w.position.y)}
    #         else:
    #             existing_cells = {(w.position.x, w.position.y), (w.position.x, w.position.y + 1)}

    #         # 1. Superposition exacte
    #         if wall.orientation == w.orientation and wall.position == w.position:
    #             return False

    #         # 2. Chevauchement partiel interdit (même orientation + cases partagées)
    #         if wall.orientation == w.orientation and wall_cells & existing_cells:
    #             return False

    #         # 3. Croisement autorisé uniquement si c’est un croisement central exact
            
    #         if wall.orientation != w.orientation:
    #             intersection = wall_cells & existing_cells
    #             if len(intersection) == 1:
    #                 i = next(iter(intersection))

    #                 # Vérifie si le croisement est un "+" parfait indépendamment de l’ordre
    #                 if (
    #                     (wall.orientation == "horizontal" and
    #                     w.orientation == "vertical" and
    #                     wall.position == Position(x=w.position.x - 1, y=w.position.y) and
    #                     i == (w.position.x, w.position.y))
    #                     or
    #                     (wall.orientation == "vertical" and
    #                     w.orientation == "horizontal" and
    #                     wall.position == Position(x=w.position.x, y=w.position.y - 1) and
    #                     i == (w.position.x, w.position.y))
    #                     or
    #                     (w.orientation == "horizontal" and
    #                     wall.orientation == "vertical" and
    #                     w.position == Position(x=wall.position.x - 1, y=wall.position.y) and
    #                     i == (wall.position.x, wall.position.y))
    #                     or
    #                     (w.orientation == "vertical" and
    #                     wall.orientation == "horizontal" and
    #                     w.position == Position(x=wall.position.x, y=wall.position.y - 1) and
    #                     i == (wall.position.x, wall.position.y))
    #                 ):
    #                     continue  # croisement central autorisé 

    #             return False  # tout autre croisement est interdit 



    #     return True




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
            # Minimax alpha-beta (profondeur 2)
            self.ia_move_minmax_ab(depth=2)
        else:
            raise ValueError(f"Difficulté inconnue : {difficulty}")

    def ai_move_a_star(self, game_state: GameState):
        if self.game_over:
            return  # Ne rien faire si la partie est déjà finie

        idx = self.current_turn - 1
        current_player = self.players[idx]
        opponent = self.players[1 - idx]

        best_move = None
        best_score = -math.inf

        # Évaluer les déplacements de pion
        move_score, best_position, valid_moves = self.evaluate_pawn_moves(current_player, game_state)
        if move_score > best_score:
            best_score = move_score
            best_move = ("move", best_position)
            print(f"[DEBUG] Meilleur déplacement pour le pion : {best_position} avec score {move_score}")
        # Évaluer les placements de mur si le joueur a encore des murs
        if current_player.remaining_walls > 0:
            
            wall_score, best_wall = self.evaluate_best_wall_placement(current_player, opponent, game_state)
            print(f"[DEBUG] MUR  coup trouvé : {best_wall} avec score {wall_score}")

            if best_wall is not None and wall_score > best_score:
                best_score = wall_score
                best_move = ("wall", best_wall)
                print(f"[DEBUG] Meilleur coup trouvé : {best_wall} avec score {best_score}")
        # Appliquer le meilleur coup
        if best_move is None:
            # Sélectionne un coup au hasard ou un déplacement simple
            best_move = ("move", valid_moves[0])

        if best_move:
            kind, obj = best_move
            print(f"[DEBUG] IA choisit le coup : {kind} avec {obj}, score={best_score}")
            if kind == "move":
                # Utiliser move_pawn pour déplacer et gérer la victoire
                finished = self.move_pawn(current_player.id, {"x": obj.x, "y": obj.y})
                if finished:
                    return  # Le joueur a gagné, fin du tour
            else:  # placement de mur
                self.place_wall(current_player.id, obj.dict())
        else:
            raise Exception("Aucun coup possible pour l’IA (move_a_star)")
    
    

    # def ai_move_random(self, game_state: GameState):
    #     """
    #     Une IA simple qui effectue aléatoirement un coup légal.
    #     """
    #     idx = game_state.current_turn - 1
    #     current_player = game_state.players[idx]
    #     opponent = game_state.players[1 - idx]

    #     legal_moves = []
    
    #     # Obtenir tous les déplacements valides pour le pion
    #     valid_pawn_moves = self.get_valid_pawn_moves(current_player, game_state)
    #     for move in valid_pawn_moves:
    #         legal_moves.append(("move", move))
    
    #     # Ajouter les placements de murs valides
    #     if current_player.remaining_walls > 0:
    #         for x in range(8):
    #             for y in range(8):
    #                 for orientation in ["horizontal", "vertical"]:
    #                     test_wall = Wall(position=Position(x=x, y=y), orientation=orientation)
    #                     if self.is_valid_wall(test_wall):
    #                         legal_moves.append(("wall", test_wall))
    
    #     # Si aucun coup légal n'est disponible, lever une exception
    #     if not legal_moves:
    #         raise Exception("Aucun coup légal trouvé pour l'IA")
    
    #     # Choisir un coup aléatoire parmi les coups légaux
    #     move_type, move_value = random.choice(legal_moves)
    #     if move_type == "move":
    #         if self.move_pawn(current_player.id, move_value.dict()):
    #             return # partie est finie 
    #     else:
    #         self.place_wall(current_player.id, move_value.dict())
    
    def ai_move_random(self, game_state: GameState):
        """
        IA rapide avec logique simple :
        - Privilégie les déplacements vers l'avant
        - Ne pose un mur que si l'adversaire est proche de gagner
        """
        import random

        idx = game_state.current_turn - 1
        current_player = game_state.players[idx]
        opponent = game_state.players[1 - idx]

        direction = 1 if current_player.id == 1 else -1  # direction vers l’avant

        # 1. Tenter de bloquer si l’adversaire est très proche de la ligne de victoire
        if current_player.remaining_walls > 0:
            oy = opponent.pawn.y
            if (opponent.id == 1 and oy >= 4) or (opponent.id == 2 and oy <= 2):
                ox = opponent.pawn.x
                possible_walls = []
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        x, y = ox + dx, oy + dy
                        if 0 <= x < 8 and 0 <= y < 8:
                            for orientation in ["horizontal", "vertical"]:
                                wall = Wall(position=Position(x=x, y=y), orientation=orientation)
                                if self.is_valid_wall(wall):
                                    possible_walls.append(wall)
                if possible_walls:
                    chosen_wall = random.choice(possible_walls)
                    self.place_wall(current_player.id, chosen_wall.dict())
                    return  

        # 2. Sinon, se déplacer (privilégier l’avant)
        valid_moves = self.get_valid_pawn_moves(current_player, game_state)
        forward_moves = []
        other_moves = []

        for move in valid_moves:
            if (move.y - current_player.pawn.y) == direction:
                forward_moves.append(move)
            else:
                other_moves.append(move)

        if forward_moves:
            move = random.choice(forward_moves)
        elif other_moves:
            move = random.choice(other_moves)
        else:
            raise Exception("Aucun déplacement possible")

        self.move_pawn(current_player.id, move.dict())
        return  

    # def ai_move_random(self, game_state: GameState):
    #     """
    #     IA améliorée rapide avec Monte Carlo :
    #     - Évalue quelques coups autour du pion adverse
    #     - Choisit le coup avec le meilleur score estimé
    #     """
    #     import random

    #     idx = game_state.current_turn - 1
    #     current_player = game_state.players[idx]
    #     opponent = game_state.players[1 - idx]

    #     best_score = -1
    #     best_action = None

    #     # 1. Déplacements possibles
    #     for move in self.get_valid_pawn_moves(current_player, game_state):
    #         self.save_state()
    #         self.move_pawn(current_player.id, move.dict())
    #         score = self.monte_carlo_evaluation(simulations=3)
    #         self.load_state()
    #         if score > best_score:
    #             best_score = score
    #             best_action = ("move", move)
    #             if score == 1.0:
    #                 break  # score parfait → pas besoin d'évaluer plus

    #     # 2. Murs (si murs restants et adversaire proche)
    #     if best_score < 1.0 and current_player.remaining_walls > 0:
    #         ox, oy = opponent.pawn.x, opponent.pawn.y
    #         for dx in [-1, 0, 1]:
    #             for dy in [-1, 0, 1]:
    #                 x, y = ox + dx, oy + dy
    #                 if 0 <= x < 8 and 0 <= y < 8:
    #                     for orientation in ["horizontal", "vertical"]:
    #                         wall = Wall(position=Position(x, y), orientation=orientation)
    #                         if self.is_valid_wall(wall):
    #                             self.save_state()
    #                             if self.place_wall(current_player.id, wall.dict()):
    #                                 score = self.monte_carlo_evaluation(simulations=3)
    #                                 self.load_state()
    #                                 if score > best_score:
    #                                     best_score = score
    #                                     best_action = ("wall", wall)
    #                                     if score == 1.0:
    #                                         break

    #     # Exécuter le meilleur coup
    #     if best_action:
    #         move_type, move_value = best_action
    #         if move_type == "move":
    #             self.move_pawn(current_player.id, move_value.dict())
    #         else:
    #             self.place_wall(current_player.id, move_value.dict())
    #     else:
    #         raise Exception("Aucun coup légal trouvé")

    # def evaluate_pawn_moves(self, player: Player, game_state: GameState) -> Tuple[int, Position]:
    #     """
    #     Évalue tous les déplacements valides du joueur donné (avec A*)
    #     et retourne le meilleur déplacement accompagné de son score.
    #     """
    #     best_score = float("-inf")
    #     best_position = None

    #     valid_moves = self.get_valid_pawn_moves(player, game_state)

    #     for move in valid_moves:
    #         # Créer un faux joueur pour ne pas modifier l'état réel
    #         simulated_player = Player(
    #             id=player.id,
    #             pawn=move,
    #             remaining_walls=player.remaining_walls
    #         )

    #         path_len = self.a_star(simulated_player, game_state)

    #         if math.isinf(path_len):
    #             continue  # ce coup mène à une impasse

    #         score = max(0, 100 - path_len)  # plus le chemin est court, mieux c'est

    #         if score > best_score:
    #             best_score = score
    #             best_position = move

    #     return best_score, best_position
    def evaluate_pawn_moves(self, player: Player, game_state: GameState) -> Tuple[float, Position]:
        """
        Évalue les déplacements valides du joueur en priorisant les plus courts
        et les plus "en avant" vers la ligne d'arrivée.
        """
        best_score = float("-inf")
        best_position = None
        valid_moves = self.get_valid_pawn_moves(player, game_state)

        for move in valid_moves:
            simulated_player = Player(
                id=player.id,
                pawn=move,
                remaining_walls=player.remaining_walls
            )
            path_len = self.a_star(simulated_player, game_state)
            if math.isinf(path_len):
                continue

            # Encourager les mouvements vers l'avant
            # forward_progress = (move.y - player.pawn.y) if player.id == 1 else (player.pawn.y - move.y)
            # score = (100 - path_len) + 0.5 * forward_progress
            # Normaliser le score pour qu'il soit entre 0 et 1
            score = 1 - (path_len / 100)

            if score > best_score:
                best_score = score
                best_position = move

        return best_score, best_position ,valid_moves

    def get_valid_pawn_moves(self, player: Player, game_state: GameState) -> List[Position]:
        """
        Retourne tous les mouvements valides du pion pour un jeu à 2 joueurs uniquement.
        Inclut les sauts et les diagonales selon les règles officielles de Quoridor.
        """
        moves = []
        px, py = player.pawn.x, player.pawn.y
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # haut, droite, bas, gauche

        # Adversaire unique (2 joueurs)
        opponent = game_state.players[1 - (player.id - 1)]

        # ajouter wall_blocks_in_simulation car wall_blocks_move dépend de self.players, ni de self.walls
        def wall_blocks(from_pos: Position, to_pos: Position) -> bool:
            for wall in game_state.walls:
                if wall.orientation == "horizontal":
                    if from_pos.x == to_pos.x:
                        if wall.position.y == min(from_pos.y, to_pos.y) and wall.position.x <= from_pos.x < wall.position.x + 2:
                            return True
                elif wall.orientation == "vertical":
                    if from_pos.y == to_pos.y:
                        if wall.position.x == min(from_pos.x, to_pos.x) and wall.position.y <= from_pos.y < wall.position.y + 2:
                            return True
            return False

        for dx, dy in directions:
            nx, ny = px + dx, py + dy
            neighbor = Position(x=nx, y=ny)

            if not (0 <= nx < 9 and 0 <= ny < 9):
                continue
            if wall_blocks(Position(x=px, y=py), neighbor):
                continue

            if opponent.pawn.x == nx and opponent.pawn.y == ny:
                # Saut en ligne droite
                jump_x, jump_y = nx + dx, ny + dy
                jump_pos = Position(x=jump_x, y=jump_y)
                if (0 <= jump_x < 9 and 0 <= jump_y < 9 and
                    not wall_blocks(Position(x=nx, y=ny), jump_pos) and
                    (jump_pos != player.pawn and jump_pos != opponent.pawn)):
                    moves.append(jump_pos)
                    continue
                # Saut en diagonale
                #elif wall_blocks(Position(x=nx, y=ny), jump_pos):
                # Mur bloque → diagonale autorisée
                # Saut en diagonale
                if dx == 0:  # adversaire en haut/bas donc tester gauche/droite
                    for side_dx in [-1, 1]:
                        diag = Position(x=nx + side_dx, y=ny)
                        if 0 <= diag.x < 9 and not wall_blocks(Position(x=nx, y=ny), diag):
                            moves.append(diag)
                elif dy == 0:  # adversaire à gauche/droite donc tester haut/bas
                    for side_dy in [-1, 1]:
                        diag = Position(x=nx, y=ny + side_dy)
                        if 0 <= diag.y < 9 and not wall_blocks(Position(x=nx, y=ny), diag):
                            moves.append(diag)
            else:
                # Déplacement simple
                if neighbor != opponent.pawn:
                    moves.append(neighbor)

        return moves

    # def evaluate_best_wall_placement(
    #         self, player: Player, opponent: Player,
    #         game_state: GameState) -> Tuple[int, Optional[Wall]]:
    #     best_score = float("-inf")
    #     best_wall = None

    #     # On travaille sur une copie de l'état pour ne pas polluer l'état réel
    #     base_walls = copy.deepcopy(game_state.walls)

    #     for x in range(8):  # les murs ne peuvent être posés qu’entre 0 et 7
    #         for y in range(8):
    #             for orientation in ["horizontal", "vertical"]:
    #                 wall = Wall(position=Position(x=x, y=y), orientation=orientation)

    #                 # Simuler les murs temporairement
    #                 simulated_walls = base_walls + [wall]
    #                 simulated_game_state = GameState(
    #                     board=game_state.board,
    #                     players=game_state.players,
    #                     walls=simulated_walls,
    #                     current_turn=game_state.current_turn,
    #                     game_over=game_state.game_over,
    #                     winner_id=game_state.winner_id,
    #                 )

    #                 # Vérifier si ce mur est valide dans la simulation
    #                 if not self.is_valid_wall(wall, walls=game_state.walls):
    #                     continue

    #                 # Vérifier si ce mur bloque complètement un joueur
    #                 if not self.has_path(player.pawn, player.id, simulated_game_state) or not self.has_path(opponent.pawn, opponent.id, simulated_game_state):
    #                     continue

    #                 # Évaluer les longueurs de chemin
    #                 my_path_len = self.a_star(player, simulated_game_state)
    #                 opp_path_len = self.a_star(opponent, simulated_game_state)

    #                 # Heuristique : on veut ralentir l'adversaire plus qu'on ne se ralentit
    #                 score = max(0, 100 - opp_path_len) - 0.5 * max(0, 100 - my_path_len)

    #                 if score > best_score:
    #                     best_score = score
    #                     best_wall = wall

    #     return best_score, best_wall
    def evaluate_best_wall_placement(
        self, player: Player, opponent: Player, game_state: GameState
    ) -> Tuple[float, Optional[Wall]]:
        best_score = float("-inf")
        best_wall = None

        base_walls = copy.deepcopy(game_state.walls)
        original_opp_path = self.a_star(opponent, game_state)
        original_my_path = self.a_star(player, game_state)

        tested_walls = 0
        valid_walls = 0

        for x in range(8):
            for y in range(8):
                for orientation in ["horizontal", "vertical"]:
                    tested_walls += 1
                    wall = Wall(position=Position(x=x, y=y), orientation=orientation)

                    if not self.is_valid_wall(wall, walls=base_walls):
                        continue
                    valid_walls += 1

                    simulated_walls = base_walls + [wall]
                    simulated_game_state = GameState(
                        board=game_state.board,
                        players=game_state.players,
                        walls=simulated_walls,
                        current_turn=game_state.current_turn,
                        game_over=game_state.game_over,
                        winner_id=game_state.winner_id,
                    )

                    if not self.has_path(player.pawn, player.id, simulated_game_state) or \
                    not self.has_path(opponent.pawn, opponent.id, simulated_game_state):
                        continue

                    new_opp_path = self.a_star(opponent, simulated_game_state)
                    new_my_path = self.a_star(player, simulated_game_state)

                    delta_opp = new_opp_path - original_opp_path
                    delta_me = new_my_path - original_my_path

                    # Panic mode : adversaire proche de gagner
                    if original_opp_path <= 4:
                        delta_opp *= 3.0  # mode panique fort
                        raw_score = 2.5 * delta_opp - 1.0 * delta_me + 2.0
                    elif delta_opp > 0:
                        raw_score = 2.0 * delta_opp - 1.0 * delta_me + 1.0
                    else:
                        raw_score = -999  # mur inutile

                    print(f"[DEBUG] Mur testé : ({x},{y},{orientation}) deltaopp={delta_opp}, Δme={delta_me}, score={raw_score:.3f}")

                    if raw_score > best_score:
                        best_score = raw_score
                        best_wall = wall

        print(f"[DEBUG] Total murs testés : {tested_walls}, valides : {valid_walls}")
        
        if best_wall is None:
            print("[DEBUG] Aucun mur utile trouvé.")
            return 0, None

        final_score = 1 / (1 + math.exp(-best_score / 2))
        print(f"[DEBUG] MUR coup trouvé : {best_wall} avec score {final_score:.3f}")
        return final_score, best_wall



    def a_star(self, player: Player, game_state: GameState) -> int:
        """
        Implémentation de l'algorithme A* pour trouver le chemin le plus court
        du joueur player vers la ligne d'arrivée (ligne 0 ou ligne 8).
        Retourne le nombre minimal de déplacements nécessaires.

        Cette version est optimisée pour 2 joueurs.
        """

        # Position de départ du pion
        start = (player.pawn.x, player.pawn.y)

        if player.id == 1:
            goal_y = 8  # joueur 1 commence en haut, doit aller en bas
        elif player.id == 2:
            goal_y = 0  # joueur 2 commence en bas, doit aller en haut
        else:
            raise ValueError("Joueur inconnu")


        # Ensemble des cases déjà visitées
        visited = set()

        # File de priorité : chaque élément est (score_total, coût_actuel, position)
        # score_total = coût_actuel + estimation heuristique jusqu'à l'arrivée
        open_set = []
        heapq.heappush(open_set, (self.heuristic(start, goal_y), 0, start))

        while open_set:
            _, cost, (cx, cy) = heapq.heappop(open_set)

            # Ne pas revisiter une case déjà explorée
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))

            # Si on atteint la ligne d'arrivée, on retourne le coût total (nombre de pas)
            if cy == goal_y:
                return cost

            # Simule un joueur temporaire placé sur cette case pour calculer ses mouvements valides
            simulated_player = Player(id=player.id, pawn=Position(x=cx, y=cy), remaining_walls=player.remaining_walls)
            neighbors = self.get_valid_pawn_moves(simulated_player, game_state)

            for pos in neighbors:
                if (pos.x, pos.y) not in visited:
                    # Calcul du score : coût + 1 + estimation de la distance restante
                    score = cost + 1 + self.heuristic((pos.x, pos.y), goal_y)
                    heapq.heappush(open_set, (score, cost + 1, (pos.x, pos.y)))

        # Si aucun chemin trouvé (rare)
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


    def print_board_from_state(self, state: GameState):
        size = 9
        wall_map = {(w.position.x, w.position.y, w.orientation): True for w in state.walls}

        for y in range(size):
            # Ligne de pions
            row = ""
            for x in range(size):
                player_here = next((p.id for p in state.players if p.pawn.x == x and p.pawn.y == y), None)
                cell = str(player_here) if player_here else "."
                row += f" {cell} "
                row += "|" if wall_map.get((x, y, "vertical")) else " "
            print(row)

            # Ligne de murs horizontaux
            wall_row = ""
            for x in range(size):
                wall_row += "===" if wall_map.get((x, y, "horizontal")) else "   "
                wall_row += " "
            print(wall_row)

    def evaluate_state_2(self) -> float:
        """
        Évalue l'état actuel du jeu via des simulations Monte Carlo.
        """
        return self.monte_carlo_evaluation(simulations=5)

    def monte_carlo_evaluation(self, simulations: int = 1) -> float:
        """
        Évalue un état de jeu en simulant plusieurs parties avec l’IA aléatoire.
        :param simulations: Nombre de parties simulées.
        :return: Score (entre 0 et 1) basé sur le taux de victoire du joueur courant.
        """
        initial_player_id = self.current_turn
        wins = 0

        for _ in range(simulations):
            # Sauvegarder l’état de départ
            snapshot = self.save_state()

            # Simuler la partie
            try:
                while not self.game_over:
                    game_state = self.get_game_state()
                    self.ai_move_random(game_state)
            except Exception:
                # Si une erreur survient (ex: aucun coup possible), on arrête la simulation
                pass

            # Comptabiliser la victoire si le joueur courant gagne
            if self.winner_id == initial_player_id:
                wins += 1

            # Restaurer l’état initial pour la prochaine simulation
            self.load_state(snapshot)

        # Score final : proportion de victoires sur toutes les simulations
        return wins / simulations




