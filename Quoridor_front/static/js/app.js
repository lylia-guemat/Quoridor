document.addEventListener('DOMContentLoaded', () => {
    const BOARD_SIZE = 9;
    const gameBoard = document.getElementById('game-board');
    let selectedPawn = null;
    let gameState = null;

    let isVsAI = false;
    let gameMode = "2players";
    let aiLevel = "";

    if (window.APP_CONFIG) {
        // Si on a bien injecté APP_CONFIG (page IA)
        ({ isVsAI, gameMode, aiLevel } = window.APP_CONFIG);
      }

    // Initialisation du plateau et récupération du state
    createBoard();
    fetchGameState();

    // Bouton « Recommencer »
    document.getElementById('restart-btn').addEventListener('click', restartGame);
    document.getElementById('restart-btn2').addEventListener('click', restartGame);

    document.getElementById('rules-btn').addEventListener('click', () => {
        window.open('/rules', '_blank');
    });
    

    document.getElementById('stop-btn').addEventListener('click', () => {
        const mode = window.GAME_MODE || "2players";
        fetch(`/api/restart?mode=${mode}`, { method: 'POST' })
          .finally(() => window.location.href = '/');
    });
    

    function createBoard() {
        gameBoard.style.gridTemplateColumns = `repeat(${BOARD_SIZE * 2 - 1}, auto)`;
        for (let i = 0; i < BOARD_SIZE * 2 - 1; i++) {
            for (let j = 0; j < BOARD_SIZE * 2 - 1; j++) {
                const element = document.createElement('div');
                if (i % 2 === 0 && j % 2 === 0) {
                    // Case pour pions
                    element.className = 'cell';
                    element.dataset.row = i / 2;
                    element.dataset.col = j / 2;
                    element.addEventListener('click', handleCellClick);
                } else if (i % 2 === 1 && j % 2 === 1) {
                    // Intersection de murs
                    element.className = 'wall-intersection';
                } else {
                    // Espace pour mur
                    element.className = 'wall-space';
                    if (i % 2 === 1) element.classList.add('wall-horizontal-space');
                    else element.classList.add('wall-vertical-space');
                    element.dataset.row = Math.floor(i/2);
                    element.dataset.col = Math.floor(j/2);
                    element.dataset.orientation = (i % 2 === 1) ? 'h' : 'v';
                    element.addEventListener('click', handleWallClick);
                    element.addEventListener('mouseenter', showWallPreview);
                    element.addEventListener('mouseleave', hideWallPreview);
                }
                gameBoard.appendChild(element);
            }
        }
    }

    function fetchGameState() {
        const mode = window.GAME_MODE || "2players";
        // On initialise la partie côté serveur
        fetch(`/api/restart?mode=${mode}`, { method: 'POST' })
          .then(res => res.json())
          .then(state => {
            gameState = state;
            updateBoard();
            updateUI();
          })
          .catch(err => console.error("Erreur init game:", err));
      }      
      

    function updateBoard() {
        // Efface pions et surlignages
        document.querySelectorAll('.cell').forEach(cell => {
            cell.classList.remove('player1','player2','selected','valid-move');
            cell.innerHTML = '';
        });
        // Efface murs
        document.querySelectorAll('.wall-space').forEach(w => {
            w.classList.remove('wall-active','wall-preview');
        });

        // Affiche les pions depuis gameState.players
        gameState.players.forEach(player => {
            const { x, y } = player.pawn;
            const cell = document.querySelector(`.cell[data-row="${y}"][data-col="${x}"]`);
            if (cell) {
                cell.classList.add(`player${player.id}`);
                const pawn = document.createElement('div');
                pawn.className = `pawn player${player.id}`;
                cell.appendChild(pawn);
            }
        });

        // Affiche les murs depuis gameState.walls
        gameState.walls.forEach(wall => {
            const { x, y } = wall.position;
            const sel = wall.orientation === 'horizontal'
                ? `.wall-horizontal-space[data-row="${y}"][data-col="${x}"]`
                : `.wall-vertical-space[data-row="${y}"][data-col="${x}"]`;
            const we = document.querySelector(sel);
            if (we) we.classList.add('wall-active');
        });

        // Surlignage des déplacements possibles
        if (selectedPawn) {
            showValidMoves(selectedPawn.row, selectedPawn.col);
        }
    }

    function updateUI() {
        // Murs restants
        gameState.players.forEach(player => {
            const el = document.getElementById(`player${player.id}-walls`);
            if (el) el.textContent = player.remaining_walls;
        });
        // Tour actuel
        const curEl = document.getElementById('current-player');
        if (curEl) {
            curEl.textContent = `Joueur ${gameState.current_turn}`;
        }
        // Statut de fin de partie
        const status = document.getElementById('game-status');
        const popup = document.getElementById('game-over-popup');
        const winnerText = document.getElementById('winner-text');
        const restart_btn2 = document.getElementById('restart-btn2');

        if (gameState.game_over) {
            status.textContent = `Partie terminée ! Joueur ${gameState.winner_id} gagne !`;
            winnerText.textContent = `🏆 Joueur ${gameState.winner_id} a gagné !`;
            popup.classList.remove('hidden');
            if (restart_btn2) restart_btn2.classList.remove('hidden');
        } else {
            status.textContent = '';
            popup.classList.add('hidden');
            if (restart_btn2) restart_btn2.classList.add('hidden');
        }
    }

    // function showValidMoves(row, col) {
    //     if (gameState.game_over) return;
    //     document.querySelectorAll('.cell').forEach(c => c.classList.remove('valid-move'));
    //     const dirs = [[-1,0],[1,0],[0,-1],[0,1]];
    //     dirs.forEach(([dr,dc]) => {
    //         const nr = row + dr, nc = col + dc;
    //         if (nr >= 0 && nr < BOARD_SIZE && nc >= 0 && nc < BOARD_SIZE) {
    //             const c = document.querySelector(`.cell[data-row="${nr}"][data-col="${nc}"]`);
    //             if (c && !c.querySelector('.pawn')) c.classList.add('valid-move');
    //         }
    //     });
    // }

    function showValidMoves(row, col) {
        if (gameState.game_over) return;
    
        // 1) Supprime l’ancien surlignage
        document.querySelectorAll('.cell').forEach(c =>
            c.classList.remove('valid-move')
        );
    
        // 2) Appel au serveur qui utilise get_valid_pawn_moves
        fetch('/api/showValidMoves', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_id: gameState.current_turn })
        })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(moves => {
            // 3) Pour chaque position renvoyée, on ajoute la classe CSS
            moves.forEach(({ x, y }) => {
                const cell = document.querySelector(
                    `.cell[data-row="${y}"][data-col="${x}"]`
                );
                if (cell) cell.classList.add('valid-move');
            });
        })
        .catch(err => console.error("Erreur showValidMoves :", err));
    }
    

    function handleCellClick(e) {
        if (gameState.game_over) return;
        const cell = e.target.closest('.cell');
        if (!cell) return;
        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);
        // Sélection du pion
        if (gameState.players.find(p => p.id === gameState.current_turn)
            .pawn.x === col &&
            gameState.players.find(p => p.id === gameState.current_turn)
            .pawn.y === row
        ) {
            selectedPawn = { row, col };
            document.querySelectorAll('.cell').forEach(c => c.classList.remove('selected'));
            cell.classList.add('selected');
            showValidMoves(row, col);
        } else if (selectedPawn) {
            movePawn(row, col);
        }
    }

    function movePawn(row, col) {
        fetch(`/api/move?player_id=${gameState.current_turn}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                move_type: 'move',
                new_position: { x: col, y: row }
            })
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(err => { throw err; });
            }
            return res.json();
        })
        .then(res => {
            gameState = res;
            selectedPawn = null;
            updateBoard();
            updateUI();
            console.log(isVsAI);
            if (isVsAI && gameState.current_turn !== gameState.players[0].id) {
                setTimeout(makeAIMove, 500);
            }
        })
        .catch(err => {
            console.error("Erreur de déplacement :", err);
            showError(err.detail || "Déplacement invalide");
        });
    }
    

    function handleWallClick(e) {
        if (gameState.game_over) return;
        const ws = e.target;
        const row = parseInt(ws.dataset.row);
        const col = parseInt(ws.dataset.col);
        const ori = ws.dataset.orientation;
    
        fetch(`/api/move?player_id=${gameState.current_turn}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                move_type: 'wall',
                wall: {
                    position: { x: col, y: row },
                    orientation: ori === 'h' ? 'horizontal' : 'vertical'
                }
            })
        })
        .then(res => {
            if (!res.ok) {
                // Si erreur 400, on récupère le message et on le renvoie sous forme d’erreur JS
                return res.json().then(err => { throw err; });
            }
            return res.json();
        })
        .then(res => {
            gameState = res;
            updateBoard();
            updateUI();
            if (isVsAI && gameState.current_turn !== gameState.players[0].id) {
                setTimeout(makeAIMove, 500);
            }
        })
        .catch(err => {
            console.error("Erreur placement mur :", err);
            showError(err.detail || "Placement de mur invalide");
            updateBoard();
            updateUI();
        });
    }
    

    function makeAIMove() {
        // on récupère le niveau depuis la config
        const level = window.APP_CONFIG?.aiLevel || 'easy';
        fetch(`/api/ai_move?difficulty=${level}`, { method: 'POST' })
          .then(res => {
            if (!res.ok) {
              // gère l'erreur éventuelle
              return res.json().then(err => { throw err; });
            }
            return res.json();
          })
          .then(state => {
            // la réponse est directement le GameState
            gameState = state;
            updateBoard();
            updateUI();
          })
          .catch(err => {
            console.error("Erreur IA :", err);
            showError(err.detail || "Erreur IA");
          });
      }
      

    function showWallPreview(e) {
        const ws = e.target;
        if (!ws.classList.contains('wall-active')) {
            ws.classList.add('wall-preview');
        }
    }

    function hideWallPreview(e) {
        e.target.classList.remove('wall-preview');
    }

    function restartGame() {
        const mode = window.GAME_MODE || "2players";
        fetch(`/api/restart?mode=${mode}`, { method: "POST" })
          .then(res => res.json())
          .then(state => {
            gameState = state;
            selectedPawn = null;
            updateBoard();
            updateUI();
          });
      }

    function showError(message) {
        const errorDiv = document.getElementById('error-message');
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    
        // Cacher automatiquement après 3 secondes
        setTimeout(() => {
            errorDiv.classList.add('hidden');
        }, 3000);
    }
    
    
});