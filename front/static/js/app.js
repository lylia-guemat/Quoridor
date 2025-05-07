
document.addEventListener('DOMContentLoaded', () => {
    const BOARD_SIZE = 9;
    const CELL_SIZE = 50;
    let selectedPawn = null;
    let gameState = null;
    const gameBoard = document.getElementById('game-board');
    
    // Initialize the game
    createBoard();
    fetchGameState();
    
    // Add event listener for restart button
    document.getElementById('restart-btn').addEventListener('click', restartGame);

    function createBoard() {
        gameBoard.style.gridTemplateColumns = `repeat(${BOARD_SIZE * 2 - 1}, auto)`;
        
        for (let i = 0; i < BOARD_SIZE * 2 - 1; i++) {
            for (let j = 0; j < BOARD_SIZE * 2 - 1; j++) {
                const element = document.createElement('div');
                
                if (i % 2 === 0 && j % 2 === 0) {
                    // Cell for pawns
                    element.className = 'cell';
                    element.dataset.row = i / 2;
                    element.dataset.col = j / 2;
                    element.addEventListener('click', handleCellClick);
                } else if (i % 2 === 1 && j % 2 === 1) {
                    // Wall intersection
                    element.className = 'wall-intersection';
                } else {
                    // Wall space
                    element.className = 'wall-space';
                    if (i % 2 === 1) {
                        element.classList.add('wall-horizontal-space');
                    } else {
                        element.classList.add('wall-vertical-space');
                    }
                    element.dataset.row = Math.floor(i/2);
                    element.dataset.col = Math.floor(j/2);
                    element.dataset.orientation = i % 2 === 1 ? 'h' : 'v';
                    element.addEventListener('click', handleWallClick);
                    element.addEventListener('mouseenter', showWallPreview);
                    element.addEventListener('mouseleave', hideWallPreview);
                }
                
                gameBoard.appendChild(element);
            }
        }
    }

    function fetchGameState() {
        fetch('/api/game/state')
            .then(response => response.json())
            .then(state => {
                gameState = state;
                updateBoard();
                updateUI();
            });
    }

    function updateBoard() {
        // Clear all cells and walls
        document.querySelectorAll('.cell').forEach(cell => {
            cell.classList.remove('player1', 'player2', 'selected', 'valid-move');
            cell.innerHTML = '';
        });
        
        document.querySelectorAll('.wall-space').forEach(wall => {
            wall.classList.remove('wall-active');
        });

        // Update pawns
        if (gameState.board) {
            for (let i = 0; i < BOARD_SIZE; i++) {
                for (let j = 0; j < BOARD_SIZE; j++) {
                    if (gameState.board[i][j] > 0) {
                        const cell = document.querySelector(`.cell[data-row="${i}"][data-col="${j}"]`);
                        if (cell) {
                            cell.classList.add(`player${gameState.board[i][j]}`);
                            const pawn = document.createElement('div');
                            pawn.className = `pawn player${gameState.board[i][j]}`;
                            cell.appendChild(pawn);
                        }
                    }
                }
            }
        }

        // Update walls
        if (gameState.horizontal_walls) {
            for (let i = 0; i < gameState.horizontal_walls.length; i++) {
                for (let j = 0; j < gameState.horizontal_walls[i].length; j++) {
                    if (gameState.horizontal_walls[i][j]) {
                        const wall = document.querySelector(`.wall-horizontal-space[data-row="${i}"][data-col="${j}"]`);
                        if (wall) wall.classList.add('wall-active');
                    }
                }
            }
        }

        if (gameState.vertical_walls) {
            for (let i = 0; i < gameState.vertical_walls.length; i++) {
                for (let j = 0; j < gameState.vertical_walls[i].length; j++) {
                    if (gameState.vertical_walls[i][j]) {
                        const wall = document.querySelector(`.wall-vertical-space[data-row="${i}"][data-col="${j}"]`);
                        if (wall) wall.classList.add('wall-active');
                    }
                }
            }
        }

        // Show valid moves if a pawn is selected
        if (selectedPawn) {
            showValidMoves(selectedPawn.row, selectedPawn.col);
        }
    }

    function updateUI() {
        document.getElementById('player1-walls').textContent = gameState.walls_remaining[1];
        document.getElementById('player2-walls').textContent = gameState.walls_remaining[2];
        document.getElementById('current-player').textContent = 
            gameState.current_player === 1 ? 'Joueur 1' : 'Ordinateur';
        
        const gameStatus = document.getElementById('game-status');
        if (gameState.game_over) {
            gameStatus.textContent = `Partie terminée ! ${gameState.winner === 1 ? 'Joueur 1' : 'Ordinateur'} gagne !`;
        } else {
            gameStatus.textContent = '';
        }
    }

    function showValidMoves(row, col) {
        // Clear previous highlights
        document.querySelectorAll('.cell').forEach(cell => {
            cell.classList.remove('valid-move');
        });

        // Show possible moves (adjacent cells)
        const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
        directions.forEach(([dr, dc]) => {
            const newRow = parseInt(row) + dr;
            const newCol = parseInt(col) + dc;
            if (newRow >= 0 && newRow < BOARD_SIZE && newCol >= 0 && newCol < BOARD_SIZE) {
                const cell = document.querySelector(`.cell[data-row="${newRow}"][data-col="${newCol}"]`);
                if (cell && !cell.querySelector('.pawn')) {
                    cell.classList.add('valid-move');
                }
            }
        });
    }

    function handleCellClick(event) {
        const cell = event.target.closest('.cell');
        if (!cell) return;

        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);

        if (gameState.board[row][col] === gameState.current_player) {
            // Select pawn
            selectedPawn = { row, col };
            document.querySelectorAll('.cell').forEach(c => c.classList.remove('selected'));
            cell.classList.add('selected');
            showValidMoves(row, col);
        } else if (selectedPawn) {
            // Move pawn
            movePawn(row, col);
        }
    }

    function movePawn(row, col) {
        fetch('/api/game/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'pawn', row, col })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                gameState = result.state;
                selectedPawn = null;
                updateBoard();
                updateUI();
                if (gameState.current_player === 2) {
                    setTimeout(makeAIMove, 500);
                }
            }
        });
    }

    function handleWallClick(event) {
        const wallSpace = event.target;
        const row = parseInt(wallSpace.dataset.row);
        const col = parseInt(wallSpace.dataset.col);
        const orientation = wallSpace.dataset.orientation;

        fetch('/api/game/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'wall', row, col, orientation })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                gameState = result.state;
                updateBoard();
                updateUI();
                if (gameState.current_player === 2) {
                    setTimeout(makeAIMove, 500);
                }
            }
        });
    }

    function makeAIMove() {
        fetch('/api/game/ai-move', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                gameState = result.state;
                updateBoard();
                updateUI();
            }
        });
    }

    function showWallPreview(event) {
        const wallSpace = event.target;
        if (!wallSpace.classList.contains('wall-active')) {
            wallSpace.classList.add('wall-preview');
        }
    }

    function hideWallPreview(event) {
        const wallSpace = event.target;
        wallSpace.classList.remove('wall-preview');
    }

    function restartGame() {
        fetch('/api/game/restart', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                gameState = result.state;
                selectedPawn = null;
                updateBoard();
                updateUI();
            }
        });
    }
});
