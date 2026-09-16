import random
import time

from Money import add_money


# =========================================================
# SETTINGS
# =========================================================

BLACKJACK_STARTING_BET = 100
BLACKJACK_WIN_MULTIPLIER = 2
BLACKJACK_BLACKJACK_MULTIPLIER = 3

UNO_STARTING_COST = 50

HUNT_MIN_REWARD = 20
HUNT_MAX_REWARD = 160


# =========================================================
# SESSION STORAGE
# =========================================================

BLACKJACK_SESSIONS = {}
UNO_SESSIONS = {}

SESSION_TIMEOUT = 10 * 60


# =========================================================
# CARD DATA
# =========================================================

CARDS = [
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
]


def card_value(card):
    if card == "A":
        return 11

    if card in (
        "J",
        "Q",
        "K",
    ):
        return 10

    return int(card)


def hand_value(hand):
    total = sum(
        card_value(card)
        for card in hand
    )

    aces = hand.count("A")

    while total > 21 and aces:
        total -= 10
        aces -= 1

    return total


def cleanup_sessions():
    now = time.time()

    for user_id, session in list(
        BLACKJACK_SESSIONS.items()
    ):
        if (
            now - session["created_at"]
            > SESSION_TIMEOUT
        ):
            del BLACKJACK_SESSIONS[user_id]

    for user_id, session in list(
        UNO_SESSIONS.items()
    ):
        if (
            now - session["created_at"]
            > SESSION_TIMEOUT
        ):
            del UNO_SESSIONS[user_id]


# =========================================================
# BLACKJACK
# =========================================================

def blackjack(user_id):
    cleanup_sessions()

    user_id = str(user_id)

    if user_id in BLACKJACK_SESSIONS:
        return (
            "🃏 You already have a Blackjack game.\n\n"
            "Use:\n"
            "`cleydo hit`\n"
            "`cleydo stand`"
        )

    player = [
        random.choice(CARDS),
        random.choice(CARDS),
    ]

    dealer = [
        random.choice(CARDS),
        random.choice(CARDS),
    ]

    player_total = hand_value(player)

    session = {
        "player": player,
        "dealer": dealer,
        "created_at": time.time(),
        "bet": BLACKJACK_STARTING_BET,
    }

    BLACKJACK_SESSIONS[user_id] = session

    if player_total == 21:
        del BLACKJACK_SESSIONS[user_id]

        reward = (
            BLACKJACK_STARTING_BET
            * BLACKJACK_BLACKJACK_MULTIPLIER
        )

        add_money(
            user_id,
            reward,
        )

        return (
            "╭─────────────────╮\n"
            "      🃏 BLACKJACK\n"
            "╰─────────────────╯\n\n"
            f"Your cards:\n"
            f"{' | '.join(player)}\n\n"
            f"Your total: **21**\n"
            f"Dealer: {' | '.join(dealer)}\n\n"
            "✨ **NATURAL BLACKJACK!**\n\n"
            f"💰 +{reward:,} coins"
        )

    return format_blackjack(
        player,
        dealer,
    )


def format_blackjack(
    player,
    dealer,
):
    total = hand_value(player)

    return (
        "╭─────────────────╮\n"
        "      🃏 BLACKJACK\n"
        "╰─────────────────╯\n\n"
        f"Your cards:\n"
        f"{' | '.join(player)}\n"
        f"Total: **{total}**\n\n"
        f"Dealer:\n"
        f"{dealer[0]} | ❓\n\n"
        "🎴 `cleydo hit`\n"
        "🛑 `cleydo stand`"
    )


def blackjack_hit(user_id):
    cleanup_sessions()

    user_id = str(user_id)

    session = BLACKJACK_SESSIONS.get(
        user_id
    )

    if not session:
        return (
            "❌ You don't have an active "
            "Blackjack game.\n\n"
            "Start one with:\n"
            "`cleydo blackjack`"
        )

    session["player"].append(
        random.choice(CARDS)
    )

    total = hand_value(
        session["player"]
    )

    if total > 21:
        del BLACKJACK_SESSIONS[user_id]

        return (
            "╭─────────────────╮\n"
            "       💥 BUST\n"
            "╰─────────────────╯\n\n"
            f"Your cards:\n"
            f"{' | '.join(session['player'])}\n\n"
            f"Total: **{total}**\n\n"
            "💀 You went over 21.\n"
            "Better luck next time."
        )

    if total == 21:
        return blackjack_stand(
            user_id
        )

    return format_blackjack(
        session["player"],
        session["dealer"],
    )


def blackjack_stand(user_id):
    cleanup_sessions()

    user_id = str(user_id)

    session = BLACKJACK_SESSIONS.get(
        user_id
    )

    if not session:
        return (
            "❌ You don't have an active "
            "Blackjack game."
        )

    player = session["player"]
    dealer = session["dealer"]
    bet = session["bet"]

    player_total = hand_value(player)

    while hand_value(dealer) < 17:
        dealer.append(
            random.choice(CARDS)
        )

    dealer_total = hand_value(
        dealer
    )

    del BLACKJACK_SESSIONS[user_id]

    if dealer_total > 21:
        reward = (
            bet
            * BLACKJACK_WIN_MULTIPLIER
        )

        add_money(
            user_id,
            reward,
        )

        result = (
            "🎉 Dealer busted!\n"
            f"💰 +{reward:,} coins"
        )

    elif player_total > dealer_total:
        reward = (
            bet
            * BLACKJACK_WIN_MULTIPLIER
        )

        add_money(
            user_id,
            reward,
        )

        result = (
            "🏆 You win!\n"
            f"💰 +{reward:,} coins"
        )

    elif player_total == dealer_total:
        add_money(
            user_id,
            bet,
        )

        result = (
            "🤝 Push!\n"
            f"💰 Your {bet:,} coin bet was returned."
        )

    else:
        result = (
            "💀 Dealer wins.\n"
            "Better luck next time."
        )

    return (
        "╭─────────────────╮\n"
        "    🃏 GAME OVER\n"
        "╰─────────────────╯\n\n"
        f"Your cards:\n"
        f"{' | '.join(player)}\n"
        f"Total: **{player_total}**\n\n"
        f"Dealer cards:\n"
        f"{' | '.join(dealer)}\n"
        f"Total: **{dealer_total}**\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"{result}"
    )


# =========================================================
# UNO
# =========================================================

UNO_COLORS = [
    "🔴",
    "🟡",
    "🟢",
    "🔵",
]

UNO_NUMBERS = [
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
]


def generate_uno_card():
    return (
        random.choice(UNO_COLORS)
        + random.choice(UNO_NUMBERS)
    )


def uno(user_id):
    cleanup_sessions()

    user_id = str(user_id)

    if user_id in UNO_SESSIONS:
        return format_uno(
            UNO_SESSIONS[user_id]
        )

    hand = [
        generate_uno_card(),
        generate_uno_card(),
        generate_uno_card(),
    ]

    session = {
        "hand": hand,
        "created_at": time.time(),
        "turn": 0,
    }

    UNO_SESSIONS[user_id] = session

    return format_uno(
        session
    )


def format_uno(session):
    hand = session["hand"]

    cards = []

    for index, card in enumerate(
        hand,
        start=1,
    ):
        cards.append(
            f"{index}️⃣ {card}"
        )

    return (
        "╭─────────────────╮\n"
        "        🃏 UNO\n"
        "╰─────────────────╯\n\n"
        "Your hand:\n\n"
        + "\n".join(cards)
        + "\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "`cleydo play 1`\n"
        "`cleydo play 2`\n"
        "`cleydo play 3`"
    )


def uno_play(
    user_id,
    card_number,
):
    cleanup_sessions()

    user_id = str(user_id)

    session = UNO_SESSIONS.get(
        user_id
    )

    if not session:
        return (
            "❌ You don't have an active UNO game.\n\n"
            "Start with:\n"
            "`cleydo uno`"
        )

    try:
        index = int(card_number) - 1
    except (TypeError, ValueError):
        return (
            "❌ Choose a card from 1 to 3."
        )

    hand = session["hand"]

    if index < 0 or index >= len(hand):
        return (
            "❌ That card doesn't exist."
        )

    played = hand.pop(index)

    # Draw a replacement.
    hand.append(
        generate_uno_card()
    )

    # Simple solo AI response.
    ai_card = generate_uno_card()

    if random.random() < 0.35:
        del UNO_SESSIONS[user_id]

        reward = random.randint(
            100,
            300,
        )

        add_money(
            user_id,
            reward,
        )

        return (
            "╭─────────────────╮\n"
            "       🃏 UNO\n"
            "╰─────────────────╯\n\n"
            f"🎴 You played **{played}**\n"
            f"🤖 Cleydo played **{ai_card}**\n\n"
            "✨ **YOU WIN!**\n\n"
            f"💰 +{reward:,} coins"
        )

    return (
        "╭─────────────────╮\n"
        "       🃏 UNO\n"
        "╰─────────────────╯\n\n"
        f"🎴 You played **{played}**\n"
        f"🤖 Cleydo played **{ai_card}**\n\n"
        "The game continues...\n\n"
        + format_uno(session)
    )


# =========================================================
# COIN FLIP
# =========================================================

def coinflip():
    result = random.choice(
        [
            "🪙 HEADS",
            "🪙 TAILS",
        ]
    )

    return (
        "╭─────────────────╮\n"
        "     🪙 COIN FLIP\n"
        "╰─────────────────╯\n\n"
        "Cleydo flipped the coin...\n\n"
        f"✨ **{result}**"
    )


# =========================================================
# HUNT
# =========================================================

ANIMALS = [
    ("🐰 Rabbit", 20, 60),
    ("🦊 Fox", 40, 90),
    ("🐺 Wolf", 60, 120),
    ("🐻 Bear", 80, 160),
    ("🦌 Deer", 50, 100),
]


def hunt(user_id):
    animal, minimum, maximum = random.choice(
        ANIMALS
    )

    coins = random.randint(
        minimum,
        maximum,
    )

    add_money(
        user_id,
        coins,
    )

    return (
        "╭─────────────────╮\n"
        "       🏹 HUNT\n"
        "╰─────────────────╯\n\n"
        f"You encountered a {animal}!\n\n"
        f"💰 **+{coins:,} coins**\n\n"
        "The reward was added to your wallet."
    )


# =========================================================
# DICE
# =========================================================

def dice():
    number = random.randint(
        1,
        6,
    )

    faces = {
        1: "⚀",
        2: "⚁",
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅",
    }

    return (
        "╭─────────────────╮\n"
        "        🎲 DICE\n"
        "╰─────────────────╯\n\n"
        f"{faces[number]}  **{number}**\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Luck has spoken."
    )


# =========================================================
# SLOTS
# =========================================================

SLOT_SYMBOLS = [
    "🍒",
    "🍋",
    "🍇",
    "⭐",
    "💎",
    "🔔",
]


def slots():
    a = random.choice(
        SLOT_SYMBOLS
    )

    b = random.choice(
        SLOT_SYMBOLS
    )

    c = random.choice(
        SLOT_SYMBOLS
    )

    result = (
        f"{a} │ {b} │ {c}"
    )

    if a == b == c:
        outcome = (
            "✨ **THREE MATCH!**\n"
            "🎉 JACKPOT!"
        )

    elif (
        a == b
        or b == c
        or a == c
    ):
        outcome = (
            "✨ **TWO MATCH!**\n"
            "Not bad!"
        )

    else:
        outcome = (
            "Nothing matched.\n"
            "Better luck next time. 😭"
        )

    return (
        "╭─────────────────╮\n"
        "       🎰 SLOTS\n"
        "╰─────────────────╯\n\n"
        f"      {result}\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"{outcome}"
    )


# =========================================================
# GAME ROUTER
# =========================================================

def play_game(
    game_name,
    user_id=None,
):
    game_name = str(
        game_name
    ).lower().strip()

    if game_name == "blackjack":
        if user_id is None:
            return (
                "❌ User ID is required."
            )

        return blackjack(
            user_id
        )

    if game_name == "uno":
        if user_id is None:
            return (
                "❌ User ID is required."
            )

        return uno(
            user_id
        )

    if game_name in (
        "coinflip",
        "coin",
        "flip",
    ):
        return coinflip()

    if game_name == "hunt":
        if user_id is None:
            return (
                "❌ User ID is required."
            )

        return hunt(
            user_id
        )

    if game_name in (
        "dice",
        "roll",
    ):
        return dice()

    if game_name == "slots":
        return slots()

    return (
        "❌ Unknown game.\n\n"
        "Available games:\n"
        "🃏 blackjack\n"
        "🃏 uno\n"
        "🪙 coinflip\n"
        "🏹 hunt\n"
        "🎲 dice\n"
        "🎰 slots"
    )


# =========================================================
# GAME ACTION ROUTER
# =========================================================

def game_action(
    command,
    user_id,
):
    command = str(
        command
    ).lower().strip()

    if command == "hit":
        return blackjack_hit(
            user_id
        )

    if command == "stand":
        return blackjack_stand(
            user_id
        )

    if command.startswith("play "):
        card_number = command[
            5:
        ].strip()

        return uno_play(
            user_id,
            card_number,
        )

    return (
        "❌ Invalid game action."
    )


# =========================================================
# HELP
# =========================================================

def game_help():
    return (
        "╭──────────────────╮\n"
        "      🎮 GAMES\n"
        "╰──────────────────╯\n\n"

        "🃏 BLACKJACK\n"
        "`cleydo blackjack`\n"
        "`cleydo hit`\n"
        "`cleydo stand`\n\n"

        "🃏 UNO\n"
        "`cleydo uno`\n"
        "`cleydo play 1`\n"
        "`cleydo play 2`\n"
        "`cleydo play 3`\n\n"

        "🪙 COIN FLIP\n"
        "`cleydo coinflip`\n\n"

        "🏹 HUNT\n"
        "`cleydo hunt`\n\n"

        "🎲 DICE\n"
        "`cleydo dice`\n\n"

        "🎰 SLOTS\n"
        "`cleydo slots`"
    )
