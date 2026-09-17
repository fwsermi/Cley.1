
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
  isAdmin,
} = require("./permissions");

// ============================================================
// CONFIG
// ============================================================

const ADMIN_IDS = (process.env.ADMIN_IDS || "")
  .split(",")
  .map((id) => id.trim())
  .filter(Boolean);

const BOT_PREFIX = "!";

// ============================================================
// WEB SERVER
// ============================================================

const app = express();

app.get("/", (_req, res) => {
  res.status(200).send("🐈‍⬛ Cleydo is running.");
});

app.get("/health", (_req, res) => {
  res.status(200).json({
    status: "online",
    bot: "Cleydo",
  });
});

const port = Number.parseInt(
  process.env.PORT || "3000",
  10
);

app.listen(
  port,
  "0.0.0.0",
  () => {
    console.log(
      `[WEB] Cleydo listening on port ${port}`
    );
  }
);

// ============================================================
// FACEBOOK SESSION
// ============================================================

function readAppState() {
  const rawCookies =
    process.env.FB_COOKIES;

  if (
    typeof rawCookies !== "string" ||
    !rawCookies.trim()
  ) {
    throw new Error(
      "FB_COOKIES is missing."
    );
  }

  let parsed;

  try {
    parsed = JSON.parse(rawCookies);

    // Supports accidentally double-encoded JSON.
    if (typeof parsed === "string") {
      parsed = JSON.parse(parsed);
    }
  } catch (error) {
    throw new Error(
      "FB_COOKIES must contain valid JSON."
    );
  }

  if (
    !Array.isArray(parsed) ||
    parsed.length === 0
  ) {
    throw new Error(
      "FB_COOKIES must be a non-empty array."
    );
  }

  return parsed.map((cookie) => {
    if (
      !cookie ||
      typeof cookie !== "object" ||
      Array.isArray(cookie)
    ) {
      throw new Error(
        "Every cookie entry must be an object."
      );
    }

    const key =
      typeof cookie.key === "string"
        ? cookie.key
        : cookie.name;

    if (
      typeof key !== "string" ||
      !key.trim() ||
      typeof cookie.value !== "string"
    ) {
      throw new Error(
        "Every cookie must contain a name/key and value."
      );
    }

    return {
      ...cookie,
      key,
    };
  });
}

// ============================================================
// LOAD SESSION
// ============================================================

let appState;

try {
  appState = readAppState();

  console.log(
    `[AUTH] Loaded ${appState.length} session cookies.`
  );
} catch (error) {
  console.error(
    `[AUTH] ${error.message}`
  );

  process.exit(1);
}

// ============================================================
// LOGIN
// ============================================================

login(
  appState,
  {
    online: true,
    updatePresence: true,
    selfListen: false,
    randomUserAgent: false,
  },

  (loginError, api) => {
    if (loginError) {
      console.error(
        "[AUTH] Facebook login failed:",
        loginError
      );

      process.exit(1);
    }

    if (!api) {
      console.error(
        "[AUTH] No Messenger API object returned."
      );

      process.exit(1);
    }

    console.log(
      "╭────────────────────────────╮"
    );
    console.log(
      "       🐈‍⬛ CLEYDO"
    );
    console.log(
      "       LOGIN SUCCESS"
    );
    console.log(
      "╰────────────────────────────╯"
    );

    // ========================================================
    // LISTENER
    // ========================================================

    api.setOptions({
      listenEvents: true,
      selfListen: false,
    });

    console.log(
      "[MESSENGER] Listener starting..."
    );

    api.listenMqtt(
      (listenError, event) => {
        if (listenError) {
          console.error(
            "[MESSENGER] Listener error:",
            listenError
          );

          return;
        }

        if (
          !event ||
          typeof event !== "object"
        ) {
          return;
        }

        if (
          event.type !== "message" &&
          event.type !== "message_reply"
        ) {
          return;
        }

        if (
          !event.threadID ||
          !event.senderID
        ) {
          return;
        }

        if (
          typeof event.body !== "string" ||
          !event.body.trim()
        ) {
          return;
        }

        void handleMessage(
          api,
          event
        );
      }
    );

    console.log(
      "[MESSENGER] Cleydo is ready."
    );
  }
);

// ============================================================
// MESSAGE HANDLER
// ===============================
