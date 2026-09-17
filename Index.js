"use strict";

const express = require("express");
const { login } = require("ws3-fca");

const {
  handleEconomyCommand,
} = require("./economy");

const {
  handleGamesCommand,
  handleGameResponse,
} = require("./games");

const {
  handleActionCommand,
} = require("./actions");

const {
  handleAdminCommand,
  registerThread,
  isBotEnabled,
} = require("./admin");


// =========================================================
// CONFIG
// =========================================================

const PORT = Number(process.env.PORT || 10000);

const BOT_PREFIX = "!";

const ADMIN_IDS = String(
  process.env.ADMIN_IDS || ""
)
  .split(",")
  .map((id) => id.trim())
  .filter(Boolean);


// =========================================================
// EXPRESS
// =========================================================

const app = express();

app.use(express.json());

app.get("/", (req, res) => {
  res.status(200).send("🐈‍⬛ Cleydo is online.");
});

app.get("/health", (req, res) => {
  res.status(200).json({
    status: "online",
    bot: "Cleydo",
  });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(
    `[Cleydo] Web server listening on port ${PORT}`
  );
});


// =========================================================
// HELPERS
// =========================================================

function isAdmin(userID) {
  return ADMIN_IDS.includes(String(userID));
}


function send(api, threadID, message) {
  return new Promise((resolve) => {
    try {
      api.sendMessage(
        String(message),
        threadID,
        (error) => {
          if (error) {
            console.error(
              "[Cleydo] sendMessage error:",
              error
            );

            resolve(false);
            return;
          }

          resolve(true);
        }
      );
    } catch (error) {
      console.error(
        "[Cleydo] Failed to send message:",
        error
      );

      resolve(false);
    }
  });
}


// =========================================================
// APPSTATE / FACEBOOK SESSION
// =========================================================

function readAppState() {
  const raw = String(
    process.env.FB_COOKIES || ""
  ).trim();

  if (!raw) {
    throw new Error(
      "FB_COOKIES environment variable is missing."
    );
  }

  let parsed;

  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    throw new Error(
      "FB_COOKIES is not valid JSON."
    );
  }

  // Support accidentally double-encoded JSON.
  if (typeof parsed === "string") {
    try {
      parsed = JSON.parse(parsed);
    } catch (error) {
      throw new Error(
        "FB_COOKIES contains invalid encoded JSON."
      );
    }
  }

  if (!Array.isArray(parsed)) {
    throw new Error(
      "FB_COOKIES must contain a JSON array."
    );
  }

  const appState = parsed
    .map((cookie) => {
      if (!cookie || typeof cookie !== "object") {
        return null;
      }

      const name =
        cookie.key ||
        cookie.name;

      const value =
        cookie.value;

      if (
        typeof name !== "string" ||
        !name.trim()
      ) {
        return null;
      }

      if (
        typeof value !== "string"
      ) {
        return null;
      }

      return {
        key: name.trim(),
        value,
        domain:
          cookie.domain ||
          ".facebook.com",
        path:
          cookie.path ||
          "/",
      };
    })
    .filter(Boolean);

  if (!appState.length) {
    throw new Error(
      "FB_COOKIES contains no valid cookies."
    );
  }

  return appState;
}


// =========================================================
// COMMAND HELP
// =========================================================

function helpMessage() {
  return [
    "╭────────────────────╮",
    "      🐈‍⬛ CLEYDO",
    "╰────────────────────╯",
    "",
    "💰 ECONOMY",
    "• !balance",
    "• !daily",
    "• !deposit <amount>",
    "• !withdraw <amount>",
    "",
    "🎮 GAMES",
    "• !games",
    "• !blackjack [bet]",
    "• !hit",
    "• !stand",
    "• !uno",
    "• !uno hand",
    "• !uno draw",
    "• !uno <card>",
    "• !coinflip",
    "• !dice",
    "• !slots",
    "• !hunt",
    "",
    "🎭 ACTIONS",
    "• !slap @user",
    "• !kick @user",
    "• !punch @user",
    "• !hug @user",
    "• !pat @user",
    "• !highfive @user",
    "• !poke @user",
    "",
    "👑 ADMIN",
    "• !admin",
    "• !announce <message>",
    "• !addmoney <user_id> <amount>",
    "• !removemoney <user_id> <amount>",
    "• !bot on",
    "• !bot off",
    "",
    "━━━━━━━━━━━━━━━━━━━━",
    "🐾 Have fun with Cleydo!",
  ].join("\n");
}


// =========================================================
// COMMAND ROUTER
// =========================================================

async function handleCommand(
  api,
  event
) {
  const threadID =
    String(event.threadID || "");

  const senderID =
    String(
      event.senderID ||
      event.author ||
      ""
    );

  const message =
    event.body ||
    event.message?.body ||
    "";

  if (!threadID || !senderID) {
    return;
  }

  if (
    typeof message !== "string"
  ) {
    return;
  }

  const text =
    message.trim();

  if (!text) {
    return;
  }

  if (
    !text.startsWith(BOT_PREFIX)
  ) {
    return;
  }

  registerThread(threadID);

  // !bot on/off must remain available
  // even when normal bot processing is disabled.
  const commandText =
    text.slice(BOT_PREFIX.length).trim();

  if (!commandText) {
    await send(
      api,
      threadID,
      helpMessage()
    );

    return;
  }

  const command =
    commandText
      .split(/\s+/)[0]
      .toLowerCase();

  // =======================================================
  // BOT TOGGLE
  // =======================================================

  if (
    command === "bot"
  ) {
    await handleAdminCommand(
      api,
      event,
      threadID,
      senderID,
      commandText
    );

    return;
  }

  // Ignore everything else while bot is disabled.
  if (!isBotEnabled()) {
    return;
  }

  // =======================================================
  // HELP
  // =======================================================

  if (
    command === "help" ||
    command === "commands" ||
    command === "menu" ||
    command === "?"
  ) {
    await send(
      api,
      threadID,
      helpMessage()
    );

    return;
  }

  // =======================================================
  // ADMIN
  // =======================================================

  if (
    command === "admin" ||
    command === "announce" ||
    command === "addmoney" ||
    command === "removemoney"
  ) {
    await handleAdminCommand(
      api,
      event,
      threadID,
      senderID,
      commandText
    );

    return;
  }

  // =======================================================
  // ECONOMY
  // =======================================================

  const economyHandled =
    await handleEconomyCommand(
      api,
      event,
      threadID,
      senderID,
      commandText
    );

  if (economyHandled) {
    return;
  }

  // =======================================================
  // GAMES
  // =======================================================

  const gameHandled =
    await handleGamesCommand(
      api,
      event,
      threadID,
      senderID,
      commandText
    );

  if (gameHandled) {
    return;
  }

  // =======================================================
  // GAME CONTINUATION
  // =======================================================

  const responseHandled =
    await handleGameResponse(
      api,
      event,
      threadID,
      senderID,
      commandText
    );

  if (responseHandled) {
    return;
  }

  // =======================================================
  // ACTIONS
  // =======================================================

  const actionHandled =
    await handleActionCommand(
      api,
      event,
      threadID,
      senderID,
      commandText
    );

  if (actionHandled) {
    return;
  }

  // =======================================================
  // UNKNOWN COMMAND
  // =======================================================

  await send(
    api,
    threadID,
    [
      "❓ I don't recognize that command.",
      "",
      "Try:",
      "!help",
    ].join("\n")
  );
}


// =========================================================
// FACEBOOK LOGIN
// =========================================================

function startBot() {
  let appState;

  try {
    appState = readAppState();
  } catch (error) {
    console.error(
      "[Cleydo] AppState error:",
      error.message
    );

    process.exit(1);
  }

  console.log(
    "[Cleydo] Logging into Facebook..."
  );

  login(
    appState,
    {
      online: true,
      updatePresence: true,
      selfListen: false,
      randomUserAgent: false,
    },
    (error, api) => {
      if (error) {
        console.error(
          "[Cleydo] Facebook login failed:"
        );

        console.error(error);

        process.exit(1);
      }

      console.log(
        "[Cleydo] Facebook login successful."
      );

      try {
        api.setOptions({
          listenEvents: true,
          selfListen: false,
        });
      } catch (error) {
        console.error(
          "[Cleydo] Failed to configure API:",
          error
        );
      }

      // ===================================================
      // LISTEN FOR MESSAGES
      // ===================================================

      api.listenMqtt(
        async (error, event) => {
          if (error) {
            console.error(
              "[Cleydo] Messenger listener error:",
              error
            );

            return;
          }

          try {
            await handleCommand(
              api,
              event
            );
          } catch (error) {
            console.error(
              "[Cleydo] Command processing error:",
              error
            );
          }
        }
      );

      console.log(
        "[Cleydo] Messenger listener started."
      );
    }
  );
}


// =========================================================
// PROCESS ERROR HANDLING
// =========================================================

process.on(
  "uncaughtException",
  (error) => {
    console.error(
      "[Cleydo] Uncaught exception:",
      error
    );
  }
);

process.on(
  "unhandledRejection",
  (error) => {
    console.error(
      "[Cleydo] Unhandled rejection:",
      error
    );
  }
);


// =========================================================
// START
// =========================================================

startBot();
