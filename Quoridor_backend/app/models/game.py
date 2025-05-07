import random
import logging
from collections import deque
from app.schemas.game_schema import Position, Wall, GameState, Player
import heapq  # Import the heapq module
from typing import List,Tuple,Optional
logger = logging.getLogger("quoridor")


class QuoridorGame:

    def __init__(self, num_players: int = 2):

        self.board = [["" for _ in range(9)] for _ in range(9)]
        self.walls = []
        self.num_players = num_players
        self.game_over = False  # Indicateur de fin de partie
        self.winner_id = None  # Identifiant du gagnant (None tant que la partie continue)

        if num_players == 2:
            # Positions standard pour 2 joueurs
            self.players = [
                Player(id=1, pawn=Position(x=4, y=0), remaining_walls=10),
                Player(id=2, pawn=Position(x=4, y=8), remaining_walls=10)
            ]
        elif num_players == 4:
            # Pour 4 joueurs, chaque joueur commence au centre d'un côté du plateau.
            self.players = [
                Player(id=1, pawn=Position(x=4, y=0), remaining_walls=5),
                Player(id=2, pawn=Position(x=4, y=8), remaining_walls=5),
                Player(id=3, pawn=Position(x=0, y=4), remaining_walls=5),
                Player(id=4, pawn=Position(x=8, y=4), remaining_walls=5)
            ]
        else:
            raise Exception(
                "Le nombre de joueurs supporté est 2 ou 4 uniquement.")

        #le premier tour est celui du joueur 1 (choix perso)
        self.current_turn = 1

    def get_game_state(self) -> GameState:
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
                    # Si new_pos correspond à l'une des diagonales autorisées
                    if (new_pos.x, new_pos.y) in info["diagonals"]:
                        # Vérifier que la trajectoire de from_pos à new_pos n'est pas bloquée par un mur
                        if self.wall_blocks_move(player.pawn, new_pos):
                            return False
                        # Vérifier que la case d'arrivée est libre
                        if any(p.pawn.x == new_pos.x and p.pawn.y == new_pos.y
                               for p in self.players):
                            return False
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

    def move_pawn(self, player_id: int, new_pos: dict):
        logger.info(
            f"Déplacement demandé pour le joueur {player_id} vers {new_pos}")

        if self.game_over:
            raise Exception(
                "La partie est terminée, aucun autre coup n'est accepté.")

        # new_pos est un dictionnaire contenant x et y
        new_position = Position(**new_pos)
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            raise Exception("Joueur non trouvé")
        if not self.is_valid_move(player, new_position):
            raise Exception("Déplacement invalide")

        # Déplacement du pion
        player.pawn = new_position

        # Vérifier la condition de victoire pour le joueur actuel
        if self.has_won(player):
            print(f"Le joueur {player.id} a gagné!")
            self.game_over = True
            self.winner_id = player.id
            return

        self.switch_turn()

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

    def is_valid_wall(self, wall: Wall) -> bool:
        if wall.orientation not in ["horizontal", "vertical"]:
            return False

        # Pour un mur, la position de référence doit être dans les bornes (entre 0 et 7)
        if not (0 <= wall.position.x < 8 and 0 <= wall.position.y < 8):
            return False

        # Empêcher le chevauchement de murs
        for w in self.walls:
            if w.orientation == wall.orientation:
                if wall.orientation == "horizontal":
                    # Un mur horizontal placé à (x, y) bloque les passages entre (x,y)<->(x,y+1) et (x+1,y)<->(x+1,y+1)
                    # Deux murs horizontaux sur la même ligne se chevauchent si la distance entre leurs positions x est <= 1.
                    if w.position.y == wall.position.y and abs(
                            w.position.x - wall.position.x) <= 1:
                        return False
                elif wall.orientation == "vertical":
                    # Un mur vertical placé à (x, y) bloque les passages entre (x,y)<->(x+1,y) et (x,y+1)<->(x+1,y+1)
                    # Deux murs verticaux sur la même colonne se chevauchent si la distance entre leurs positions y est <= 1.
                    if w.position.x == wall.position.x and abs(
                            w.position.y - wall.position.y) <= 1:
                        return False
            else:
                # ajouter une vérification pour empêcher l'intersection
                # (empêcher qu'un mur horizontal et un mur vertical se croisent de manière à couvrir le même segment.les murs ne doivent pas se chevaucher, même en travers.
                if wall.orientation == "horizontal" and w.orientation == "vertical":
                    # Un mur horizontal occupe [wall.position.x, wall.position.x+1] sur la ligne wall.position.y
                    # Un mur vertical occupe [w.position.y, w.position.y+1] sur la colonne w.position.x
                    # On interdit l'intersection si :
                    #   w.position.x est dans [wall.position.x, wall.position.x+1]
                    #   et wall.position.y est dans [w.position.y, w.position.y+1]
                    if wall.position.x <= w.position.x <= wall.position.x + 1 and w.position.y <= wall.position.y <= w.position.y + 1:
                        return False
                elif wall.orientation == "vertical" and w.orientation == "horizontal":
                    # Inverse de ce qui précède
                    if w.position.x <= wall.position.x <= w.position.x + 1 and wall.position.y <= w.position.y <= wall.position.y + 1:
                        return False

        return True

    def place_wall(self, player_id: int, wall_data: dict):
        wall = Wall(**wall_data)
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            raise Exception("Joueur non trouvé")
        if player.remaining_walls <= 0:
            raise Exception("Plus de murs disponibles")
        if not self.is_valid_wall(wall):
            raise Exception("Placement de mur invalide")

        # On pose le mur
        self.walls.append(wall)
        player.remaining_walls -= 1

        # vérifier que chaque joueur a toujours un chemin
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

    def has_path(self, start: Position, player_id: int) -> bool:
        """
        BFS (Breadth-First Search) pour vérifier qu'il existe un chemin depuis la position 'start'
        jusqu'à la ligne opposée (y=8 pour le joueur 1, y=0 pour le joueur 2, etc.)
        """
        goal_row = 8 if player_id == 1 else 0  # Adaptable si plus de 2 joueurs
        visited = set()
        queue = deque()
        queue.append((start.x, start.y))
        visited.add((start.x, start.y))

        while queue:
            cx, cy = queue.popleft()
            # Condition de victoire : atteindre la ligne opposée
            if cy == goal_row:
                return True

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < 9 and 0 <= ny < 9:
                    if (nx, ny) not in visited:
                        # Vérifier qu'aucun mur ne bloque le déplacement
                        if not self.wall_blocks_move(Position(x=cx, y=cy),
                                                     Position(x=nx, y=ny)):
                            visited.add((nx, ny))
                            queue.append((nx, ny))
        return False

    def switch_turn(self):
        self.current_turn = (self.current_turn % self.num_players) + 1

    # #L’IA est très basique (choix aléatoire parmi les coups légaux), on va la modifier plus tard
    def ai_move_random(self):
        # Une IA simple qui effectue aléatoirement un coup légal
        current_player = next(
            (p for p in self.players if p.id == self.current_turn), None)
        legal_moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            new_x = current_player.pawn.x + dx
            new_y = current_player.pawn.y + dy
            new_position = Position(x=new_x, y=new_y)
            if 0 <= new_x < 9 and 0 <= new_y < 9 and self.is_valid_move(
                    current_player, new_position):
                legal_moves.append(("move", new_position))
        if current_player.remaining_walls > 0:
            # tester un mur en position fixe
            test_wall = Wall(position=Position(x=3, y=3),
                             orientation="horizontal")
            if self.is_valid_wall(test_wall):
                legal_moves.append(("wall", test_wall))
        if not legal_moves:
            raise Exception("Aucun coup légal trouvé pour l'IA")
        move_type, move_value = random.choice(legal_moves)
        if move_type == "move":
            self.move_pawn(current_player.id, move_value.dict())
        else:
            self.place_wall(current_player.id, move_value.dict())


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


def ai_move_a_star(self, game_state: GameState):
    current_player = game_state.players[game_state.current_turn]
    opponent = game_state.players[1 - game_state.current_turn]

    best_move = None
    best_score = float("-inf")

    # Évaluer déplacement de pion
    move_score, best_position = self.evaluate_pawn_moves(
        current_player, game_state)
    if move_score > best_score:
        best_score = move_score
        best_move = ("move", best_position)

    # Évaluer placement de mur si encore disponible
    if current_player.remaining_walls > 0:
        wall_score, best_wall = self.evaluate_best_wall_placement(
            current_player, opponent, game_state)
        if wall_score > best_score:
            best_score = wall_score
            best_move = ("wall", best_wall)

    # Appliquer le meilleur coup
    if best_move:
        move_type, move_value = best_move
        if move_type == "move":
            self.move_pawn(current_player.id, move_value, game_state)
        else:
            self.place_wall(current_player.id, move_value, game_state)


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


def evaluate_pawn_moves(self, player: Player,
                        game_state: GameState) -> Tuple[int, Position]:
    """Évalue tous les déplacements valides (incluant sauts et diagonales) avec A* et retourne le meilleur."""

    best_score = float("-inf")
    best_position = None
    opponent = game_state.players[1 - (player.id - 1)]

    # Obtenir tous les mouvements légaux selon les règles du jeu
    valid_moves = self.get_valid_pawn_moves(player, opponent, game_state)

    for pos in valid_moves:
        # Simuler le déplacement
        old_pos = player.pawn
        player.pawn = pos

        # Calculer la longueur réelle du plus court chemin jusqu’à la ligne d’arrivée
        path_len = self.a_star(player, game_state)

        # Revenir à la position originale
        player.pawn = old_pos

        # Score = inverse de la longueur du chemin (plus court = meilleur)
        score = max(
            0, 100 - path_len
        )  # On assure que le score est positif  # ou: 100 - path_len pour un score positif

        if score > best_score:
            best_score = score
            best_position = pos

    return best_score, best_position


def get_valid_pawn_moves(self, player: Player, opponent: Player,
                         game_state: GameState) -> List[Position]:
    """Retourne toutes les positions valides que le joueur peut atteindre en un coup, en respectant les règles de Quoridor."""

    moves = []
    px, py = player.pawn.x, player.pawn.y
    ox, oy = opponent.pawn.x, opponent.pawn.y

    directions = [(0, -1), (1, 0), (0, 1),
                  (-1, 0)]  # haut, droite, bas, gauche

    for dx, dy in directions:
        nx, ny = px + dx, py + dy
        if not self.is_valid_move(player, Position(nx, ny)):
            continue

        # Si la case contient l'adversaire
        if (nx, ny) == (ox, oy):
            jx, jy = ox + dx, oy + dy  # tentative de saut par-dessus
            if self.is_valid_move(opponent, Position(jx, jy)):
                moves.append(Position(jx, jy))  # saut direct
            else:
                # Essayer les deux diagonales
                if dx == 0:
                    for side in [-1, 1]:
                        sidex = ox + side
                        sidey = oy
                        if self.is_valid_move(player, Position(sidex, sidey)):
                            moves.append(Position(sidex, sidey))
                elif dy == 0:
                    for side in [-1, 1]:
                        sidex = ox
                        sidey = oy + side
                        if self.is_valid_move(player, Position(sidex, sidey),
                                              game_state):
                            moves.append(Position(sidex, sidey))
        else:
            moves.append(Position(nx, ny))  # déplacement normal

    return moves


def evaluate_best_wall_placement(
        self, player: Player, opponent: Player,
        game_state: GameState) -> Tuple[int, Optional[Wall]]:
    best_score = float("-inf")
    best_wall = None

    for x in range(9):
        for y in range(9):
            for orientation in ["horizontal", "vertical"]:
                wall = Wall(position=Position(x, y), orientation=orientation)
                if self.is_valid_wall(wall, game_state):

                    # Calculer le chemin de l'adversaire avant le placement du mur
                    path_before_opponent = self.a_star(opponent, game_state)

                    # Simuler l'ajout du mur
                    game_state.walls.append(wall)

                    # Vérifier si les deux joueurs ont toujours un chemin
                    if not self.has_path(player.start_position,
                                         player.id) or not self.has_path(
                                             opponent.start_position,
                                             opponent.id):
                        # Si l'ajout du mur bloque un joueur, on ignore ce placement
                        game_state.walls.pop()  # Annuler l'ajout du mur
                        continue

                    # Évaluer les chemins après placement
                    my_path_len = self.a_star(player, game_state)
                    opponent_path_len = self.a_star(opponent, game_state)

                    # Annuler le mur temporaire
                    game_state.walls.pop()

                    # Score : Prise en compte des conséquences sur le chemins de l'adversaire et de l'ia
                    # Normaliser le score
                    score = score_mur = max(
                        0, 100 -
                        opponent_path_len) - 0.5 * max(0, 100 - my_path_len)

                    if score > best_score:
                        best_score = score
                        best_wall = wall

    return best_score, best_wall


# Méthode A*


def a_star(self, player: Player, game_state: GameState) -> int:
    """Implémentation de l’A* pour trouver le chemin le plus court."""
    start = (player.pawn.x, player.pawn.y)
    goal_row = 0 if player.id == 2 else 8

    open_set = [
    ]  # file de prioritée contenant les positions à explorer ordonnées par le score total
    heapq.heappush(
        open_set,
        (0 + self.heuristic(start, goal_row), 0, start
         ))  # chaque élément est un tuple (score_total, coût_actuel, position)
    #score_total = coût actuel + heuristique (estimation de la distance restante).
    visited = set()

    while open_set:
        _, cost, current = heapq.heappop(
            open_set
        )  #On retire la position ayant le plus petit score total (priorité la plus haute)
        x, y = current

        if y == goal_row:
            return cost

        if current in visited:
            continue
        visited.add(current)

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 9 and 0 <= ny < 9:
                new_pos = Position(nx, ny)
                if self.is_valid_move(player, new_pos):
                    heapq.heappush(open_set, (cost + 1 + self.heuristic(
                        (nx, ny), goal_row), cost + 1, (nx, ny)))
    return float("inf")


# Foction d'estimation de la distance restante
def heuristic(self, position: Tuple[int, int], goal_row: int) -> int:
    # Heuristique de Manhattan simple (pas de diagonale)
    return abs(
        position[1] - goal_row
    )  #la distance verticale entre la position actuelle (y) et goal_row


# Méthodes pour évaluation de l'ia entre elles


def play_ai_turn(game, player_id, difficulty="easy"):
    """Joue un tour pour une IA donnée en fonction de son niveau de difficulté."""
    if difficulty == "easy":
        game.ai_move_random(player_id)
    elif difficulty == "hard":
        game.ai_move_a_star(player_id)
    else:
        raise ValueError(
            "Niveau de difficulté inconnu : utiliser 'easy' ou 'hard'")


def simulate_game_between_ais(difficulty_p1="easy",
                              difficulty_p2="hard",
                              verbose=True,
                              nb_games=100):
    """
    Simule nb_games parties entre deux IA.
    difficulty_p1 : niveau de l'IA 1 ('easy' ou 'hard')
    difficulty_p2 : niveau de l'IA 2 ('easy' ou 'hard')
    """
    wins_p1 = 0
    wins_p2 = 0

    for i in range(nb_games):
        game = QuoridorGame()
        max_turns = 200
        turn_count = 0

        while not game.game_over and turn_count < max_turns:
            current_player_id = game.current_turn
            if current_player_id == 1:
                play_ai_turn(game, 1, difficulty=difficulty_p1)
            else:
                play_ai_turn(game, 2, difficulty=difficulty_p2)

            if verbose:
                print(
                    f"Partie {i+1} - Tour {turn_count + 1} : Joueur {current_player_id} a joué."
                )
                print_board(game)

            turn_count += 1

        winner = game.winner_id
        if winner == 1:
            wins_p1 += 1
        elif winner == 2:
            wins_p2 += 1

        if verbose:
            print(
                f"Fin de la partie {i+1} en {turn_count} tours. Gagnant : Joueur {winner}"
            )
            print("-" * 40)

    # Affichage du pourcentage
    print(f"\nAprès {nb_games} parties :")
    print(
        f"IA 1 ({difficulty_p1}) : {wins_p1} victoires ({(wins_p1 / nb_games) * 100:.1f}%)"
    )
    print(
        f"IA 2 ({difficulty_p2}) : {wins_p2} victoires ({(wins_p2 / nb_games) * 100:.1f}%)"
    )
    print(
        f"Matchs nuls : {nb_games - wins_p1 - wins_p2} ({((nb_games - wins_p1 - wins_p2) / nb_games) * 100:.1f}%)"
    )


#Methode pour affichage du game


def print_board(game_state: GameState):
    size = 9
    # Créer une grille vide
    grid = [[" . " for _ in range(size)] for _ in range(size)]

    # Placer les pions des joueurs
    for player in game_state.players:
        x, y = player.pawn.x, player.pawn.y
        grid[y][x] = f" {player.id} "

    # Affichage ligne par ligne
    for y in range(size):
        # Affichage de la ligne de pions
        line = ""
        for x in range(size):
            line += grid[y][x]
            # Vérifie s'il y a un mur vertical à droite de la case
            if any(wall.position.x == x and wall.position.y == y
                   and wall.orientation == "vertical"
                   for wall in game_state.walls):
                line += "|"
            else:
                line += " "
        print(line)

        # Affichage de la ligne des murs horizontaux sous la ligne de pions
        if y < size - 1:
            wall_line = ""
            for x in range(size):
                if any(wall.position.x == x and wall.position.y == y
                       and wall.orientation == "horizontal"
                       for wall in game_state.walls):
                    wall_line += "--- "
                else:
                    wall_line += "    "
            print(wall_line)
