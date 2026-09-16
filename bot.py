from flask import Flask, request, send_from_directory
import logging
import os
import requests

from Money import (
    get_balance,
    deposit,
    withdraw,
    daily,
    admin_add_money,
    admin_remove_money,
)

from Permissions import (
    can_announce,
    is_admin,
)

from Games import (
    play_game,
    game_help,
    game_action,
)

from Actions import (
    action,
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("cleydo")


# =========================================================
# ENVIRONMENT
# =========================================================

VERIFY_TOKEN = os.environ.get(
    "VERIFY_TOKEN",
    "",
).strip()

PAGE_ACCESS_TOKEN = os.environ.get(
    "PAGE_ACCESS_TOKEN",
    "",
).strip()

PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "",
).strip().rstrip("/")


# =========================================================
# CONFIG
# =========================================================

BOT_PREFIX = "cleydo"

GIF_DIRECTORY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "gifs",
)


# =========================================================
# HELP
# =========================================================

def help_message():
    return (
        "╭────────────────────╮\n"
        "      🐈‍⬛ CLEYDO\n"
        "╰────────────────────╯\n\n"

        "💰 ECONOMY\n"
        "• `cleydo balance`\n"
        "• `cleydo daily`\n"
        "• `cleydo deposit <amount>`\n"
        "• `cleydo withdraw <amount>`\n\n"

        "🎮 GAMES\n"
        "• `cleydo games`\n"
        "• `cleydo blackjack`\n"
        "• `cleydo hit`\n"
        "• `cleydo stand`\n"
        "• `cleydo uno`\n"
        "• `cleydo play 1`\n"
        "• `cleydo coinflip`\n"
        "• `cleydo dice`\n"
        "• `cleydo slots`\n"
        "• `cleydo hunt`\n\n"

        "🎭 ACTIONS\n"
        "• `cleydo slap @user`\n"
        "• `cleydo hug @user`\n"
        "• `cleydo kick @user`\n"
        "• `cleydo punch @user`\n"
        "• `cleydo pat @user`\n"
        "• `cleydo highfive @user`\n"
        "• `cleydo poke @user`\n\n"

        "👑 ADMIN\n"
        "• `cleydo announce <message>`\n"
        "• `cleydo addmoney <user> <amount>`\n"
        "• `cleydo removemoney <user> <amount>`\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "🐾 Have fun with Cleydo!"
    )


# =========================================================
# AMOUNT PARSER
# =========================================================

def parse_amount(parts):
    if len(parts) < 2:
        return None

    try:
        amount = int(parts[1])
    except (TypeError, ValueError):
        return None

    return amount


# =========================================================
# ACTION HELPERS
# =========================================================

ACTION_NAMES = {
    "slap",
    "kick",
    "punch",
    "hug",
    "pat",
    "highfive",
    "poke",
}


# =========================================================
# CLEYDO COMMAND HANDLER
# =========================================================

def cleydo(message, user_id):
    if not isinstance(message, str):
        return None

    original = message.strip()

    if not original.lower().startswith(BOT_PREFIX):
        return None

    command = original[len(BOT_PREFIX):].strip()

    if not command:
        return help_message()

    command_lower = command.lower()

    # =====================================================
    # HELP
    # =====================================================

    if command_lower in (
        "help",
        "commands",
        "menu",
        "?",
    ):
        return help_message()

    # =====================================================
    # BALANCE
    # =====================================================

    if command_lower in (
        "balance",
        "bal",
        "wallet",
    ):
        wallet, bank = get_balance(user_id)

        total = wallet + bank

        return (
            "╭────────────────╮\n"
            "     💰 BALANCE\n"
            "╰────────────────╯\n\n"
            f"👛 Wallet: **{wallet:,}**\n"
            f"🏦 Bank: **{bank:,}**\n"
            f"💎 Total: **{total:,}**"
        )

    # =====================================================
    # DAILY
    # =====================================================

    if command_lower in (
        "daily",
        "claim",
    ):
        return daily(user_id)

    # =====================================================
    # DEPOSIT
    # =====================================================

    if command_lower == "deposit":
        return (
            "❌ Missing amount.\n\n"
            "Example:\n"
            "`cleydo deposit 500`"
        )

    if command_lower.startswith("deposit "):
        parts = command.split()

        amount = parse_amount(parts)

        if amount is None:
            return (
                "❌ Invalid amount.\n\n"
                "Example:\n"
                "`cleydo deposit 500`"
            )

        return deposit(
            user_id,
            amount,
        )

    # =====================================================
    # WITHDRAW
    # =====================================================

    if command_lower == "withdraw":
        return (
            "❌ Missing amount.\n\n"
            "Example:\n"
            "`cleydo withdraw 500`"
        )

    if command_lower.startswith("withdraw "):
        parts = command.split()

        amount = parse_amount(parts)

        if amount is None:
            return (
                "❌ Invalid amount.\n\n"
                "Example:\n"
                "`cleydo withdraw 500`"
            )

        return withdraw(
            user_id,
            amount,
        )

    # =====================================================
    # GAMES
    # =====================================================

    if command_lower in (
        "games",
        "game",
    ):
        return game_help()

    # Explicit game subcommand.
    if command_lower.startswith("game "):
        game_name = command[5:].strip()

        return play_game(
            game_name,
            user_id,
        )

    # Game continuation commands.
    if command_lower in (
        "hit",
        "stand",
        "play",
        "draw",
    ) or command_lower.startswith("play "):

        result = game_action(
            command,
            user_id,
        )

        return result

    # New game commands.
    if command_lower in (
        "blackjack",
        "uno",
        "coinflip",
        "coin",
        "flip",
        "hunt",
        "dice",
        "roll",
        "slots",
    ):
        return play_game(
            command_lower,
            user_id,
        )

    # =====================================================
    # ACTIONS
    # =====================================================

    first_word = command_lower.split(
        maxsplit=1
    )[0]

    if first_word in ACTION_NAMES:
        return action(
            command,
            user_id,
        )

    # =====================================================
    # ANNOUNCEMENT
    # =====================================================

    if command_lower == "announce":
        return (
            "❌ Write an announcement.\n\n"
            "Example:\n"
            "`cleydo announce Server maintenance tonight.`"
        )

    if command_lower.startswith("announce "):
        if not can_announce(user_id):
            return (
                "❌ You don't have permission "
                "to make announcements."
            )

        announcement = command[
            len("announce"):
        ].strip()

        if not announcement:
            return (
                "❌ Write an announcement."
            )

        return (
            "╭────────────────────╮\n"
            "      📢 ANNOUNCEMENT\n"
            "╰────────────────────╯\n\n"
            f"{announcement}\n\n"
            "🐾"
        )

    # =====================================================
    # ADMIN ADD MONEY
    # =====================================================

    if command_lower.startswith("addmoney"):
        if not is_admin(user_id):
            return (
                "❌ You don't have permission "
                "to use this command."
            )

        parts = command.split()

        if len(parts) < 3:
            return (
                "❌ Usage:\n"
                "`cleydo addmoney <user_id> <amount>`"
            )

        target_id = parts[1]

        try:
            amount = int(parts[2])
        except ValueError:
            return (
                "❌ Amount must be a valid number."
            )

        return admin_add_money(
            user_id,
            target_id,
            amount,
        )

    # =====================================================
    # ADMIN REMOVE MONEY
    # =====================================================

    if command_lower.startswith("removemoney"):
        if not is_admin(user_id):
            return (
                "❌ You don't have permission "
                "to use this command."
            )

        parts = command.split()

        if len(parts) < 3:
            return (
                "❌ Usage:\n"
                "`cleydo removemoney <user_id> <amount>`"
            )

        target_id = parts[1]

        try:
            amount = int(parts[2])
        except ValueError:
            return (
                "❌ Amount must be a valid number."
            )

        return admin_remove_money(
            user_id,
            target_id,
            amount,
        )

    # =====================================================
    # UNKNOWN
    # =====================================================

    return (
        "❓ I don't recognize that command.\n\n"
        "Try:\n"
        "`cleydo help`"
    )


# =========================================================
# MESSENGER SEND
# =========================================================

def send_message(recipient_id, message):
    if not PAGE_ACCESS_TOKEN:
        logger.error(
            "PAGE_ACCESS_TOKEN is missing."
        )
        return False

    url = (
        "https://graph.facebook.com/v23.0/me/messages"
        f"?access_token={PAGE_ACCESS_TOKEN}"
    )

    # -----------------------------------------------------
    # ACTION WITH GIF
    # -----------------------------------------------------

    if isinstance(message, dict):
        text = str(
            message.get(
                "text",
                "",
            )
        )

        gif = message.get("gif")

        # Send text + GIF attachment when possible.
        if gif and PUBLIC_BASE_URL:
            gif_url = (
                f"{PUBLIC_BASE_URL}"
                f"/gifs/{gif}"
            )

            payload = {
                "recipient": {
                    "id": str(recipient_id)
                },
                "message": {
                    "attachment": {
                        "type": "image",
                        "payload": {
                            "url": gif_url,
                            "is_reusable": True,
                        },
                    }
                },
            }

            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=15,
                )

                if response.ok:
                    return True

                logger.error(
                    "GIF send failed %s: %s",
                    response.status_code,
                    response.text,
                )

            except requests.RequestException as error:
                logger.error(
                    "GIF request failed: %s",
                    error,
                )

        # Fall back to text.
        message = text

    # -----------------------------------------------------
    # TEXT MESSAGE
    # -----------------------------------------------------

    payload = {
        "recipient": {
            "id": str(recipient_id)
        },
        "message": {
            "text": str(message)
        },
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15,
        )

        if response.ok:
            return True

        logger.error(
            "Messenger API error %s: %s",
            response.status_code,
            response.text,
        )

        return False

    except requests.RequestException as error:
        logger.error(
            "Messenger request failed: %s",
            error,
        )

        return False


# =========================================================
# GIF FILE SERVER
# =========================================================

@app.route(
    "/gifs/<path:filename>",
    methods=["GET"],
)
def serve_gif(filename):
    return send_from_directory(
        GIF_DIRECTORY,
        filename,
    )


# =========================================================
# HOME
# =========================================================

@app.route(
    "/",
    methods=["GET"],
)
def home():
    return (
        "🐈‍⬛ Cleydo is online.",
        200,
    )


# =========================================================
# HEALTH
# =========================================================

@app.route(
    "/health",
    methods=["GET"],
)
def health():
    return {
        "status": "online",
        "bot": "Cleydo",
    }, 200


# =========================================================
# WEBHOOK VERIFICATION
# =========================================================

@app.route(
    "/webhook",
    methods=["GET"],
)
def verify_webhook():
    mode = request.args.get(
        "hub.mode"
    )

    token = request.args.get(
        "hub.verify_token"
    )

    challenge = request.args.get(
        "hub.challenge"
    )

    if (
        mode == "subscribe"
        and token == VERIFY_TOKEN
        and challenge
    ):
        return challenge, 200

    return "Verification failed", 403


# =========================================================
# WEBHOOK
# =========================================================

@app.route(
    "/webhook",
    methods=["POST"],
)
def webhook():
    data = request.get_json(
        silent=True
    )

    if not data:
        return "Invalid JSON", 400

    if data.get("object") != "page":
        return "Not a page event", 404

    for entry in data.get(
        "entry",
        [],
    ):
        for event in entry.get(
            "messaging",
            [],
        ):
            try:
                sender = event.get(
                    "sender",
                    {}
                )

                sender_id = sender.get(
                    "id"
                )

                message = event.get(
                    "message",
                    {}
                )

                text = message.get(
                    "text"
                )

                if not sender_id or not text:
                    continue

                response = cleydo(
                    text,
                    sender_id,
                )

                if response is None:
                    continue

                send_message(
                    sender_id,
                    response,
                )

            except Exception as error:
                logger.exception(
                    "Event processing error: %s",
                    error,
                )

    return "EVENT_RECEIVED", 200


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    port = int(
        os.environ.get(
            "PORT",
            10000,
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )
