import random
from collections import deque
from app.schemas.game_schema import Position, Wall, GameState, Player

class QuoridorGame:
    def __init__(self):
        # Initialisation d'un plateau 9x9 (pour l'affichage, on garde un tableau simple)
        self.board = [["" for _ in range(9)] for _ in range(9)]

        # Initialisation des joueurs : joueur 1 au centre de la première ligne, joueur 2 au centre de la dernière ligne
        self.players = [
            Player(id=1, pawn=Position(x=4, y=0), remaining_walls=10),
            Player(id=2, pawn=Position(x=4, y=8), remaining_walls=10)
        ]
        self.walls = []  # Liste des murs (objets Wall)
        self.current_turn = 1


    def get_game_state(self) -> GameState:
        return GameState(
            board=self.board,
            players=self.players,
            walls=self.walls,
            current_turn=self.current_turn
        )


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
            if not any(p.id != player.id and p.pawn.x == mid_x and p.pawn.y == mid_y for p in self.players):
                return False
            
            # Vérifier que les passages ne sont pas bloqués par des murs
            if self.wall_blocks_move(player.pawn, Position(x=mid_x, y=mid_y)):
                return False
            if self.wall_blocks_move(Position(x=mid_x, y=mid_y), new_pos):
                return False
            # Vérifier que la case destination est libre
            if any(p.pawn.x == new_pos.x and p.pawn.y == new_pos.y for p in self.players):
                return False
            return True

        # Cas 2 : Saut diagonal (1 case en diagonale)
        if abs_dx == 1 and abs_dy == 1:
            # On vérifie pour chaque direction cardinale si un adversaire est adjacent
            directions = {
                "north": {
                    "adjacent": (from_x, from_y + 1),
                    "behind": (from_x, from_y + 2),
                    "diagonals": [(from_x - 1, from_y + 1), (from_x + 1, from_y + 1)]
                },
                "south": {
                    "adjacent": (from_x, from_y - 1),
                    "behind": (from_x, from_y - 2),
                    "diagonals": [(from_x - 1, from_y - 1), (from_x + 1, from_y - 1)]
                },
                "east": {
                    "adjacent": (from_x + 1, from_y),
                    "behind": (from_x + 2, from_y),
                    "diagonals": [(from_x + 1, from_y - 1), (from_x + 1, from_y + 1)]
                },
                "west": {
                    "adjacent": (from_x - 1, from_y),
                    "behind": (from_x - 2, from_y),
                    "diagonals": [(from_x - 1, from_y - 1), (from_x - 1, from_y + 1)]
                }
            }

            for direction, info in directions.items():
                adj_x, adj_y = info["adjacent"]

                # Vérifier si un adversaire est bien dans la direction orthogonale
                if not any(p.id != player.id and p.pawn.x == adj_x and p.pawn.y == adj_y for p in self.players):
                    continue

                behind_x, behind_y = info["behind"]
                # Si la case derrière est hors du plateau, on considère qu'elle est bloquée
                behind_blocked = not (0 <= behind_x < 9 and 0 <= behind_y < 9)
                # Sinon, vérifier si un mur bloque le passage derrière l'adversaire
                if not behind_blocked:
                    if self.wall_blocks_move(Position(x=adj_x, y=adj_y), Position(x=behind_x, y=behind_y)):
                        behind_blocked = True

                if behind_blocked:
                    # Si new_pos correspond à l'une des diagonales autorisées
                    if (new_pos.x, new_pos.y) in info["diagonals"]:
                        # Vérifier que la trajectoire de from_pos à new_pos n'est pas bloquée par un mur
                        if self.wall_blocks_move(player.pawn, new_pos):
                            return False
                        # Vérifier que la case d'arrivée est libre
                        if any(p.pawn.x == new_pos.x and p.pawn.y == new_pos.y for p in self.players):
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
        # new_pos est un dictionnaire contenant x et y
        new_position = Position(**new_pos)
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            raise Exception("Joueur non trouvé")
        if not self.is_valid_move(player, new_position):
            raise Exception("Déplacement invalide")

        # Déplacement du pion    
        player.pawn = new_position

        # Condition de victoire : atteindre la ligne opposée
        if (player.id == 1 and new_position.y == 8) or (player.id == 2 and new_position.y == 0):
            print(f"Joueur {player.id} a gagné!")
        self.switch_turn()


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
                    if w.position.y == wall.position.y and abs(w.position.x - wall.position.x) <= 1:
                        return False
                elif wall.orientation == "vertical":
                    # Un mur vertical placé à (x, y) bloque les passages entre (x,y)<->(x+1,y) et (x,y+1)<->(x+1,y+1)
                    # Deux murs verticaux sur la même colonne se chevauchent si la distance entre leurs positions y est <= 1.
                    if w.position.x == wall.position.x and abs(w.position.y - wall.position.y) <= 1:
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
                        if not self.wall_blocks_move(Position(x=cx, y=cy), Position(x=nx, y=ny)):
                            visited.add((nx, ny))
                            queue.append((nx, ny))
        return False


    def switch_turn(self):
        self.current_turn = 1 if self.current_turn == 2 else 2


    #L’IA présentée est très basique (choix aléatoire parmi les coups légaux), on va la modifier plus tard 
    def ai_move(self):
        # Une IA simple qui effectue aléatoirement un coup légal
        current_player = next((p for p in self.players if p.id == self.current_turn), None)
        legal_moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            new_x = current_player.pawn.x + dx
            new_y = current_player.pawn.y + dy
            new_position = Position(x=new_x, y=new_y)
            if 0 <= new_x < 9 and 0 <= new_y < 9 and self.is_valid_move(current_player, new_position):
                legal_moves.append(("move", new_position))
        if current_player.remaining_walls > 0:
            # Exemple simplifié : tester un mur en position fixe
            test_wall = Wall(position=Position(x=3, y=3), orientation="horizontal")
            if self.is_valid_wall(test_wall):
                legal_moves.append(("wall", test_wall))
        if not legal_moves:
            raise Exception("Aucun coup légal trouvé pour l'IA")
        move_type, move_value = random.choice(legal_moves)
        if move_type == "move":
            self.move_pawn(current_player.id, move_value.dict())
        else:
            self.place_wall(current_player.id, move_value.dict())
