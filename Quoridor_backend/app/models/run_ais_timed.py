# run_ais_timed.py

import time
from Quoridor_backend.app.models.game import QuoridorGame, play_ai_turn
from Quoridor_backend.app.schemas.game_schema import Position, Wall, GameState, Player

import inspect


def simulate_with_timing_and_display(
    difficulty_p1="a_star",
    difficulty_p2="minmax",
    nb_games=10,
    max_turns=200
):
    """
    Simule nb_games parties en mesurant :
      - durée de chaque partie,
      - temps total et moyen de réflexion par coup pour chaque IA,
      - comptabilise victoires et matchs nuls,
    et affiche le plateau après chaque coup.
    """
    total_durations = []
    ia_times   = {1: 0.0, 2: 0.0}
    ia_moves   = {1:   0, 2:   0}
    wins_p1    = 0
    wins_p2    = 0
    draws      = 0

    for game_idx in range(1, nb_games + 1):
        game = QuoridorGame()

    
        start_game = time.perf_counter()
        turn_count = 0




        print(f"\n=== Début de la partie {game_idx}/{nb_games} ===")
       
        game.print_board()  # état initial

        while not game.game_over and turn_count < max_turns:
            curr_id = game.current_turn

            # Mesure du temps de réflexion
            t0 = time.perf_counter()
            play_ai_turn(
                game,
                difficulty=(difficulty_p1 if curr_id == 1 else difficulty_p2)
            )
            dt = time.perf_counter() - t0

            ia_times[curr_id] += dt
            ia_moves[curr_id] += 1
            turn_count += 1

            print(f"\nTour {turn_count} – Joueur {curr_id} a joué (temps : {dt:.4f}s)")
            game.print_board()

        # Fin de partie
        duration = time.perf_counter() - start_game
        total_durations.append(duration)
        winner = game.winner_id
        if winner == 1:
            wins_p1 += 1
        elif winner == 2:
            wins_p2 += 1
        else:
            draws += 1

        print(f"\n>>> Fin partie {game_idx} en {duration:.3f}s, tours : {turn_count}, gagnant : {winner or 'Aucun'}")

    # Bilan global
    avg_game = sum(total_durations) / len(total_durations)
    print("\n=== Résultats globaux ===")
    print(f"Nombre de parties       : {nb_games}")
    print(f"Durée moyenne par partie: {avg_game:.3f}s")

    for pid in (1, 2):
        avg_move = ia_times[pid] / ia_moves[pid] if ia_moves[pid] else 0.0
        lvl = difficulty_p1 if pid == 1 else difficulty_p2
        print(f"IA {pid} ({lvl}) – Coups joués : {ia_moves[pid]}, "
              f"temps total : {ia_times[pid]:.3f}s, "
              f"moyenne : {avg_move:.4f}s/coup")

    print(f"\nAprès {nb_games} parties :")
    print(f"IA 1 ({difficulty_p1}) : {wins_p1} victoires "
          f"({wins_p1/nb_games*100:.1f}%)")
    print(f"IA 2 ({difficulty_p2}) : {wins_p2} victoires "
          f"({wins_p2/nb_games*100:.1f}%)")
    print(f"Matchs nuls : {draws} "
          f"({draws/nb_games*100:.1f}%)")


if __name__ == "__main__":
    # Paramètres personnalisables
    lvl1 = "a_star"
    lvl2 = "minmax"
    games = 5
    
    print(f"Simulation de {games} parties — P1={lvl1} vs P2={lvl2}")
    simulate_with_timing_and_display(
        difficulty_p1=lvl1,
        difficulty_p2=lvl2,
        nb_games=games
    )
