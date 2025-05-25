import unittest
from app.schemas.game_schema import Position, Wall, GameState, Player
from app.models.game import QuoridorGame

class TestQuoridorGame(unittest.TestCase):

    # Initialisation d’une partie avant chaque test
    def setUp(self):
        self.game = QuoridorGame(num_players=2)

    # Vérifie les positions initiales des deux joueurs
    def test_initial_positions(self):
        p1, p2 = self.game.players
        self.assertEqual((p1.pawn.x, p1.pawn.y), (4, 0))  # joueur 1
        self.assertEqual((p2.pawn.x, p2.pawn.y), (4, 8))  # joueur 2

    # Test d’un déplacement valide simple (vers le haut)
    def test_valid_move_basic(self):
        player = self.game.players[0]
        new_pos = Position(x=4, y=1)
        self.assertTrue(self.game.is_valid_move(player, new_pos))

    # Vérifie que les déplacements hors du plateau sont interdits
    def test_invalid_move_out_of_bounds(self):
        player = self.game.players[0]
        new_pos = Position(x=-1, y=0)
        self.assertFalse(self.game.is_valid_move(player, new_pos))

    # Vérifie qu’un placement de mur valide est autorisé
    def test_wall_placement_valid(self):
        wall = Wall(position=Position(x=3, y=3), orientation="horizontal")
        self.assertTrue(self.game.is_valid_wall(wall))
        

    # Vérifie qu’on ne peut pas placer deux fois un mur au même endroit
    def test_wall_placement_overlap(self):
        wall1 = Wall(position=Position(x=3, y=3), orientation="horizontal")
        wall2 = Wall(position=Position(x=3, y=3), orientation="horizontal")
        self.game.walls.append(wall1)  # Ajout du premier mur
        self.assertFalse(self.game.is_valid_wall(wall2))  # Le deuxième est en chevauchement

    # Vérifie que le joueur a un chemin valide au début
    def test_path_exists_simple(self):
        player = self.game.players[0]
        self.assertTrue(self.game.has_path(player.pawn, player.id))

    # Ajoute deux murs, mais vérifie qu’un chemin reste ouvert
    def test_path_blocked_by_wall(self):
        wall1 = Wall(position=Position(x=3, y=0), orientation="horizontal")
        wall2 = Wall(position=Position(x=4, y=0), orientation="horizontal")
        self.game.walls.extend([wall1, wall2])
        player = self.game.players[0]
        self.assertTrue(self.game.has_path(player.pawn, player.id))  # doit toujours pouvoir atteindre y=8

    # Teste que l’IA random peut jouer un coup sans lever d’exception
    def test_ai_move_random(self):
        game_state = self.game.get_game_state()
        try:
            self.game.ai_move_random(game_state)
        except Exception:
            self.fail("ai_move_random() raised Exception unexpectedly!")

    # Vérifie que A* retourne une distance > 0 depuis la position actuelle du joueur
    def test_a_star_path_length(self):
        player = self.game.players[0]
        game_state = self.game.get_game_state()
        path_len = self.game.a_star(player, game_state)
        self.assertGreater(path_len, 0)

    # Vérifie que la fonction minimax retourne une valeur numérique
    def test_minimax_returns_value(self):
        val = self.game.minimax_ab(depth=1, alpha=-float("inf"), beta=float("inf"), maximizing=True)
        self.assertIsInstance(val, float)

    # Vérifie que l’évaluation de placement de mur retourne un Wall valide ou None
    def test_best_wall_placement(self):
        game_state = self.game.get_game_state()
        player = self.game.players[0]
        opponent = self.game.players[1]
        score, wall = self.game.evaluate_best_wall_placement(player, opponent, game_state)
        self.assertTrue(wall is None or isinstance(wall, Wall))

    # Vérifie que le joueur a gagné en atteignant la ligne opposée
    def test_player_victory(self):
        """ Teste si le joueur gagne en atteignant la ligne opposée"""
        self.game.players[0].pawn = Position(x=4, y=8)
        self.assertTrue(self.game.has_won(self.game.players[0]))


        # Tests + poussés 

    
    #______________________________________________________
    # test des placement des murs
    def test_blocking_wall_rejected(self):
        """ Vérifie qu’un mur est rejeté s’il bloque tous les chemins"""
        self.game.players[0].pawn = Position(x=4, y=2)
        self.game.players[1].pawn = Position(x=4, y=8)
        self.game.walls.extend([
            Wall(position=Position(x=3, y=2), orientation="vertical"),
            Wall(position=Position(x=4, y=1), orientation="horizontal"),
            Wall(position=Position(x=4, y=2), orientation="horizontal"),
        ])
        wall = Wall(position=Position(x=4, y=2), orientation="horizontal")
        print(" Vérifie qu un mur est rejeté s il bloque tous les chemins")
        self.game.print_board()
        with self.assertRaises(Exception):
            self.game.place_wall(1, wall.model_dump())

    
    
    def test_invalid_wall_orientation(self):
        """ Teste qu un mur avec une orientation invalide est rejeté"""
        wall = Wall(position=Position(x=2, y=2), orientation="diagonal")
        print("Teste qu un saut diagonal est bloqué si un mur est en diagonale")
        self.game.print_board()
        self.assertFalse(self.game.is_valid_wall(wall))


    # Tester si un chemin existe toujours 
    def test_wall_block_path_but_not_entirely(self):
        """ Teste qu un mur bloque partiellement mais qu’un chemin alternatif existe"""
        self.game.walls.extend([
            Wall(position=Position(x=4, y=0), orientation="horizontal"),
            Wall(position=Position(x=3, y=0), orientation="horizontal"),
        ])
        print("Teste qu un mur bloque partiellement mais qu’un chemin alternatif existe")
        self.game.print_board()
        self.assertTrue(self.game.has_path(self.game.players[0].pawn, self.game.players[0].id))


    #_______________________________________________________
    # Tests des déplacements 
    def test_move_invalid_outside_board(self):
        """Teste qu’un déplacement en dehors de la grille échoue"""
        with self.assertRaises(Exception):
            self.game.move_pawn(1, {"x": -1, "y": 0})

    # en diagonale/ saut 

    def test_no_jump_blocked(self):
        """Teste qu un saut direct est bloqué par un mur, on saute pas"""
        self.game.players[0].pawn = Position(x=4, y=4)
        self.game.players[1].pawn = Position(x=4, y=5)
        self.game.walls.append(Wall(position=Position(x=4, y=5), orientation="horizontal"))
        print("Teste qu un saut direct est bloqué par un mur")
        self.game.print_board()
        self.assertFalse(self.game.is_valid_face_to_face_move(self.game.players[0], Position(x=4, y=6)))

    
    def test_diagonal_jump_blocked_by_wall(self):
        """Teste qu un saut diagonal est bloqué si un mur est en diagonale"""
        self.game.players[0].pawn = Position(x=4, y=4)
        self.game.players[1].pawn = Position(x=4, y=5)
        self.game.walls.append(Wall(position=Position(x=5, y=4), orientation="vertical"))
        self.game.walls.append(Wall(position=Position(x=4, y=5), orientation="horizontal"))
        print("Teste qu un saut diagonal est bloqué si un mur est en diagonale")
        self.game.print_board()
        self.assertFalse(self.game.is_valid_face_to_face_move(self.game.players[0], Position(x=5, y=5)))


    # Test de A* : 
    def test_a_star_inf_when_blocked(self):
        """ Teste que A* retourne ∞ quand aucun chemin n est possible"""
        for i in range(0, 8, 2):
            self.game.walls.append(Wall(position=Position(x=i, y=0), orientation="horizontal"))

        self.game.walls.append( Wall(position=Position(x=7, y=0), orientation="vertical"))
        print("Teste que A* retourne ∞ quand aucun chemin n est possible")
        self.game.print_board()
        self.assertEqual(self.game.a_star(self.game.players[0], self.game.get_game_state()), float("inf"))

    def test_evaluate_state_returns_number(self):
        """ Vérifie que la fonction d évaluation retourne une valeur numérique"""
        score = self.game.evaluate_state()
        self.assertIsInstance(score, float)
    
    #cas simple sans mur 

    def test_a_star_path(self):

        print("\nTest : A* retourne une distance > 0")
        player = self.game.players[0]
        game_state = self.game.get_game_state()
        distance = self.game.a_star(player, game_state)
        self.game.print_board()
        print("Distance trouvée : ", distance)
        self.assertGreater(distance, 0)


    # avec des murs 
    def test_a_star_path_with_obstacles(self):
        print("\nTest : A* retourne une distance > 0 avec des murs complexes")

        # Position initiale du joueur
        self.game.players[0].pawn = Position(x=4, y=0)

        # Placer une série de murs pour forcer A* à faire des détours
        self.game.walls.extend([
            Wall(position=Position(x=4, y=0), orientation="horizontal"),
            Wall(position=Position(x=4, y=1), orientation="horizontal"),
            Wall(position=Position(x=3, y=2), orientation="vertical"),
            Wall(position=Position(x=5, y=2), orientation="vertical"),
            Wall(position=Position(x=3, y=3), orientation="horizontal"),
            Wall(position=Position(x=4, y=3), orientation="horizontal"),
            Wall(position=Position(x=2, y=4), orientation="vertical"),
            Wall(position=Position(x=6, y=4), orientation="vertical"),
            Wall(position=Position(x=2, y=5), orientation="horizontal"),
            Wall(position=Position(x=5, y=5), orientation="horizontal"),
        ])


        # Calcul de la distance avec A*
        player = self.game.players[0]
        game_state = self.game.get_game_state()
        distance = self.game.a_star(player, game_state)

        # Affichage pour visualisation
        self.game.print_board()
        print("Distance trouvée :", distance)

        # Le chemin doit exister et avoir une distance raisonnable (> 0)
        self.assertGreater(distance, 0)
        self.assertNotEqual(distance, float("inf"))


    # Les tests pour 4 joueurs 

    def test_four_players_start_position(self):
        """Vérifie la position de départ correcte pour 4 joueurs"""
        game = QuoridorGame(num_players=4)
        expected = [(4, 0), (4, 8), (0, 4), (8, 4)]
        result = [(p.pawn.x, p.pawn.y) for p in game.players]
        print("Vérifie la position de départ correcte pour 4 joueurs")
        self.game.print_board()
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()



#python -m unittest Quoridor_backend/app/models/test_quoridor.py