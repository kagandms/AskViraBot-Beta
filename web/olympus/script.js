// Telegram WebApp Init
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Game Symbols (Gates of Olympus style)
const SYMBOLS = {
    // Low pay (gems)
    blue: { emoji: '💎', value: 1, color: '#00bfff' },
    green: { emoji: '💚', value: 1.2, color: '#00ff00' },
    purple: { emoji: '🔮', value: 1.5, color: '#9400d3' },
    red: { emoji: '❤️', value: 2, color: '#ff0000' },
    // High pay (items)
    ring: { emoji: '💍', value: 3, color: '#ffd700' },
    goblet: { emoji: '🏆', value: 4, color: '#ffd700' },
    hourglass: { emoji: '⏳', value: 5, color: '#ffd700' },
    crown: { emoji: '👑', value: 8, color: '#ffd700' },
    // Scatter (Zeus)
    scatter: { emoji: '⚡', value: 0, color: '#ffff00', isScatter: true }
};

const SYMBOL_KEYS = Object.keys(SYMBOLS);
const REGULAR_SYMBOLS = SYMBOL_KEYS.filter(k => !SYMBOLS[k].isScatter);

// Multipliers that can appear on symbols
const MULTIPLIERS = [2, 3, 4, 5, 8, 10, 15, 20, 25, 50, 100, 500, 1000];

// Game Configuration
const GRID_COLS = 6;
const GRID_ROWS = 5;
const SCATTER_FOR_FREE_SPINS = 4;
const FREE_SPINS_AMOUNT = 15;
const MIN_MATCH = 8; // Minimum symbols for a win

// Game State
let balance = 0;
let betAmount = 10;
let currentMultiplier = 1;
let totalWin = 0;
let isSpinning = false;
let grid = [];
let freeSpinsRemaining = 0;
let isAutoSpin = false;
let scatterCount = 0;

// Bet levels
const BET_LEVELS = [5, 10, 20, 50, 100, 200, 500];
let betIndex = 1;

// DOM Elements
const slotGrid = document.getElementById('slotGrid');
const balanceEl = document.getElementById('balance');
const winAmountEl = document.getElementById('winAmount');
const currentMultiplierEl = document.getElementById('currentMultiplier');
const multiplierDisplay = document.getElementById('multiplierDisplay');
const betAmountEl = document.getElementById('betAmount');
const spinBtn = document.getElementById('spinBtn');
const autoBtn = document.getElementById('autoBtn');
const betMinus = document.getElementById('betMinus');
const betPlus = document.getElementById('betPlus');
const bigWinOverlay = document.getElementById('bigWinOverlay');
const bigWinText = document.getElementById('bigWinText');
const bigWinAmount = document.getElementById('bigWinAmount');
const freeSpinsOverlay = document.getElementById('freeSpinsOverlay');
const freeSpinsCount = document.getElementById('freeSpinsCount');
const fsStartBtn = document.getElementById('fsStartBtn');
const fsCounter = document.getElementById('fsCounter');
const fsRemaining = document.getElementById('fsRemaining');
const scatterCountEl = document.getElementById('scatterCount');
const scatterNumEl = document.getElementById('scatterNum');
const lightning = document.getElementById('lightning');

// Initialize
async function init() {
    createGrid();
    await fetchBalance();
    setupEventListeners();
    updateUI();
}

function createGrid() {
    slotGrid.innerHTML = '';
    grid = [];

    for (let row = 0; row < GRID_ROWS; row++) {
        grid[row] = [];
        for (let col = 0; col < GRID_COLS; col++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.row = row;
            cell.dataset.col = col;

            // Random initial symbol
            const symbolKey = getRandomSymbol();
            grid[row][col] = { symbol: symbolKey, multiplier: null };
            cell.innerHTML = SYMBOLS[symbolKey].emoji;

            slotGrid.appendChild(cell);
        }
    }
}

function getRandomSymbol(includeScatter = true) {
    // Scatter has lower chance
    if (includeScatter && Math.random() < 0.02) {
        return 'scatter';
    }

    // Weighted random for regular symbols
    const weights = {
        blue: 20, green: 18, purple: 15, red: 12,
        ring: 8, goblet: 6, hourglass: 4, crown: 2
    };

    const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
    let random = Math.random() * totalWeight;

    for (const [symbol, weight] of Object.entries(weights)) {
        random -= weight;
        if (random <= 0) return symbol;
    }

    return 'blue';
}

function getRandomMultiplier() {
    // 15% chance for multiplier on a symbol
    if (Math.random() > 0.15) return null;

    // Weighted - higher multipliers are rarer
    const weights = [30, 25, 20, 15, 8, 5, 3, 2, 1, 0.5, 0.3, 0.1, 0.05];
    const totalWeight = weights.reduce((a, b) => a + b, 0);
    let random = Math.random() * totalWeight;

    for (let i = 0; i < weights.length; i++) {
        random -= weights[i];
        if (random <= 0) return MULTIPLIERS[i];
    }

    return MULTIPLIERS[0];
}

async function fetchBalance() {
    try {
        const response = await fetch('/api/games/olympus/balance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initData: tg.initData })
        });
        const data = await response.json();
        if (data.success) {
            balance = data.balance;
        } else {
            balance = 1000;
        }
    } catch (error) {
        console.error('Balance error:', error);
        balance = 1000;
    }
    updateUI();
}

function setupEventListeners() {
    spinBtn.addEventListener('click', spin);
    autoBtn.addEventListener('click', toggleAutoSpin);
    betMinus.addEventListener('click', decreaseBet);
    betPlus.addEventListener('click', increaseBet);
    fsStartBtn.addEventListener('click', startFreeSpins);
}

function updateUI() {
    balanceEl.textContent = balance.toLocaleString();
    betAmountEl.textContent = betAmount;
    winAmountEl.textContent = totalWin.toLocaleString();
    currentMultiplierEl.textContent = `x${currentMultiplier}`;

    if (freeSpinsRemaining > 0) {
        fsCounter.style.display = 'block';
        fsRemaining.textContent = freeSpinsRemaining;
    } else {
        fsCounter.style.display = 'none';
    }
}

function decreaseBet() {
    if (isSpinning || freeSpinsRemaining > 0) return;
    betIndex = Math.max(0, betIndex - 1);
    betAmount = BET_LEVELS[betIndex];
    updateUI();
}

function increaseBet() {
    if (isSpinning || freeSpinsRemaining > 0) return;
    betIndex = Math.min(BET_LEVELS.length - 1, betIndex + 1);
    betAmount = BET_LEVELS[betIndex];
    updateUI();
}

function toggleAutoSpin() {
    isAutoSpin = !isAutoSpin;
    autoBtn.classList.toggle('active', isAutoSpin);

    if (isAutoSpin && !isSpinning) {
        spin();
    }
}

async function spin() {
    if (isSpinning) return;

    // Check balance (free spins don't cost)
    if (freeSpinsRemaining === 0) {
        if (balance < betAmount) {
            alert('Insufficient balance!');
            isAutoSpin = false;
            autoBtn.classList.remove('active');
            return;
        }
        balance -= betAmount;
    } else {
        freeSpinsRemaining--;
    }

    isSpinning = true;
    spinBtn.disabled = true;
    totalWin = 0;
    currentMultiplier = 1;
    scatterCount = 0;
    scatterCountEl.style.display = 'none';

    updateUI();

    // Animate spin
    await animateSpin();

    // Check for wins (cascade loop)
    await checkWinsAndCascade();

    // Check for scatter bonus
    if (scatterCount >= SCATTER_FOR_FREE_SPINS && freeSpinsRemaining === 0) {
        await triggerFreeSpins();
    }

    // Show big win if applicable
    if (totalWin >= betAmount * 10) {
        await showBigWin();
    }

    // Update balance with wins
    balance += totalWin;

    isSpinning = false;
    spinBtn.disabled = false;
    updateUI();

    // Send result to server
    await sendResult();

    // Continue auto spin
    if (isAutoSpin && balance >= betAmount) {
        setTimeout(() => spin(), 1000);
    } else if (isAutoSpin) {
        isAutoSpin = false;
        autoBtn.classList.remove('active');
    }

    // Continue free spins
    if (freeSpinsRemaining > 0) {
        setTimeout(() => spin(), 1000);
    }
}

async function animateSpin() {
    const cells = document.querySelectorAll('.cell');

    // Flash lightning
    lightning.classList.add('flash');
    setTimeout(() => lightning.classList.remove('flash'), 100);

    // Spin animation
    cells.forEach(cell => cell.classList.add('spinning'));

    await sleep(300);

    // Generate new symbols
    for (let row = 0; row < GRID_ROWS; row++) {
        for (let col = 0; col < GRID_COLS; col++) {
            const symbolKey = getRandomSymbol();
            const multiplier = getRandomMultiplier();
            grid[row][col] = { symbol: symbolKey, multiplier };

            if (symbolKey === 'scatter') scatterCount++;
        }
    }

    // Show scatter count
    if (scatterCount > 0) {
        scatterCountEl.style.display = 'block';
        scatterNumEl.textContent = scatterCount;
    }

    // Reveal symbols
    cells.forEach((cell, index) => {
        cell.classList.remove('spinning');
        const row = Math.floor(index / GRID_COLS);
        const col = index % GRID_COLS;
        const { symbol, multiplier } = grid[row][col];

        cell.innerHTML = SYMBOLS[symbol].emoji;

        if (multiplier) {
            const bubble = document.createElement('div');
            bubble.className = 'multiplier-bubble';
            bubble.textContent = `x${multiplier}`;
            cell.appendChild(bubble);
        }
    });

    await sleep(200);
}

async function checkWinsAndCascade() {
    let hasWin = true;

    while (hasWin) {
        hasWin = false;

        // Count symbols
        const symbolCounts = {};
        const symbolPositions = {};

        for (let row = 0; row < GRID_ROWS; row++) {
            for (let col = 0; col < GRID_COLS; col++) {
                const { symbol } = grid[row][col];
                if (SYMBOLS[symbol].isScatter) continue;

                if (!symbolCounts[symbol]) {
                    symbolCounts[symbol] = 0;
                    symbolPositions[symbol] = [];
                }
                symbolCounts[symbol]++;
                symbolPositions[symbol].push({ row, col });
            }
        }

        // Check each symbol for wins
        for (const [symbol, count] of Object.entries(symbolCounts)) {
            if (count >= MIN_MATCH) {
                hasWin = true;

                // Calculate win
                let winMultiplier = 0;
                const positions = symbolPositions[symbol];

                // Highlight winning cells and collect multipliers
                const cells = document.querySelectorAll('.cell');
                for (const pos of positions) {
                    const cellIndex = pos.row * GRID_COLS + pos.col;
                    cells[cellIndex].classList.add('winning');

                    const { multiplier } = grid[pos.row][pos.col];
                    if (multiplier) {
                        winMultiplier += multiplier;
                    }
                }

                // Add to current multiplier
                if (winMultiplier > 0) {
                    currentMultiplier += winMultiplier;
                    updateUI();
                }

                // Calculate payout
                const baseWin = getPayoutForCount(count, SYMBOLS[symbol].value);
                const win = Math.floor(baseWin * betAmount * currentMultiplier);
                totalWin += win;

                winAmountEl.textContent = totalWin.toLocaleString();

                await sleep(500);

                // Cascade out
                for (const pos of positions) {
                    const cellIndex = pos.row * GRID_COLS + pos.col;
                    cells[cellIndex].classList.remove('winning');
                    cells[cellIndex].classList.add('cascade-out');
                    grid[pos.row][pos.col] = null;
                }

                await sleep(300);

                // Drop and fill
                await cascadeDown();

                break; // Recheck from start
            }
        }
    }
}

function getPayoutForCount(count, symbolValue) {
    // Payout table based on symbol count
    const payouts = {
        8: 0.5,
        9: 0.8,
        10: 1,
        11: 1.5,
        12: 2,
        13: 3,
        14: 5,
        15: 8
    };

    const multiplier = payouts[Math.min(count, 15)] || 0.5;
    return symbolValue * multiplier;
}

async function cascadeDown() {
    const cells = document.querySelectorAll('.cell');

    // For each column, drop symbols down
    for (let col = 0; col < GRID_COLS; col++) {
        // Collect non-null symbols from bottom to top
        const columnSymbols = [];
        for (let row = GRID_ROWS - 1; row >= 0; row--) {
            if (grid[row][col]) {
                columnSymbols.push(grid[row][col]);
            }
        }

        // Fill with new symbols from top
        while (columnSymbols.length < GRID_ROWS) {
            const symbolKey = getRandomSymbol();
            const multiplier = getRandomMultiplier();
            columnSymbols.push({ symbol: symbolKey, multiplier, isNew: true });

            if (symbolKey === 'scatter') scatterCount++;
        }

        // Place back (reversed, bottom to top)
        for (let row = GRID_ROWS - 1; row >= 0; row--) {
            const idx = GRID_ROWS - 1 - row;
            grid[row][col] = columnSymbols[idx];
        }
    }

    // Update scatter count
    if (scatterCount > 0) {
        scatterNumEl.textContent = scatterCount;
    }

    // Animate cascade in
    cells.forEach((cell, index) => {
        cell.classList.remove('cascade-out');
        const row = Math.floor(index / GRID_COLS);
        const col = index % GRID_COLS;
        const { symbol, multiplier, isNew } = grid[row][col];

        if (isNew) {
            cell.classList.add('cascade-in');
            setTimeout(() => cell.classList.remove('cascade-in'), 400);
        }

        cell.innerHTML = SYMBOLS[symbol].emoji;

        if (multiplier) {
            const bubble = document.createElement('div');
            bubble.className = 'multiplier-bubble';
            bubble.textContent = `x${multiplier}`;
            cell.appendChild(bubble);
        }

        grid[row][col].isNew = false;
    });

    await sleep(400);
}

async function triggerFreeSpins() {
    freeSpinsCount.textContent = FREE_SPINS_AMOUNT;
    freeSpinsOverlay.classList.add('show');

    // Wait for user to click start
    await new Promise(resolve => {
        fsStartBtn.onclick = resolve;
    });

    freeSpinsOverlay.classList.remove('show');
    freeSpinsRemaining = FREE_SPINS_AMOUNT;
    updateUI();
}

function startFreeSpins() {
    // Handled by promise in triggerFreeSpins
}

async function showBigWin() {
    let winType = 'BIG WIN!';
    if (totalWin >= betAmount * 50) winType = 'MEGA WIN!';
    if (totalWin >= betAmount * 100) winType = 'EPIC WIN!';
    if (totalWin >= betAmount * 500) winType = 'LEGENDARY!';

    bigWinText.textContent = winType;
    bigWinAmount.textContent = totalWin.toLocaleString();
    bigWinOverlay.classList.add('show');

    // Lightning effect
    for (let i = 0; i < 5; i++) {
        lightning.classList.add('flash');
        await sleep(100);
        lightning.classList.remove('flash');
        await sleep(100);
    }

    await sleep(2000);
    bigWinOverlay.classList.remove('show');
}

async function sendResult() {
    try {
        await fetch('/api/games/olympus/result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                initData: tg.initData,
                betAmount: betAmount,
                winAmount: totalWin,
                multiplier: currentMultiplier,
                freeSpins: freeSpinsRemaining > 0
            })
        });
    } catch (error) {
        console.error('Result send error:', error);
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Start
init();
