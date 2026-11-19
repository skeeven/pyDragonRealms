"""Presentation-only feedback for Dragon Realms player actions.

All text derives from actions already completed by the engine.
No rule, score, or resource calculation is changed here.
"""

from __future__ import annotations


ACTION_LABELS = {
    "quest": ("🗺️ Quest completed", "Your dragons gain prestige"),
    "build": ("🏰 Building constructed", "Your realm grows stronger"),
    "bond": ("🤝 Dragon bond strengthened", "Quest power improved"),
    "channel": ("💎 Resources channeled", "Supplies added"),
    "recruit": ("🐉 Dragon recruited", "Check your reserve"),
    "meditate": ("✨ Meditation complete", "Check your reserve"),
}


def action_feedback(
    action: str,
    prestige_change: int,
    resources_before: dict[str, int],
    resources_after: dict[str, int],
) -> str:
    """Summarize confirmed results of an engine action."""
    title, detail = ACTION_LABELS.get(
        action, (f"{action.title()} completed", "Action resolved")
    )
    changes = [
        f"{key.title()} {resources_after.get(key, 0) - value:+d}"
        for key, value in resources_before.items()
        if resources_after.get(key, 0) != value
    ]
    result = f"{title} · Prestige {prestige_change:+d}"
    if changes:
        result += " · " + ", ".join(changes)
    return f"{result}. {detail}."
