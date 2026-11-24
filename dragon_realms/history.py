"""Pure presentation helpers for the final Dragon Realms scoreboard."""

from __future__ import annotations

from .bots import score_breakdown
from .engine import Game

ACTION_LABELS = {
    "quest": "completed a quest",
    "build": "constructed",
    "bond": "bonded with",
    "recruit": "recruited a dragon",
    "meditate": "meditated for a dragon",
}


def leaderboard(game: Game) -> list[dict]:
    """Rank Wardens using exactly the engine's victory tie-breakers."""
    entries = []
    for pid, player in game.players.items():
        breakdown = score_breakdown(game, pid)
        ranking = (
            game.score(pid),
            player.quests_completed,
            sum(dragon.bond for dragon in player.deployed),
            player.resources["crystal"],
        )
        entries.append({
            "warden": pid,
            "total": game.score(pid),
            "quests_completed": player.quests_completed,
            "ranking": ranking,
            **breakdown,
        })
    entries.sort(key=lambda entry: entry["ranking"], reverse=True)
    previous = None
    for index, entry in enumerate(entries, 1):
        if entry["ranking"] != previous:
            rank = index
        entry["rank"] = rank
        previous = entry["ranking"]
    return entries



def current_placement(game: Game, pid: str) -> tuple[int, bool]:
    """Return one-based standing and whether another Warden shares it.

    A tie uses the same score, quests, bonds and Crystal tie-breakers
    as the victory ranking. Final tied places remain tied.
    """
    standings = leaderboard(game)
    player = next(entry for entry in standings if entry["warden"] == pid)
    tied = sum(
        entry["ranking"] == player["ranking"] for entry in standings
    ) > 1
    return player["rank"], tied


def placement_label(rank: int, tied: bool = False) -> str:
    """Format a readable ordinal rank, including exact ties."""
    suffix = (
        "th" if rank % 100 in (11, 12, 13)
        else {1: "st", 2: "nd", 3: "rd"}.get(rank % 10, "th")
    )
    return f"{'T-' if tied else ''}{rank}{suffix}"


def match_history(game: Game) -> list[dict]:
    """Convert match events into readable, chronological highlights.

    Older saves do not include card names or explicit round numbers.
    They still produce a useful action timeline, without guessing names.
    """
    result = []
    round_number = 1
    for event in game.events:
        kind = event.get("event")
        if kind == "round_started":
            round_number = event.get("round", round_number + 1)
            continue
        current = event.get("round", round_number)
        player = event.get("player", "")
        card_name = event.get("card_name", "")
        description = ""
        if kind == "auction_won":
            name = card_name or "a market card"
            description = (
                f"{player} won {name} for {event.get('amount', 0)} Crystal"
            )
        elif kind == "deployed":
            name = card_name or "a dragon"
            description = f"{player} deployed {name}"
        elif kind == "action":
            action = event.get("action")
            if action in ACTION_LABELS:
                description = f"{player} {ACTION_LABELS[action]}"
                if card_name:
                    description += f" {card_name}"
                if action == "quest" and event.get("prestige"):
                    description += f" (+{event['prestige']} prestige)"
        elif kind == "finished":
            description = "Match completed"
        if description:
            result.append({
                "round": current,
                "event": description,
                "player": player,
            })
    return result
