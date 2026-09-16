import os
import sqlite3
import time


# =========================================================
# DATABASE
# =========================================================

DB_FILE = os.environ.get(
    "CLEYDO_DB_FILE",
    "cleydo.db",
)


def connect():
    db = sqlite3.connect(
        DB_FILE,
        timeout=15,
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            wallet INTEGER NOT NULL DEFAULT 0,
            bank INTEGER NOT NULL DEFAULT 0,
            last_daily INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    db.commit()

    return db


# =========================================================
# USER
# =========================================================

def ensure_user(user_id):
    user_id = str(user_id)

    db = connect()

    try:
        db.execute(
            """
            INSERT OR IGNORE INTO users (
                user_id
            )
            VALUES (?)
            """,
            (user_id,),
        )

        db.commit()

    finally:
        db.close()


# =========================================================
# BALANCE
# =========================================================

def get_balance(user_id):
    user_id = str(user_id)

    ensure_user(user_id)

    db = connect()

    try:
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT wallet, bank
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )

        result = cursor.fetchone()

        if result is None:
            return 0, 0

        return (
            int(result[0]),
            int(result[1]),
        )

    finally:
        db.close()


# =========================================================
# ADD MONEY
# =========================================================

def add_money(
    user_id,
    amount,
):
    try:
        amount = int(amount)
    except (
        TypeError,
        ValueError,
    ):
        return False

    if amount <= 0:
        return False

    user_id = str(user_id)

    ensure_user(user_id)

    db = connect()

    try:
        db.execute(
            """
            UPDATE users
            SET wallet = wallet + ?
            WHERE user_id = ?
            """,
            (
                amount,
                user_id,
            ),
        )

        db.commit()

        return True

    finally:
        db.close()


# =========================================================
# REMOVE MONEY
# =========================================================

def remove_money(
    user_id,
    amount,
):
    try:
        amount = int(amount)
    except (
        TypeError,
        ValueError,
    ):
        return False

    if amount <= 0:
        return False

    user_id = str(user_id)

    wallet, bank = get_balance(
        user_id
    )

    if wallet + bank < amount:
        return False

    wallet_remove = min(
        wallet,
        amount,
    )

    bank_remove = (
        amount
        - wallet_remove
    )

    db = connect()

    try:
        db.execute(
            """
            UPDATE users
            SET wallet = wallet - ?,
                bank = bank - ?
            WHERE user_id = ?
            """,
            (
                wallet_remove,
                bank_remove,
                user_id,
            ),
        )

        db.commit()

        return True

    finally:
        db.close()


# =========================================================
# DEPOSIT
# =========================================================

def deposit(
    user_id,
    amount,
):
    try:
        amount = int(amount)
    except (
        TypeError,
        ValueError,
    ):
        return (
            "❌ Amount must be a valid number."
        )

    if amount <= 0:
        return (
            "❌ Amount must be greater than 0."
        )

    wallet, bank = get_balance(
        user_id
    )

    if wallet < amount:
        return (
            "❌ You don't have enough "
            "coins in your wallet."
        )

    user_id = str(user_id)

    db = connect()

    try:
        db.execute(
            """
            UPDATE users
            SET wallet = wallet - ?,
                bank = bank + ?
            WHERE user_id = ?
            """,
            (
                amount,
                amount,
                user_id,
            ),
        )

        db.commit()

    finally:
        db.close()

    return (
        "╭────────────────╮\n"
        "      🏦 DEPOSIT\n"
        "╰────────────────╯\n\n"
        f"💰 Deposited: **{amount:,}**\n\n"
        f"👛 Wallet: **{wallet - amount:,}**\n"
        f"🏦 Bank: **{bank + amount:,}**"
    )


# =========================================================
# WITHDRAW
# =========================================================

def withdraw(
    user_id,
    amount,
):
    try:
        amount = int(amount)
    except (
        TypeError,
        ValueError,
    ):
        return (
            "❌ Amount must be a valid number."
        )

    if amount <= 0:
        return (
            "❌ Amount must be greater than 0."
        )

    wallet, bank = get_balance(
        user_id
    )

    if bank < amount:
        return (
            "❌ You don't have enough "
            "coins in your bank."
        )

    user_id = str(user_id)

    db = connect()

    try:
        db.execute(
            """
            UPDATE users
            SET wallet = wallet + ?,
                bank = bank - ?
            WHERE user_id = ?
            """,
            (
                amount,
                amount,
                user_id,
            ),
        )

        db.commit()

    finally:
        db.close()

    return (
        "╭────────────────╮\n"
        "     💵 WITHDRAW\n"
        "╰────────────────╯\n\n"
        f"💰 Withdrew: **{amount:,}**\n\n"
        f"👛 Wallet: **{wallet + amount:,}**\n"
        f"🏦 Bank: **{bank - amount:,}**"
    )


# =========================================================
# DAILY
# =========================================================

DAILY_AMOUNT = 500
DAILY_COOLDOWN = 24 * 60 * 60


def daily(user_id):
    user_id = str(user_id)

    ensure_user(user_id)

    db = connect()

    try:
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT last_daily
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )

        result = cursor.fetchone()

        last_daily = (
            int(result[0])
            if result
            else 0
        )

        now = int(
            time.time()
        )

        remaining = (
            DAILY_COOLDOWN
            - (
                now
                - last_daily
            )
        )

        if remaining > 0:
            hours = (
                remaining
                // 3600
            )

            minutes = (
                remaining
                % 3600
            ) // 60

            return (
                "╭────────────────╮\n"
                "       🎁 DAILY\n"
                "╰────────────────╯\n\n"
                "❌ Already claimed!\n\n"
                f"⏰ Try again in "
                f"**{hours}h {minutes}m**."
            )

        cursor.execute(
            """
            UPDATE users
            SET wallet = wallet + ?,
                last_daily = ?
            WHERE user_id = ?
            """,
            (
                DAILY_AMOUNT,
                now,
                user_id,
            ),
        )

        db.commit()

    finally:
        db.close()

    return (
        "╭────────────────╮\n"
        "   🎁 DAILY REWARD\n"
        "╰────────────────╯\n\n"
        f"💰 **+{DAILY_AMOUNT:,} coins**\n\n"
        "Come back tomorrow! 🐈‍⬛"
    )


# =========================================================
# ADMIN
# =========================================================

ADMINS = {
    admin_id.strip()
    for admin_id in os.environ.get(
        "ADMIN_IDS",
        "",
    ).split(",")
    if admin_id.strip()
}


def is_admin(user_id):
    return str(user_id) in ADMINS


def admin_add_money(
    admin_id,
    target_id,
    amount,
):
    if not is_admin(admin_id):
        return (
            "❌ You don't have permission."
        )

    try:
        amount = int(amount)
    except (
        TypeError,
        ValueError,
    ):
        return (
            "❌ Amount must be a valid number."
        )

    if amount <= 0:
        return (
            "❌ Amount must be greater than 0."
        )

    if not add_money(
        target_id,
        amount,
    ):
        return (
            "❌ Failed to add coins."
        )

    return (
        "╭────────────────╮\n"
        "    👑 ADMIN MONEY\n"
        "╰────────────────╯\n\n"
        f"💰 Added: **{amount:,}**\n"
        f"👤 User: `{target_id}`"
    )


def admin_remove_money(
    admin_id,
    target_id,
    amount,
):
    if not is_admin(admin_id):
        return (
            "❌ You don't have permission."
        )

    try:
        amount = int(amount)
    except (
        TypeError,
        ValueError,
    ):
        return (
            "❌ Amount must be a valid number."
        )

    if amount <= 0:
        return (
            "❌ Amount must be greater than 0."
        )

    if not remove_money(
        target_id,
        amount,
    ):
        return (
            "❌ That user doesn't have "
            "enough money."
        )

    return (
        "╭────────────────╮\n"
        "    👑 ADMIN MONEY\n"
        "╰────────────────╯\n\n"
        f"💰 Removed: **{amount:,}**\n"
        f"👤 User: `{target_id}`"
    )
