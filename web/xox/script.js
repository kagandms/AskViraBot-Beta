// Telegram WebApp Init
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Game State
let board = ['', '', '', '', '', '', '', '', ''];
let currentPlayer = 'X'; // Player is always X
let difficulty = 'easy';
let gameActive = false;
let stats = { wins: 0, draws: 0, losses: 0 };

// DOM Elements
const cells = document.querySelectorAll('.cell');
const difficultyBtns = document.querySelectorAll('.diff-btn');
const playerTurnEl = document.getElementById('playerTurn');
const gameOverEl = document.getElementById('gameOver');
const resultMessageEl = document.getElementById('resultMessage');
const newGameBtn = document.getElementById('newGameBtn');
const winsEl = document.getElementById('wins');
const drawsEl = document.getElementById('draws');
const lossesEl = document.getElementById('losses');

// Winning combinations
const winningCombinations = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8], // Columns
    [0, 4, 8], [2, 4, 6]              // Diagonals
];

// Initialize
function init() {
    // Set default difficulty to easy
    difficultyBtns[0].classList.add('active');

    // Event Listeners
    difficultyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (!gameActive) {
                selectDifficulty(btn.dataset.difficulty);
            }
        });
    });

    cells.forEach((cell, index) => {
        cell.addEventListener('click', () => handleCellClick(index));
    });

    newGameBtn.addEventListener('click', resetGame);
}

function selectDifficulty(level) {
    difficulty = level;
    difficultyBtns.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function handleCellClick(index) {
    if (!gameActive || board[index] !== '' || currentPlayer !== 'X') {
        return;
    }

    // Start game on first move
    if (board.every(cell => cell === '')) {
        gameActive = true;
        updateTurnDisplay();
    }

    // Player move
    makeMove(index, 'X');

    // Check game state
    const result = checkWinner();
    if (result) {
        endGame(result);
        return;
    }

    // Bot move
    currentPlayer = 'O';
    updateTurnDisplay();

    setTimeout(() => {
        const botMove = getBotMove();
        if (botMove !== null) {
            makeMove(botMove, 'O');
            const result = checkWinner();
            if (result) {
                endGame(result);
            } else {
                currentPlayer = 'X';
                updateTurnDisplay();
            }
        }
    }, 500);
}

function makeMove(index, player) {
    board[index] = player;
    const cell = cells[index];
    cell.textContent = player === 'X' ? '❌' : '⭕';
    cell.classList.add('disabled');

    // Animate
    cell.style.transform = 'scale(1.2)';
    setTimeout(() => {
        cell.style.transform = 'scale(1)';
    }, 200);
}

function getBotMove() {
    const emptyIndices = board.map((cell, idx) => cell === '' ? idx : null).filter(idx => idx !== null);

    if (emptyIndices.length === 0) return null;

    // Difficulty-based AI
    if (difficulty === 'easy') {
        // 30% optimal, 70% random
        if (Math.random() < 0.3) {
            return getBestMove();
        }
        return emptyIndices[Math.floor(Math.random() * emptyIndices.length)];
    } else if (difficulty === 'medium') {
        // 60% optimal, 40% random
        if (Math.random() < 0.6) {
            return getBestMove();
        }
        return emptyIndices[Math.floor(Math.random() * emptyIndices.length)];
    } else {
        // Hard: Always optimal
        return getBestMove();
    }
}

function getBestMove() {
    let bestScore = -Infinity;
    let bestMove = null;

    for (let i = 0; i < 9; i++) {
        if (board[i] === '') {
            board[i] = 'O';
            const score = minimax(board, 0, false);
            board[i] = '';

            if (score > bestScore) {
                bestScore = score;
                bestMove = i;
            }
        }
    }

    return bestMove;
}

function minimax(board, depth, isMaximizing) {
    const result = checkWinner();

    if (result === 'O') return 10 - depth;
    if (result === 'X') return depth - 10;
    if (result === 'Draw') return 0;

    if (isMaximizing) {
        let bestScore = -Infinity;
        for (let i = 0; i < 9; i++) {
            if (board[i] === '') {
                board[i] = 'O';
                const score = minimax(board, depth + 1, false);
                board[i] = '';
                bestScore = Math.max(score, bestScore);
            }
        }
        return bestScore;
    } else {
        let bestScore = Infinity;
        for (let i = 0; i < 9; i++) {
            if (board[i] === '') {
                board[i] = 'X';
                const score = minimax(board, depth + 1, true);
                board[i] = '';
                bestScore = Math.min(score, bestScore);
            }
        }
        return bestScore;
    }
}

function checkWinner() {
    // Check winning combinations
    for (const combo of winningCombinations) {
        const [a, b, c] = combo;
        if (board[a] && board[a] === board[b] && board[a] === board[c]) {
            // Highlight winning cells
            cells[a].classList.add('winner');
            cells[b].classList.add('winner');
            cells[c].classList.add('winner');
            return board[a];
        }
    }

    // Check for draw
    if (board.every(cell => cell !== '')) {
        return 'Draw';
    }

    return null;
}

function updateTurnDisplay() {
    if (currentPlayer === 'X') {
        playerTurnEl.textContent = 'Your Turn';
    } else {
        playerTurnEl.textContent = 'Bot Thinking...';
    }
}

function endGame(result) {
    gameActive = false;

    let message = '';
    if (result === 'X') {
        message = '🎉 You Win!';
        stats.wins++;
        winsEl.textContent = `Wins: ${stats.wins}`;
    } else if (result === 'O') {
        message = '😢 You Lose!';
        stats.losses++;
        lossesEl.textContent = `Losses: ${stats.losses}`;
    } else {
        message = '🤝 Draw!';
        stats.draws++;
        drawsEl.textContent = `Draws: ${stats.draws}`;
    }

    resultMessageEl.textContent = message;
    gameOverEl.classList.add('show');

    // Send result to bot
    sendGameResult(result);
}

async function sendGameResult(result) {
    try {
        const response = await fetch('/api/games/xox/result', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                initData: tg.initData,
                winner: result,
                difficulty: difficulty
            })
        });

        const data = await response.json();
        if (!data.success) {
            console.error('Failed to save game result:', data.error);
        }
    } catch (error) {
        console.error('Error sending game result:', error);
    }
}

function resetGame() {
    board = ['', '', '', '', '', '', '', '', ''];
    currentPlayer = 'X';
    gameActive = false;

    cells.forEach(cell => {
        cell.textContent = '';
        cell.classList.remove('disabled', 'winner');
    });

    gameOverEl.classList.remove('show');
    playerTurnEl.textContent = 'Your Turn';
}

// Start
init();
