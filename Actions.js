
"use strict";

const fs = require("fs");
const path = require("path");

// ============================================================
// CONFIG
// ============================================================

const GIF_DIR =
  path.join(__dirname, "gifs");

// ============================================================
// ACTION DEFINITIONS
// ============================================================

const ACTIONS = {
  slap: {
    text: "{user} slapped {target}! 👋",
    gif: "slap.gif",
  },

  kick: {
    text: "{user} kicked {target}! 🦵",
    gif: "kick.gif",
  },

  punch: {
    text: "{user} punched {target}! 👊",
    gif: "punch.gif",
  },

  hug: {
    text: "{user} hugged {target}! 🫂",
    gif: "hug.gif",
  },

  pat: {
    text: "{user} patted {target}! 🫳",
    gif: "pat.gif",
  },

  highfive: {
    text: "{user} high-fived {target}! 🙌",
    gif: "highfive.gif",
  },

  poke: {
    text: "{user} poked {target}! 👉",
    gif: "poke.gif",
  },
};

// ============================================================
// COMMAND ALIASES
// ============================================================

const ALIASES = {
  slap: "slap",
  kick: "kick",
  punch: "punch",
  hug: "hug",
  pat: "pat",
  highfive: "highfive",
  "high-five": "highfive",
  poke: "poke",
};

// ============================================================
// PARSE TARGET
// ============================================================

function parseTarget(originalText) {
  const parts =
    String(originalText)
      .trim()
      .split(/\s+/);

  if (parts.length < 2) {
    return null;
  }

  const target =
    parts
      .slice(1)
      .join(" ")
      .trim();

  if (!target) {
    return null;
  }

  return target;
}

// ============================================================
// DISPLAY NAME
// ============================================================

async function getDisplayName(
  api,
  userID
) {
  try {
    if (
      api &&
      typeof api.getUserInfo ===
        "function"
    ) {
      const info =
        await new Promise(
          (resolve) => {
            try {
              api.getUserInfo(
                [String(userID)],
                (error, data) => {
                  if (error) {
                    resolve(null);
                    return;
                  }

                  resolve(data);
                }
              );
            } catch (_) {
              resolve(null);
            }
          }
        );

      const user =
        info &&
        info[String(userID)];

      if (user) {
        return (
          user.name ||
          user.fullName ||
          `User ${userID}`
        );
      }
    }
  } catch (error) {
    console.error(
      "[ACTIONS] Failed to get username:",
      error
    );
  }

  return `User ${userID}`;
}

// ============================================================
// GIF CHECK
// ============================================================

function getGifPath(filename) {
  if (
    typeof filename !== "string" ||
    !filename.trim()
  ) {
    return null;
  }

  const clean =
    path.basename(
      filename.trim()
    );

  const fullPath =
    path.join(
      GIF_DIR,
      clean
    );

  try {
    if (
      fs.existsSync(fullPath)
    ) {
      return fullPath;
    }
  } catch (error) {
    console.error(
      "[ACTIONS] GIF check failed:",
      error
    );
  }

  return null;
}

// ============================================================
// SEND ACTION
// ============================================================

async function sendAction(
  api,
  event,
  actionName,
  target
) {
  const threadID =
    String(event.threadID);

  const senderID =
    String(event.senderID);

  const action =
    ACTIONS[actionName];

  if (!action) {
    return false;
  }

  const senderName =
    await getDisplayName(
      api,
      senderID
    );

  const targetName =
    String(target || "someone");

  const message =
    action.text
      .replace(
        "{user}",
        senderName
      )
      .replace(
        "{target}",
        targetName
      );

  const gifPath =
    getGifPath(
      action.gif
    );

  // ----------------------------------------------------------
  // SEND GIF + TEXT
  // ----------------------------------------------------------

  if (
    gifPath &&
    typeof api.sendMessage ===
      "function"
  ) {
    try {
      await new Promise(
        (resolve) => {
          api.sendMessage(
            {
              body: message,
              attachment:
                fs.createReadStream(
                  gifPath
                ),
            },
            threadID,
            (error) => {
              if (error) {
                console.error(
                  "[ACTIONS] GIF send failed:",
                  error
                );
              }

              resolve();
            }
          );
        }
      );

      return true;
    } catc
