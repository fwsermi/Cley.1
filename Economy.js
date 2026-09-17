
"use strict";

const fs = require("fs");
const path = require("path");
const sqlite3 = require("sqlite3").verbose();

// ============================================================
// CONFIG
// ============================================================

const DATA_DIR =
  process.env.CLEYDO_DATA_DIR ||
  path.join(__dirname, "data");

const DB_FILE =
  process.env.CLEYDO_DB_FILE ||
  path.join(DATA_DIR, "cleydo.db");

const DAILY_REWARD = 500;
const DAILY_COOLDOWN_MS = 24 * 60 * 60 * 1000;

// ============================================================
// DATABASE SETUP
// ============================================================

fs.mkdirSync(DATA_DIR, {
  recursive: true,
});

const db = new sqlite3.Database(DB_FILE);

db.serialize(() => {
  db.run(`
    PRAGMA journal_mode = WAL;
  `);

  db.run(`
    PRAGMA busy_timeout = 5000;
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS users (
      user_id TEXT PRIMARY KEY,
      wallet INTEGER NOT NULL DEFAULT 0,
      bank INTEGER NOT NULL DEFAULT 0,
      last_daily INTEGER NOT NULL DEFAULT 0
    );
  `);
});

// ============================================================
// DATABASE HELPERS
// ============================================================

function run(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (error) {
      if (error) {
        reject(error);
        return;
      }

      resolve({
        lastID: this.lastID,
        changes: this.changes,
      });
    });
  });
}

function get(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (error, row) => {
      if (error) {
        reject(error);
        return;
      }

      resolve(row);
    });
  });
}

// ============================================================
// USER INITIALIZATION
// ============================================================

async function ensureUser(userID) {
  const id = String(userID);

  await run(
    `
      INSERT OR IGNORE INTO users (
        user_id,
        wallet,
        bank,
        last_daily
      )
      VALUES (?, 0, 0, 0)
    `,
    [id]
  );

  return get(
    `
      SELECT
        user_id,
        wallet,
        bank,
        last_daily
      FROM users
      WHERE user_id = ?
    `,
    [id]
  );
}

// ============================================================
// BALANCE
// ============================================================

async function getBalance(userID) {
  const user = await ensureUser(userID);

  return {
    wallet: Number(user.wallet),
    bank: Number(user.bank),
    total:
      Number(user.wallet) +
      Number(user.bank),
  };
}

// ============================================================
// ADD MONEY
// ============================================================

async function addMoney(userID, amount) {
  const id = String(userID);
  const value = Number(amount);

  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(
      "Amount must be a positive number."
    );
  }

  const money = Math.floor(value);

  await ensureUser(id);

  await run(
    `
      UPDATE users
      SET wallet = wallet + ?
      WHERE user_id = ?
    `,
    [money, id]
  );

  return getBalance(id);
}

// ============================================================
// REMOVE MONEY
// ============================================================

async function removeMoney(userID, amount) {
  const id = String(userID);
  const value = Number(amount);

  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(
      "Amount must be a positive number."
    );
  }

  const money = Math.floor(value);

  await ensureUser(id);

  await run("BEGIN IMMEDIATE TRANSACTION");

  try {
    const user = await get(
      `
        SELECT wallet
        FROM users
        WHERE user_id = ?
      `,
      [id]
    );

    if (!user) {
      throw new Error(
        "User does not exist."
      );
    }

    if (Number(user.wallet) < money) {
      throw new Error(
        "Insufficient wallet balance."
      );
    }

    await run(
      `
        UPDATE users
        SET wallet = wallet - ?
        WHERE user_id = ?
      `,
      [money, id]
    );

    await run("COMMIT");

    return getBalance(id);
  } catch (error) {
    try {
      await run("ROLLBACK");
    } catch (_) {
      // Ignore rollback errors.
    }

    throw error;
  }
}

// ============================================================
// DEPOSIT
// ============================================================

async function deposit(userID, amount) {
  const id = String(userID);
  const value = Number(amount);

  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(
      "Amount must be a positive number."
    );
  }

  const money = Math.floor(value);

  await ensureUser(id);

  await run("BEGIN IMMEDIATE TRANSACTION");

  try {
    const user = await get(
      `
        SELECT wallet
        FROM users
   
