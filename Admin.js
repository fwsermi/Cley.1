
"use strict";

const {
  isAdmin,
} = require("./permissions");

const {
  addMoney,
  removeMoney,
  getBalance,
  formatMoney,
} = require("./economy");

// ============================================================
// CONFIG
// ============================================================

const BOT_STATE = {
  enabled: true,
};

// Threads currently known to the bot.
// index.js will register threads here.
const activeThreads = new Set();

// ============================================================
// THREAD REGISTRATION
// ============================================================

function registerThread(threadID) {
  if (!threadID) {
    return;
  }

  activeThreads.add(
    String(threadID)
  );
}

function unregisterThread(threadID) {
  if (!threadID) {
    return;
  }

  activeThreads.delete(
    String(threadID)
  );
}

function getActiveThreads() {
  return [
    ...activeThreads,
  ];
}

// ============================================================
// BOT STATE
// ============================================================

function isBotEnabled() {
  return BOT_STATE.enabled;
}

function setBotEnabled(enabled) {
  BOT_STATE.enabled =
    Boolean(enabled);

  return BOT_STATE.enabled;
}

// ============================================================
// SEND MESSAGE
// ============================================================

function sendMessage(
  api,
  threadID,
  message
) {
  return new Promise(
    (resolve) => {
      try {
        api.sendMessage(
          String(message),
          String(threadID),
          (error) => {
            if (error) {
              console.error(
                "[ADMIN] Send failed:",
                error
              );
            }

            resolve(
              !error
            );
          }
        );
      } catch (error) {
        console.error(
          "[ADMIN] Send error:",
          error
        );

        resolve(false);
      }
    }
  );
}

// ============================================================
// ANNOUNCE
// ============================================================

async function announce(
  api,
  message
) {
  const text =
    String(message || "")
      .trim();

  if (!text) {
    return {
      sent: 0,
      failed: 0,
    };
  }

  let sent = 0;
  let failed = 0;

  for (
    const threadID of activeThreads
  ) {
    const success =
      await sendMessage(
        api,
        threadID,
        [
          "📢 CLEYDO ANNOUNCEMENT",
          "",
          text,
        ].join("\n")
      );

    if (success) {
      sent++;
    } else {
      failed++;
    }
  }

  return {
    sent,
    failed,
  };
}

// ============================================================
// ADD MONEY
// ============================================================

async function adminAddMoney(
  api,
  event,
  targetID,
  amount
) {
  const threadID =
    String(event.threadID);

  const userID =
    String(event.senderID);

  if (!isAdmin(userID)) {
    await sendMessage(
      api,
      threadID,
      "❌ You don't have permission to use this command."
    );

    return true;
  }

  const target =
    String(targetID || "")
      .trim();

  const value =
    Number(amount);

  if (
    !target ||
    !Number.isFinite(value) ||
    value <= 0
  ) {
    await sendMessage(
      api,
      threadID,
      "Usage: !addmoney <user_id> <amount>"
    );

    return true;
  }

  const money =
    Math.floor(value);

  const balance =
    await addMoney(
      target,
      money
    );

  await sendMessage(
    api,
    threadID,
    [
      "💰 MONEY ADDED",
      "",
      `User: ${target}`,
      `Added: +${formatMoney(money)}`,
      `Wallet: ${formatMoney(balance.wallet)}`,
      `Total: ${formatMoney(balance.total)}`,
    ].join("\n")
  );

  return true;
}

// ============================================================
// REMOVE MONEY
// ============================================================

async function adminRemoveMoney(
  api,
  event,
  targetID,
  amount
) {
  const threadID =
    String(event.threadID);

  const userID =
    String(event.senderID);

  if (!isAdmin(userID)) {
    await sendMessage(
      api,
      threadID,
      "❌ You don't have permission to use this command."
    );

    return true;
  }

  const target =
    String(targetID || "")
      .trim();

  const value =
    Number(amount);

  if (
    !target ||
    !Number.isFinite(value) ||
    value <= 0
  ) {
    await sendMessage(
      api,
      threadID,
      "Usage: !removemoney <user_id> <amount>"
    );

    return true;
  }

  const money =
    Math.floor(value);

  try {
    const balance =
      await removeMoney(
        target,
        money
      );

    await sendMessage(
      api,
      threadID,
      [
        "💸 MONEY REMOVED",
        "",
        `User: ${target}`,
        `Removed: -${formatMoney(money)}`,
        `Wallet: ${formatMoney(balance.wallet)}`,
        `Total: ${formatMon
