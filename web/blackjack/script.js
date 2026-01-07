// Telegram WebApp Init
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Card suits and values
const suits = ['♠', '♥', '♦', '♣'];
const values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];

// Game State
let balance = 0;
let currentBet = 0;
let deck = [];
let playerHand = [];
let dealerHand = [];
let gameActive = false;
let canDouble = false;

// DOM Elements
const balanceEl = document.getElementById('balance');
const currentBetEl = document.getElementById('currentBet');
const dealerScoreEl = document.getElementById('dealerScore');
const playerScoreEl = document.getElementById('playerScore');
const dealerCardsEl = document.getElementById('dealerCards');
const playerCardsEl = document.getElementById('playerCards');
const bettingAreaEl = document.getElementById('bettingArea');
const gameControlsEl = document.getElementById('gameControls');
const resultMessageEl = document.getElementById('resultMessage');
const continueBtn = document.getElementById('continueBtn');
const chips = document.querySelectorAll('.chip');
const clearBetBtn = document.getElementById('clearBet');
const dealBtn = document.getElementById('dealBtn');
const hitBtn = document.getElementById('hitBtn');
const standBtn = document.getElementById('standBtn');
const doubleBtn = document.getElementById('doubleBtn');

// Initialize
async function init() {
    await fetchBalance();
    setupEventListeners();
}

// Fetch user balance from server
async function fetchBalance() {
    try {
        const response = await fetch('/api/games/blackjack/balance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initData: tg.initData })
        });

        const data = await response.json();
        if (data.success) {
            balance = data.balance;
            updateBalance();
        } else {
            balanceEl.textContent = 'Error';
        }
    } catch (error) {
        console.error('Balance fetch error:', error);
        balanceEl.textContent = '1000'; // Fallback
        balance = 1000;
    }
}

// Event Listeners
function setupEventListeners() {
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const value = parseInt(chip.dataset.value);
            addBet(value);
        });
    });

    clearBetBtn.addEventListener('click', clearBet);
    dealBtn.addEventListener('click', startGame);
    hitBtn.addEventListener('click', hit);
    standBtn.addEventListener('click', stand);
    doubleBtn.addEventListener('click', doubleDown);
    continueBtn.addEventListener('click', resetForNewGame);
}

// Betting
function addBet(amount) {
    if (currentBet + amount <= balance) {
        currentBet += amount;
        updateBet();
    }
}

function clearBet() {
    currentBet = 0;
    updateBet();
}

function updateBet() {
    currentBetEl.textContent = currentBet;
    dealBtn.disabled = currentBet === 0;
}

function updateBalance() {
    balanceEl.textContent = balance;
}

// Deck Management
function createDeck() {
    const newDeck = [];
    for (let suit of suits) {
        for (let value of values) {
            newDeck.push({ value, suit });
        }
    }
    return shuffleDeck(newDeck);
}

function shuffleDeck(deck) {
    for (let i = deck.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [deck[i], deck[j]] = [deck[j], deck[i]];
    }
    return deck;
}

function drawCard() {
    return deck.pop();
}

// Card Value Calculation
function getCardValue(card) {
    if (card.value === 'A') return 11;
    if (['J', 'Q', 'K'].includes(card.value)) return 10;
    return parseInt(card.value);
}

function calculateHandValue(hand) {
    let value = 0;
    let aces = 0;

    for (let card of hand) {
        const cardVal = getCardValue(card);
        value += cardVal;
        if (card.value === 'A') aces++;
    }

    // Adjust for aces
    while (value > 21 && aces > 0) {
        value -= 10;
        aces--;
    }

    return value;
}

// UI Card Rendering
function renderCard(card, isHidden = false) {
    const cardEl = document.createElement('div');
    cardEl.className = 'card';

    if (isHidden) {
        cardEl.classList.add('card-back');
        return cardEl;
    }

    const isRed = card.suit === '♥' || card.suit === '♦';
    cardEl.classList.add(isRed ? 'red' : 'black');

    cardEl.innerHTML = `
        <div class="card-top">
            <div class="card-value">${card.value}</div>
            <div style="font-size: 1em;">${card.suit}</div>
        </div>
        <div class="card-suit">${card.suit}</div>
        <div class="card-bottom">
            <div class="card-value">${card.value}</div>
            <div style="font-size: 1em;">${card.suit}</div>
        </div>
    `;

    return cardEl;
}

function updateUI() {
    // Dealer cards
    dealerCardsEl.innerHTML = '';
    dealerHand.forEach((card, index) => {
        const isHidden = gameActive && index === 1; // Hide second card during game
        dealerCardsEl.appendChild(renderCard(card, isHidden));
    });

    // Player cards
    playerCardsEl.innerHTML = '';
    playerHand.forEach(card => {
        playerCardsEl.appendChild(renderCard(card));
    });

    // Scores
    const dealerValue = gameActive ? calculateHandValue([dealerHand[0]]) : calculateHandValue(dealerHand);
    const playerValue = calculateHandValue(playerHand);

    dealerScoreEl.textContent = gameActive ? `${dealerValue}` : dealerValue;
    playerScoreEl.textContent = playerValue;
}

// Game Flow
async function startGame() {
    if (currentBet === 0) return;
    if (currentBet > balance) {
        alert('Insufficient balance!');
        return;
    }

    // Deduct bet from balance
    balance -= currentBet;
    updateBalance();

    // Initialize game
    deck = createDeck();
    playerHand = [drawCard(), drawCard()];
    dealerHand = [drawCard(), drawCard()];
    gameActive = true;
    canDouble = true;

    // UI Updates
    bettingAreaEl.style.display = 'none';
    gameControlsEl.style.display = 'flex';
    resultMessageEl.classList.remove('show');
    resultMessageEl.textContent = '';

    updateUI();

    // Check for immediate blackjack
    const playerValue = calculateHandValue(playerHand);
    const dealerValue = calculateHandValue(dealerHand);

    if (playerValue === 21) {
        if (dealerValue === 21) {
            // Push
            endGame('push');
        } else {
            // Blackjack!
            endGame('blackjack');
        }
    }
}

function hit() {
    if (!gameActive) return;

    playerHand.push(drawCard());
    canDouble = false; // Can only double on first hit
    doubleBtn.disabled = true;

    updateUI();

    const playerValue = calculateHandValue(playerHand);
    if (playerValue > 21) {
        endGame('bust');
    } else if (playerValue === 21) {
        stand(); // Auto-stand on 21
    }
}

function stand() {
    if (!gameActive) return;

    gameActive = false;
    gameControlsEl.style.display = 'none';

    // Reveal dealer's hidden card
    updateUI();

    // Dealer draws until 17+
    setTimeout(() => {
        dealerPlay();
    }, 500);
}

function doubleDown() {
    if (!gameActive || !canDouble) return;
    if (currentBet > balance) {
        alert('Insufficient balance to double!');
        return;
    }

    // Double the bet
    balance -= currentBet;
    currentBet *= 2;
    updateBalance();
    updateBet();

    // Draw one card and stand
    playerHand.push(drawCard());
    updateUI();

    const playerValue = calculateHandValue(playerHand);
    if (playerValue > 21) {
        endGame('bust');
    } else {
        stand();
    }
}

function dealerPlay() {
    let dealerValue = calculateHandValue(dealerHand);

    const dealInterval = setInterval(() => {
        if (dealerValue < 17) {
            dealerHand.push(drawCard());
            updateUI();
            dealerValue = calculateHandValue(dealerHand);
        } else {
            clearInterval(dealInterval);
            setTimeout(() => {
                determineWinner();
            }, 500);
        }
    }, 800);
}

function determineWinner() {
    const playerValue = calculateHandValue(playerHand);
    const dealerValue = calculateHandValue(dealerHand);

    if (dealerValue > 21) {
        endGame('win'); // Dealer bust
    } else if (playerValue > dealerValue) {
        endGame('win');
    } else if (playerValue < dealerValue) {
        endGame('lose');
    } else {
        endGame('push');
    }
}

async function endGame(result) {
    gameActive = false;
    gameControlsEl.style.display = 'none';

    let winAmount = 0;
    let message = '';
    let messageClass = '';

    switch (result) {
        case 'blackjack':
            winAmount = Math.floor(currentBet * 2.5); // 3:2 payout
            message = '🎉 BLACKJACK! 🎰';
            messageClass = 'blackjack';
            break;
        case 'win':
            winAmount = currentBet * 2;
            message = '✅ You Win!';
            messageClass = 'win';
            break;
        case 'lose':
            winAmount = 0;
            message = '❌ Dealer Wins';
            messageClass = 'lose';
            break;
        case 'bust':
            winAmount = 0;
            message = '💥 BUST! You Lose';
            messageClass = 'lose';
            break;
        case 'push':
            winAmount = currentBet;
            message = '🤝 Push (Tie)';
            messageClass = 'push';
            break;
    }

    // Update balance
    balance += winAmount;
    updateBalance();

    // Show result
    resultMessageEl.textContent = message;
    resultMessageEl.className = `result-message show ${messageClass}`;
    continueBtn.style.display = 'block';

    // Update UI to show both hands fully
    updateUI();

    // Send result to server
    await sendGameResult(result, winAmount);
}

async function sendGameResult(result, winAmount) {
    try {
        const response = await fetch('/api/games/blackjack/result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                initData: tg.initData,
                result: result,
                betAmount: currentBet,
                winAmount: winAmount,
                playerScore: calculateHandValue(playerHand),
                dealerScore: calculateHandValue(dealerHand)
            })
        });

        const data = await response.json();
        if (!data.success) {
            console.error('Failed to save result:', data.error);
        }
    } catch (error) {
        console.error('Error sending result:', error);
    }
}

function resetForNewGame() {
    currentBet = 0;
    playerHand = [];
    dealerHand = [];
    deck = [];
    gameActive = false;
    canDouble = false;

    bettingAreaEl.style.display = 'block';
    gameControlsEl.style.display = 'none';
    continueBtn.style.display = 'none';
    resultMessageEl.classList.remove('show');

    dealerCardsEl.innerHTML = '';
    playerCardsEl.innerHTML = '';
    dealerScoreEl.textContent = '-';
    playerScoreEl.textContent = '-';
    currentBetEl.textContent = '0';
    dealBtn.disabled = true;
    doubleBtn.disabled = false;
}

// Start
init();
