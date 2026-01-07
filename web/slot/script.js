const DATA_URL = "/api/games/slot/spin";
const tg = window.Telegram.WebApp;

// Initialize
tg.ready();
tg.expand();

// UI Elements
const balanceDisplay = document.getElementById("balance");
const reel1 = document.querySelector("#reel1 .symbol");
const reel2 = document.querySelector("#reel2 .symbol");
const reel3 = document.querySelector("#reel3 .symbol");
const spinBtn = document.getElementById("spin-btn");
const statusText = document.getElementById("status");
const betBtns = document.querySelectorAll(".bet-btn");

let currentBet = 100;
let isSpinning = false;
let userBalance = 0; // Will be fetched

// Symbols for animation
const symbols = ["🍒", "🍋", "🍇", "💎", "7️⃣", "🔔", "🍊", "⭐"];

// Setup
function init() {
    // Theme matching
    document.body.style.backgroundColor = tg.themeParams.bg_color || "#0f0f1b";

    // Check auth
    if (!tg.initData) {
        statusText.innerText = "❌ No Telegram Data";
        spinBtn.disabled = true;
        return;
    }

    // We assume user has some balance, or we fetch it?
    // In this simple MVP, we see balance only after first spin OR we need a "getUserInfo" api.
    // For now, let's just show "???" or wait for interaction.
    // Or we can fetch balance on load if we implement GET /api/user/balance.
    // Let's just say "Ready" and update after spin.
    balanceDisplay.innerText = "---";
}

// Bet Selection
betBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        if (isSpinning) return;
        betBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentBet = parseInt(btn.dataset.amount);
    });
});

// Spin Logic
spinBtn.addEventListener("click", async () => {
    if (isSpinning) return;

    startSpin();

    try {
        const response = await fetch(DATA_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                initData: tg.initData,
                bet: currentBet
            })
        });

        const data = await response.json();

        // Ensure animation runs for at least 1 second for effect
        setTimeout(() => {
            stopSpin(data);
        }, 1000);

    } catch (e) {
        console.error(e);
        // Show detailed error if possible
        let errMsg = "Network Error";
        if (e && e.message) errMsg = e.message;

        stopSpin({ success: false, error: errMsg });
    }
});

let spinIntervals = [];

function startSpin() {
    isSpinning = true;
    spinBtn.disabled = true;
    statusText.innerText = "Rolling...";
    statusText.className = "status-text";

    // Clear previous win effects
    [reel1, reel2, reel3].forEach(el => el.parentElement.classList.remove("win-anim"));

    // Start random symbol cycling
    spinIntervals = [reel1, reel2, reel3].map((el, i) => {
        return setInterval(() => {
            el.innerText = symbols[Math.floor(Math.random() * symbols.length)];
        }, 80 + (i * 20)); // Stagger slightly
    });

    document.querySelectorAll(".reel").forEach(el => el.classList.add("spinning"));
}

function stopSpin(data) {
    // Clear intervals
    spinIntervals.forEach(clearInterval);
    spinIntervals = [];
    document.querySelectorAll(".reel").forEach(el => el.classList.remove("spinning"));

    isSpinning = false;
    spinBtn.disabled = false;

    if (!data.success) {
        statusText.innerText = "❌ " + (data.error || "Error");
        if (data.balance !== undefined) {
            balanceDisplay.innerText = data.balance;
            userBalance = data.balance;
        }
        return;
    }

    // Set final symbols
    reel1.innerText = data.result[0];
    reel2.innerText = data.result[1];
    reel3.innerText = data.result[2];

    // Update balance
    balanceDisplay.innerText = data.new_balance;
    userBalance = data.new_balance;

    if (data.is_win) {
        statusText.innerText = `🎉 WON ${data.win_amount}!`;
        statusText.classList.add("neon-text");

        // Add win effect
        [reel1, reel2, reel3].forEach(el => el.parentElement.classList.add("win-anim"));

        // Haptic Feedback
        if (tg.HapticFeedback) {
            tg.HapticFeedback.notificationOccurred('success');
        }
    } else {
        statusText.innerText = "Try Again!";
    }
}

init();
