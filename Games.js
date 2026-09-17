
"use strict";

const {
  getBalance,
  addMoney,
  removeMoney,
  formatMoney,
} = require("./economy");

// ============================================================
// CONFIG
// ============================================================

const SESSION_TIMEOUT_MS =
  10 * 60 * 1000;

// Entry fees from the original Games.py
const BLACKJACK_ENTRY_FEE = 100;
const UNO_ENTRY_FEE = 50;

// Blackjack
const BLACKJACK_WIN_MULTIPLIER = 2;
const BLACKJACK_NATURAL_MULTIPLIER = 3;

// ============================================================
// SESSION STORAGE
// ============================================================

// Sessions live in RAM.
// They disappear if the bot restarts.
// Money remains persistent in SQLite.

const blackjackSessions = new Map();
const unoSessions = new Map();

// ============================================================
// CARD DECK
// ============================================================

const SUITS = [
  "♠",
  "♥",
  "♦",
  "♣",
];

const RANKS = [
  "A",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "10",
  "J",
  "Q",
  "K",
];

function createDeck() {
  const deck = [];

  for (const suit of SUITS) {
    for (const rank of RANKS) {
      deck.push({
        rank,
        suit,
      });
    }
  }

  return deck;
}

function shuffle(deck) {
  for (
    let i = deck.length - 1;
    i > 0;
    i--
  ) {
    const j =
      Math.floor(
        Math.random() * (i + 1)
      );

    [
      deck[i],
      deck[j],
    ] = [
      deck[j],
      deck[i],
    ];
  }

  return deck;
}

function drawCard(session) {
  if (
    !session.deck ||
    session.deck.length === 0
  ) {
    session.deck = shuffle(
      createDeck()
    );
  }

  return session.deck.pop();
}

// ============================================================
// BLACKJACK
// ============================================================

function cardValue(card) {
  if (card.rank === "A") {
    return 11;
  }

  if (
    ["K", "Q", "J"].includes(
      card.rank
    )
  ) {
    return 10;
  }

  return Number(card.rank);
}

function calculateHand(hand) {
  let total = 0;
  let aces = 0;

  for (const card of hand) {
    total += cardValue(card);

    if (card.rank === "A") {
      aces++;
    }
  }

  while (
    total > 21 &&
    aces > 0
  ) {
    total -= 10;
    aces--;
  }

  return total;
}

function isNaturalBlackjack(hand) {
  return (
    hand.length === 2 &&
    calculateHand(hand) === 21
  );
}

function formatCard(card) {
  return `${card.rank}${card.suit}`;
}

function formatHand(hand) {
  return hand
    .map(formatCard)
    .join(" ");
}

function getBlackjackKey(
  threadID,
  userID
) {
  return `${threadID}:${userID}`;
}

function cleanupExpiredBlackjackSessions() {
  const now = Date.now();

  for (
    const [
      key,
      session,
    ] of blackjackSessions
  ) {
    if (
      now - session.createdAt >
      SESSION_TIMEOUT_MS
    ) {
      blackjackSessions.delete(key);
    }
  }
}

async function startBlackjack(
  api,
  event,
  amount
) {
  const threadID =
    String(event.threadID);

  const userID =
    String(event.senderID);

  const key =
    getBlackjackKey(
      threadID,
      userID
    );

  cleanupExpiredBlackjackSessions();

  if (
    blackjackSessions.has(key)
  ) {
    await sendReply(
      api,
      threadID,
      [
        "🃏 You already have a Blackjack game.",
        "",
        "Use !hit or !stand.",
      ].join("\n")
    );

    return;
  }

  let bet = Number(amount);

  if (
    !Number.isFinite(bet) ||
    bet <= 0
  ) {
    bet =
      BLACKJACK_ENTRY_FEE;
  }

  bet = Math.floor(bet);

  const balance =
    await getBalance(userID);

  if (
    balance.wallet < bet
  ) {
    await sendReply(
      api,
      threadID,
      [
        "❌ Insufficient balance.",
        "",
        `Bet: ${formatMoney(bet)}`,
        `Wallet: ${formatMoney(balance.wallet)}`,
      ].join("\n")
    );

    return;
  }

  // Charge the bet before creating the game.
  await removeMoney(
    userID,
    bet
  );

  const deck =
    shuffle(createDeck());

  const session = {
    userID,
    threadID,
    deck,

    playerHand: [
      deck.pop(),
      deck.pop(),
    ],

    dealerHand: [
      deck.pop(),
      deck.pop(),
    ],

    bet,
    createdAt: Date.now(),
  };

  blackjackSessions.set(
    key,
    session
  );

  // Natural blackjack
  if (
    isNaturalBlackjack(
      session.playerHand
    )
  ) {
    const payout =
      bet *
      BLACKJACK_NATURAL_MULTIPLIER;

    await addMoney(
      userID,
      payout
    );

    blackjackSessions.delete(key);

    const balanceAfter =
      await getBalance(userID);

    await sendReply(
      api,
      threadID,
      [
        "🃏 BLACKJACK!",
        "",
        `Your hand: ${formatHand(session.playerHand)} = 21`,
        `Dealer: ${formatCard(session.dealerHand[0])} ${formatCard(session.dealerHand[1])}`,
        "",
        `🎉 Payout: ${formatMoney(p
