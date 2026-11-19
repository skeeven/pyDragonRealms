"""Streamlit visual prototype for Dragon Realms.

Run with: streamlit run app.py
"""
from __future__ import annotations

from html import escape
from random import Random
from secrets import randbelow

import streamlit as st

from dragon_realms.advisor import chapter, quest_previews, recommendation
from dragon_realms.artwork import PALETTES
from dragon_realms.art_assets import dragon_art_html
from dragon_realms.codex import (
    codex_entries,
    codex_summary,
    family_progress,
)
from dragon_realms.dragon_identity import dragon_lore
from dragon_realms.bots import (
    choose_action,
    deploy_best,
    score_breakdown,
)
from dragon_realms.engine import (
    DRAGON_ABILITIES,
    Game,
    Phase,
    RuleError,
)
from dragon_realms.history import leaderboard, match_history
from dragon_realms.presentation import action_feedback
from dragon_realms.savegame import export_session, import_session
from dragon_realms.simulate import _bid

HUMAN = "You"
BOTS = {
    "Bot-Collector": "collector",
    "Bot-Bonding": "bonding",
    "Bot-Builder": "builder",
}
BOND_COSTS = (
    {"ember": 2},
    {"ember": 2, "aether": 1},
    {"ember": 3, "aether": 2},
)

st.set_page_config(
    page_title="Dragon Realms",
    page_icon="🐉",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1500px; padding-top: 4rem;}
    h1 {font-size: 1.65rem !important;}
    .game-title {font-size: 1.65rem; font-weight: 750;
        line-height: 1.35; min-height: 2.25rem;
        padding: 0.1rem 0; margin: 0 0 0.4rem 0;
        position: relative; overflow: visible;}
    div[data-testid="stVerticalBlock"] {gap: 0.32rem;}
    div[data-testid="stMetricValue"] {font-size: 1.45rem;}
    div[data-testid="stMetric"] {
        background: #15283a;
        border: 1px solid #35536a;
        border-radius: 12px;
        padding: 7px 11px;
    }
    .dragon-slot {
        min-height: 154px; padding: 6px 5px;
        border: 1px solid var(--dragon-line, #46617a);
        border-radius: 12px;
        background:
            linear-gradient(140deg, #ffffff12, transparent 42%),
            linear-gradient(160deg, var(--dragon-tint, #182b3d),
                            #142638 72%);
        box-shadow: inset 0 0 0 1px #ffffff0b, 0 3px 9px #0003;
        text-align: center;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center; gap: 3px;
        overflow: hidden;
    }
    .dragon-slot svg, .dragon-slot img {
        display: block; width: min(100%, 120px);
        height: auto; max-height: 70px;
        filter: drop-shadow(0 3px 8px #0005);
    }
    .dragon-slot strong {
        font-size: .79rem; line-height: 1.15;
        overflow-wrap: anywhere;
    }
    .dragon-slot small {font-size: .70rem; color: #e2ebf5;}
    .dragon-slot .dragon-ability {
        color: #f0dcaa; min-height: 1.05rem; font-size: .64rem;
    }
    .dragon-slot.is-resting {opacity: .68; filter: grayscale(.3);}
    .dragon-slot .dragon-stats {
        display: flex; justify-content: center;
        gap: 4px; flex-wrap: wrap; font-size: .67rem;
    }
    .dragon-slot .dragon-stats span {
        border: 1px solid #ffffff22; border-radius: 5px;
        padding: 1px 3px; background: #07162380;
    }
    .dragon-slot .dragon-status {
        color: #f4dfa8; font-size: .64rem; font-weight: 650;
    }
    .dragon-slot:not(.empty-slot) {
        border-top: 3px solid var(--dragon-line, #46617a);
    }
    .card-art {
        display: inline-flex; vertical-align: middle;
        align-items: center; margin: 0 8px 0 0;
        border-radius: 9px; overflow: hidden;
    }
    .card-art svg, .card-art img {display: block;}
    .element-key {font-size: .77rem; opacity: .9;}
    .market-card {
        border: 1px solid #35536a;
        border-left: 3px solid var(--card-accent, #35536a);
        border-radius: 9px;
        background: linear-gradient(125deg, #26394c, #162532 65%);
        box-shadow: inset 0 1px #ffffff12;
        padding: 7px 9px; min-height: 95px;
    }
    .market-card-head {
        display: flex; align-items: center; gap: 8px;
    }
    .market-card-art {width: 62px; flex: 0 0 62px;}
    .market-card-art svg, .market-card-art img {
        display: block; width: 62px; height: auto;
    }
    .market-card-body {min-width: 0; flex: 1;}
    .market-card-title {
        display: block; font-size: .82rem; line-height: 1.15;
        color: #f4f7fc; font-weight: 700;
    }
    .market-card-meta {
        display: block; font-size: .71rem; color: #c9d8e6;
        margin-top: 3px;
    }
    .market-card-ability {
        display: block; font-size: .70rem; color: #f0d69a;
        margin-top: 4px; line-height: 1.15;
    }
    div[data-testid="stForm"] {
        border: 0; padding: 0; background: transparent;
    }
    div[data-testid="stForm"] div[data-testid="stNumberInput"] {
        margin-top: -2px;
    }
    .codex-tile {
        min-height: 98px; padding: 6px 4px;
        border: 1px solid var(--codex-accent, #42566a);
        border-radius: 9px;
        background: linear-gradient(155deg, #26394a, #172636);
        text-align: center;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center; gap: 3px;
        overflow: hidden;
    }
    .codex-tile svg, .codex-tile img {
        display: block; max-width: 100%; height: auto;
    }
    .codex-tile strong {
        font-size: .68rem; line-height: 1.2;
        overflow-wrap: anywhere;
    }
    .codex-tile small {font-size: .64rem; color: #d9e4f1;}
    .codex-tile.locked {
        background: #121a23; border-style: dashed;
        color: #8c9aa8;
    }
    .codex-tile:not(.locked) {border-top-width: 3px;}
    .codex-progress {color: #f0dcaa;}
    .codex-lock {font-size: 1.6rem; opacity: .65;}
    .codex-detail {
        border: 1px solid #49647d; border-radius: 12px;
        background: #172a3e; padding: 12px;
    }
    .empty-slot {border-style: dashed; opacity: .5;}
    .empty-slot span {font-size: 1.6rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


ELEMENT_EMOJI = {
    "Flame": "🔥",
    "Tide": "🌊",
    "Grove": "🌿",
    "Storm": "⚡",
    "Stone": "🪨",
    "Shadow": "🌑",
}


ABILITY_SHORT = {
    "produce:ember": "+1 Ember / round",
    "produce:crystal": "+1 Crystal / round",
    "produce:aether": "+1 Aether / round",
    "storm_boost": "+1 quest power",
    "stone_guard": "+1 active prestige",
    "shadow_bonus": "+1 quest prestige",
}


def show_dragon_slots(game: Game, dragons, slots: int) -> None:
    """Draw compact dragon slots instead of tall text panels."""
    if not slots:
        return
    # All zones use five tracks so a single reserve card never stretches.
    columns = st.columns(5, gap="small")
    for index in range(slots):
        with columns[index % len(columns)]:
            if index >= len(dragons):
                st.markdown(
                    '<div class="dragon-slot empty-slot">'
                    '<span>＋</span><small>EMPTY SLOT</small></div>',
                    unsafe_allow_html=True,
                )
                continue
            dragon = dragons[index]
            card = game.cards[dragon.card_id]
            exhausted = " · Resting" if dragon.exhausted else ""
            ability = DRAGON_ABILITIES.get(card.effect, "")
            title = escape(
                f"{ability} {dragon_lore(card.id)}", quote=True
            )
            name = escape(card.name)
            palette = PALETTES.get(card.element)
            color = palette[0] if palette else "#46617a"
            tint = palette[3] if palette else "#142638"
            resting = " is-resting" if dragon.exhausted else ""
            art = dragon_art_html(card.id, card.element, 112)
            st.markdown(
                f'<div class="dragon-slot{resting}" title="{title}" '
                f'style="--dragon-line:{color};--dragon-tint:{tint}">'
                f'{art}'
                f'<strong>{name}</strong>'
                f'<small>{ELEMENT_EMOJI[card.element]} '
                f'{escape(card.element)}</small>'
                '<div class="dragon-stats">'
                f'<span title="Quest power">⚔ {card.power + dragon.bond}</span>'
                f'<span title="Base prestige">🏆 {card.prestige}</span>'
                f'<span title="Bond level">🤝 {dragon.bond}</span>'
                '</div>'
                f'<small class="dragon-ability">'
                f'{escape(ABILITY_SHORT.get(card.effect, ""))}</small>'
                f'<small class="dragon-status">'
                f'{"💤 Resting" if dragon.exhausted else ""}</small>'
                '</div>',
                unsafe_allow_html=True,
            )


def start_game(seed: int, rounds: int = 8) -> None:
    """Initialize a new match and advance to its first market."""
    game = Game([HUMAN, *BOTS], seed=seed, max_rounds=rounds)
    game.gather()
    st.session_state.game = game
    st.session_state.rng = Random(seed + 1)
    st.session_state.notice = (
        "Welcome, Warden! Bid for dragons, deploy them, and earn "
        "prestige by completing quests and building your realm."
    )
    st.session_state.auction = []
    st.session_state.notice_kind = "info"


def label(game: Game, item) -> str:
    """Return a readable card label."""
    card = game.cards[item.card_id]
    return card.name


def cost_label(cost: dict[str, int]) -> str:
    """Format a resource cost."""
    return ", ".join(
        f"{value} {key.title()}"
        for key, value in cost.items() if value
    ) or "Free"


def can_afford(resources: dict[str, int],
               cost: dict[str, int]) -> bool:
    """Check whether resources cover a cost."""
    return all(resources.get(key, 0) >= value
               for key, value in cost.items())


def card_panel(game: Game, item, extra: str = "") -> None:
    """Display a compact card without relying on external images."""
    card = game.cards[item.card_id]
    element = f" · {card.element}" if card.element else ""
    if card.kind == "dragon":
        art = dragon_art_html(card.id, card.element, 64)
        st.markdown(
            f'<span class="card-art">{art}</span>'
            f'<strong>{escape(card.name)}</strong>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"**{card.name}**")
    if card.kind == "dragon":
        st.caption(
            f"{card.element} · Power {card.power} · "
            f"Prestige {card.prestige} · Bond {item.bond}"
            f"{' · Exhausted' if item.exhausted else ''}"
        )
        if card.effect in DRAGON_ABILITIES:
            st.caption(f"✨ {DRAGON_ABILITIES[card.effect]}")
    elif card.kind == "quest":
        st.caption(
            f"Requires {card.requirement} · Rewards {card.reward}"
        )
    else:
        st.caption(
            f"Prestige {card.prestige} · Cost {cost_label(card.cost)}"
        )
    if extra:
        st.caption(extra)


def market_card_html(game: Game, item) -> str:
    """Return a compact, accessible market-card summary."""
    card = game.cards[item.card_id]
    title = escape(card.name)
    if card.kind == "dragon":
        artwork = dragon_art_html(card.id, card.element, 62)
        metadata = (
            f"{escape(card.element)} · "
            f"⚔ {card.power} · 🏆 {card.prestige}"
        )
        description = escape(
            ABILITY_SHORT.get(card.effect, "No special ability")
        )
        accent = PALETTES[card.element][0]
    else:
        artwork = '<span aria-hidden="true">✨</span>'
        metadata = f"🏆 {card.prestige} · Min bid 3 Crystal"
        description = escape(
            DRAGON_ABILITIES.get(card.effect, "")
            or card.effect.replace("_", " ").title()
            or "Mystical relic"
        )
        accent = "#d8b977"
    return (
        f'<div class="market-card" '
        f'style="--card-accent:{accent}">'
        '<div class="market-card-head">'
        f'<span class="market-card-art">{artwork}</span>'
        '<span class="market-card-body">'
        f'<strong class="market-card-title">{title}</strong>'
        f'<span class="market-card-meta">{metadata}</span>'
        f'<span class="market-card-ability">{description}</span>'
        '</span></div></div>'
    )


def codex_screen(game: Game) -> None:
    """Browse compact discoveries and inspect a selected dragon."""
    summary = codex_summary(game, HUMAN)
    st.caption(
        f"Discovered {summary['discovered']} of {summary['total']} "
        f"dragons · {summary['owned']} currently owned"
    )
    progress = family_progress(game, HUMAN)
    st.caption(
        "  ·  ".join(
            f"{ELEMENT_EMOJI[entry['element']]} "
            f"{entry['element']} {entry['discovered']}/8"
            for entry in progress
        )
    )
    family = st.selectbox(
        "Dragon family",
        list(ELEMENT_EMOJI),
        key="codex_family",
    )
    family_count = next(
        item["discovered"] for item in progress
        if item["element"] == family
    )
    st.progress(
        family_count / 8,
        text=f"{family}: {family_count} of 8 discovered",
    )
    entries = codex_entries(game, HUMAN, family)
    columns = st.columns(4, gap="small")
    for index, entry in enumerate(entries):
        with columns[index % 4]:
            if entry["status"] == "Unknown":
                st.markdown(
                    '<div class="codex-tile locked" '
                    'aria-label="Undiscovered dragon">'
                    '<span class="codex-lock">🔒</span>'
                    '<small>Unknown</small></div>',
                    unsafe_allow_html=True,
                )
                continue
            art = dragon_art_html(entry["card_id"], family, 70)
            st.markdown(
                f'<div class="codex-tile" '
                f'style="--codex-accent:{PALETTES[family][0]}">'
                f'{art}<strong>{escape(entry["name"])}</strong>'
                f'<small>{entry["status"]}</small></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "View", key=f"codex_view_{entry['card_id']}",
                use_container_width=True,
            ):
                st.session_state.codex_selected = entry["card_id"]

    known = {
        item["card_id"]: item
        for item in entries if item["status"] != "Unknown"
    }
    selected = st.session_state.get("codex_selected")
    if selected not in known:
        if known:
            st.caption("Select View to inspect a discovered dragon.")
        return

    entry = known[selected]
    card = game.cards[selected]
    st.divider()
    st.markdown(f"**📖 {entry['name']} · {family} dragon**")
    art_col, info_col = st.columns([1, 2], gap="small")
    with art_col:
        st.markdown(
            dragon_art_html(selected, family, 180, portrait=True),
            unsafe_allow_html=True,
        )
    with info_col:
        st.caption(
            f"{entry['status']} · ⚔ Power {card.power} · "
            f"🏆 Prestige {card.prestige}"
        )
        st.caption(f"✨ {DRAGON_ABILITIES.get(card.effect, 'No ability')}")
        st.write(entry["lore"])



def preview_swap(game: Game, incoming, outgoing) -> int:
    """Calculate a swap's exact immediate prestige change."""
    player = game.players[HUMAN]
    before = game.score(HUMAN)
    index = player.deployed.index(outgoing)
    player.deployed[index] = incoming
    try:
        return game.score(HUMAN) - before
    finally:
        player.deployed[index] = outgoing


def market_screen(game: Game) -> None:
    """Collect human bids, then resolve the auction and start actions."""
    player = game.players[HUMAN]
    st.markdown("**🏛️ Market · Sealed auction**")
    st.caption(
        "Bid 0 to pass or at least 2 Crystal for dragons "
        "(3 for relics). Win up to 2 cards; pay only if you win."
    )
    with st.form(f"market_{game.round}"):
        submitted = st.form_submit_button(
            "⚔️ Resolve auction", type="primary",
            use_container_width=True,
        )
        columns = st.columns(2, gap="small")
        bids = {}
        for index, item in enumerate(game.market):
            column = columns[index % len(columns)]
            card = game.cards[item.card_id]
            minimum = 3 if card.kind == "relic" else 2
            with column:
                st.markdown(
                    market_card_html(game, item),
                    unsafe_allow_html=True,
                )
                bids[item.uid] = st.number_input(
                    f"Bid for {card.name} (0 or {minimum}+)",
                    min_value=0,
                    max_value=player.resources["crystal"],
                    value=0,
                    step=1,
                    label_visibility="collapsed",
                    key=f"bid_{game.round}_{item.uid}",
                    help=(
                        f"Bid 0 to pass, or at least "
                        f"{minimum} Crystal."
                    ),
                )
        total = sum(bids.values())
        st.caption(
            f"💎 Your bids: {total} / "
            f"{player.resources['crystal']} Crystal · "
            "Maximum 2 cards won."
        )
    if not submitted:
        return
    if total > player.resources["crystal"]:
        st.error("Your combined bids exceed your Crystal.")
        return
    for item in game.market:
        amount = bids[item.uid]
        minimum = 3 if game.cards[item.card_id].kind == "relic" else 2
        if 0 < amount < minimum:
            st.error(
                f"{label(game, item)} requires at least "
                f"{minimum} Crystal, or bid zero."
            )
            return
    try:
        game.submit_bids(
            HUMAN, {uid: amount for uid, amount in bids.items()
                    if amount}
        )
        for bot, strategy in BOTS.items():
            _bid(game, bot, strategy, st.session_state.rng)
        start_event = len(game.events)
        game.resolve_market()
        results = []
        for event in game.events[start_event:]:
            if event["event"] == "auction_won":
                results.append(event)
        st.session_state.auction = [
            {
                "winner": event["player"],
                "card": next(
                    (game.cards[item.card_id].name
                     for player_state in game.players.values()
                     for item in (
                         player_state.reserve + player_state.relics
                     ) if item.uid == event["card"]),
                    "Unknown card",
                ),
                "amount": event["amount"],
            }
            for event in results
        ]
        game.begin_actions()
        for bot in BOTS:
            deploy_best(game, bot)
        won = [
            result["card"] for result in st.session_state.auction
            if result["winner"] == HUMAN
        ]
        st.session_state.notice = (
            "🏛️ Auction resolved · "
            + (
                "Won: " + ", ".join(won)
                if won else "No cards won this round"
            )
            + ". Deploy a dragon if one is in reserve."
        )
        st.session_state.notice_kind = "success" if won else "info"
        st.rerun()
    except RuleError as exc:
        st.error(str(exc))


def deploy_screen(game: Game) -> None:
    """Allow a free deployment or an informed replacement."""
    player = game.players[HUMAN]
    st.markdown("**🐲 Choose a reserve dragon**")
    st.write(
        "Only deployed dragons earn dragon prestige, contribute "
        "to elemental synergy, and complete quests. You can "
        "deploy or swap once each round, for free."
    )
    if not player.reserve or player.swapped:
        st.caption("No deployment available this round.")
        return
    options = {f"{label(game, item)} · {item.uid[:5]}": item
               for item in player.reserve}
    chosen = st.selectbox(
        "Choose a reserve dragon", list(options),
        key=f"deploy_{game.round}",
    )
    incoming = options[chosen]
    if len(player.deployed) < 5:
        st.success(
            f"Deploying adds {game.cards[incoming.card_id].prestige} "
            "base prestige, potentially more from synergy."
        )
        if st.button("Deploy dragon", type="primary"):
            game.deploy(HUMAN, incoming.uid)
            st.session_state.notice = (
                f"🐉 {label(game, incoming)} deployed! "
                f"Prestige now {game.score(HUMAN)}."
            )
            st.session_state.notice_kind = "success"
            st.rerun()
        return
    replacements = {
        f"{label(game, item)} · {item.uid[:5]}": item
        for item in player.deployed if not item.exhausted
    }
    if not replacements:
        st.warning("No deployed dragon is available to swap.")
        return
    selected = st.selectbox(
        "Replace which deployed dragon?",
        list(replacements),
        key=f"replace_{game.round}",
    )
    outgoing = replacements[selected]
    change = preview_swap(game, incoming, outgoing)
    st.info(
        f"Immediate prestige change: **{change:+d}**. "
        "This includes dragon points, existing bonds, "
        "and elemental synergy."
    )
    if change < 0:
        st.warning(
            "This swap reduces your current score. "
            "It might still help with future quests."
        )
    if st.button("Confirm swap", type="primary"):
        game.deploy(HUMAN, incoming.uid, outgoing.uid)
        st.session_state.notice = (
            f"🐉 Swapped {label(game, outgoing)} for "
            f"{label(game, incoming)} ({change:+d} prestige)."
        )
        st.session_state.notice_kind = "success"
        st.rerun()


def action_screen(game: Game) -> None:
    """Offer guided, validated actions with meaningful outcomes."""
    player = game.players[HUMAN]
    st.markdown(f"**⚔️ {player.actions_left} actions remaining**")
    buildings = [
        item for item in game.blueprints
        if can_afford(
            player.resources, game.cards[item.card_id].cost
        )
    ] if len(player.buildings) < 3 else []
    bonds = [
        item for item in player.deployed
        if item.bond < 3 and can_afford(
            player.resources, BOND_COSTS[item.bond]
        )
    ]
    guide = recommendation(game, HUMAN)
    st.info(
        f"**🧙 Warden advisor · {guide['title']}**"
        f" — {guide['reason']}"
    )
    tabs = st.tabs([
        "🗺️ Quests", "🏰 Build", "🤝 Bond",
        "💎 Channel", "🐉 Recruit", "✨ Meditate",
    ])
    with tabs[0]:
        st.caption(
            "Quest = one action. Selected dragons become exhausted "
            "for the rest of this round, but recover next round."
        )
        previews = quest_previews(game, HUMAN)
        for index, preview in enumerate(previews):
            req = preview["requirement"]
            element = req.get("element") or "Any"
            distinct = req.get("distinct", 0)
            requirement = (
                f"⚔ Power {req.get('power', 0)} · "
                f"Element {element} · Distinct {distinct}"
            )
            rewards = {
                key: value for key, value in preview["reward"].items()
                if key != "prestige" and value
            }
            reward_text = (
                f" · 🎁 {cost_label(rewards)}" if rewards else ""
            )
            st.markdown(
                f"**{preview['name']}** · "
                f"🏆 +{preview['prestige']}"
            )
            st.caption(requirement + reward_text)
            if preview["ready"]:
                st.caption(
                    "✅ " + ", ".join(preview["dragon_names"])
                    + " · Dragons rest after quest."
                )
                if st.button(
                    f"Complete {preview['name']}",
                    key=f"quest_{game.round}_{preview['uid']}",
                ):
                    perform(
                        game, "quest",
                        uid=preview["uid"],
                        dragons=preview["dragon_uids"],
                    )
            else:
                st.caption(
                    "🔒 " + " ".join(preview["reasons"])
                )
            if index < len(previews) - 1:
                st.divider()
    with tabs[1]:
        st.write(
            "Buildings permanently improve your realm "
            "and may grant special effects."
        )
        for item in game.blueprints:
            card = game.cards[item.card_id]
            possible = (
                item in buildings and player.actions_left > 0
            )
            st.write(
                f"**{card.name}** · +{card.prestige} base prestige "
                f"· {cost_label(card.cost)} "
                f"· {'Affordable' if possible else 'Unavailable'}"
            )
            if st.button(
                f"Build {card.name}",
                key=f"build_{game.round}_{item.uid}",
                disabled=not possible,
            ):
                perform(game, "build", uid=item.uid)
    with tabs[2]:
        st.write(
            "Bonding improves dragon quest power. Bond level "
            "two adds 1 prestige; level three adds 3 total."
        )
        for item in player.deployed:
            cost = BOND_COSTS[min(item.bond, 2)]
            possible = item in bonds
            st.write(
                f"**{label(game, item)}** · Bond {item.bond}/3 "
                f"· Next cost: {cost_label(cost)}"
            )
            if st.button(
                f"Strengthen {label(game, item)}",
                key=f"bond_{game.round}_{item.uid}",
                disabled=not possible,
            ):
                perform(game, "bond", uid=item.uid)
    with tabs[3]:
        st.write(
            "Channel two resources for future bids, "
            "buildings, or bonds. Resource cap: 20."
        )
        choices = st.columns(3)
        with choices[0]:
            crystal = st.number_input(
                "Crystal", min_value=0, max_value=2, value=2,
                key=f"channel_crystal_{game.round}",
            )
        with choices[1]:
            ember = st.number_input(
                "Ember", min_value=0, max_value=2, value=0,
                key=f"channel_ember_{game.round}",
            )
        with choices[2]:
            aether = st.number_input(
                "Aether", min_value=0, max_value=2, value=0,
                key=f"channel_aether_{game.round}",
            )
        valid = crystal + ember + aether == 2
        if st.button(
            "Collect resources",
            disabled=not valid,
            key=f"channel_{game.round}_{player.actions_left}",
        ):
            perform(
                game, "channel",
                gains={
                    "crystal": crystal,
                    "ember": ember,
                    "aether": aether,
                },
            )
    with tabs[4]:
        st.write(
            "Recruit a random dragon into your reserve. "
            "It will not score until deployed."
        )
        available = (
            bool(game.decks["dragon"]) and len(player.reserve) < 7
        )
        if available:
            next_card = game.cards[game.decks["dragon"][-1]]
            cost = next_card.cost
            st.caption(f"Cost: {cost_label(cost)}")
            available = can_afford(player.resources, cost)
        if st.button("Recruit dragon", disabled=not available):
            perform(game, "recruit")
    with tabs[5]:
        st.write(
            "Spend 2 Crystal to draw two dragons and keep one. "
            "The current engine chooses the kept card by index "
            "without revealing the choices first."
        )
        available = (
            player.resources["crystal"] >= 2
            and len(player.reserve) < 7
            and len(game.decks["dragon"]) >= 2
        )
        if st.button(
            "Meditate (keep first draw)",
            disabled=not available,
        ):
            perform(game, "meditate", keep=0)


def perform(game: Game, action: str, **kwargs) -> None:
    """Run a human action and report a useful result."""
    try:
        before = game.score(HUMAN)
        resources_before = dict(game.players[HUMAN].resources)
        game.act(HUMAN, action, **kwargs)
        change = game.score(HUMAN) - before
        st.session_state.notice = action_feedback(
            action, change, resources_before,
            game.players[HUMAN].resources,
        )
        st.session_state.notice_kind = "success"
        st.rerun()
    except RuleError as exc:
        st.error(str(exc))


def finish_round(game: Game) -> None:
    """Let opponents act, then advance the game state."""
    for bot, strategy in BOTS.items():
        while game.players[bot].actions_left:
            choose_action(game, bot, strategy)
    game.end_round()
    if game.phase == Phase.GATHER:
        game.gather()
        st.session_state.notice = (
            f"Round {game.round} begins. Your realm gained "
            "its new round resources."
        )
        st.session_state.notice_kind = "info"
    else:
        st.session_state.notice = "The match is finished!"
        st.session_state.notice_kind = "success"
    st.rerun()


def victory_screen(game: Game) -> None:
    """Celebrate the result and show a compact detailed match recap."""
    rankings = leaderboard(game)
    winners = game.winners()
    if HUMAN in winners:
        st.success("🏆 Victory! Your realm reigns supreme!")
    else:
        st.info(f"🏆 Victory goes to {', '.join(winners)}")
    if len(winners) > 1:
        st.caption("The leading Wardens share first place.")

    top = st.columns(min(4, len(rankings)), gap="small")
    for column, item in zip(top, rankings):
        with column:
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(
                item["rank"], "🛡️"
            )
            st.metric(
                f"{medal} #{item['rank']} {item['warden']}",
                item["total"],
                help=(
                    f"{item['quests_completed']} quests completed"
                ),
            )

    breakdown_tab, history_tab = st.tabs([
        "📊 Final scoring", "📜 Match history",
    ])
    with breakdown_tab:
        st.caption(
            "Rank ties are resolved by completed quests, total "
            "bond levels, then remaining Crystal."
        )
        st.dataframe(
            [
                {
                    "Rank": entry["rank"],
                    "Warden": entry["warden"],
                    "Quests": entry["quests"],
                    "Dragons": entry["dragons"],
                    "Bonds": entry["bonds"],
                    "Buildings": entry["buildings"],
                    "Relics": entry["relics"],
                    "Synergy": entry["synergy"],
                    "Total": entry["total"],
                }
                for entry in rankings
            ],
            hide_index=True,
            use_container_width=True,
        )
        st.bar_chart(
            [
                {
                    "Warden": entry["warden"],
                    "Prestige": entry["total"],
                }
                for entry in rankings
            ],
            x="Warden",
            y="Prestige",
            horizontal=True,
        )
    with history_tab:
        history = match_history(game)
        if history:
            st.caption(
                f"{len(history)} recorded highlights across "
                f"{game.max_rounds} rounds."
            )
            rounds = ["All", *range(1, game.max_rounds + 1)]
            selected = st.selectbox(
                "Round", rounds, key="history_round"
            )
            filtered = [
                item for item in history
                if selected == "All" or item["round"] == selected
            ]
            st.dataframe(
                [
                    {
                        "Round": item["round"],
                        "Event": item["event"],
                    }
                    for item in filtered
                ],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("No recorded highlights are available.")

    st.divider()
    if st.button("🐉 Play another match", type="primary"):
        start_game(randbelow(1_000_000), game.max_rounds)
        st.rerun()


def main() -> None:
    """Render a compact, guided, session-local game board."""
    with st.sidebar:
        st.header("New match")
        rounds = st.selectbox("Match length", [8, 6, 10])
        seed = st.number_input(
            "Game seed", min_value=0, value=0, step=1
        )
        if st.button("Start new game", type="primary"):
            start_game(int(seed), rounds)
            st.rerun()
        with st.expander("💾 Save and resume", expanded=False):
            if "game" in st.session_state:
                save_text = export_session(
                    st.session_state.game,
                    st.session_state.rng,
                    st.session_state.get("auction", []),
                )
                st.download_button(
                    "💾 Download saved game",
                    data=save_text,
                    file_name=(
                        f"dragon-realms-round-"
                        f"{st.session_state.game.round}.json"
                    ),
                    mime="application/json",
                    use_container_width=True,
                )
            saved_file = st.file_uploader(
                "Load a saved game (.json)",
                type=["json"],
                key="saved_game_upload",
            )
            if st.button(
                "Restore uploaded game",
                disabled=saved_file is None,
                use_container_width=True,
            ):
                try:
                    game, rng, auction = import_session(
                        saved_file.getvalue()
                    )
                    if set(game.players) != {HUMAN, *BOTS}:
                        raise ValueError(
                            "Save does not match this game's players"
                        )
                except (ValueError, UnicodeError) as exc:
                    st.error(f"Could not restore game: {exc}")
                else:
                    st.session_state.game = game
                    st.session_state.rng = rng
                    st.session_state.auction = auction
                    st.session_state.notice = (
                        f"Restored round {game.round} of "
                        f"{game.max_rounds}."
                    )
                    st.session_state.notice_kind = "info"
                    st.rerun()
            st.caption(
                "Save a JSON file to your computer and upload it "
                "later to resume. An unsaved browser session can "
                "still be lost."
            )
        with st.expander("Rules overview"):
            st.write(
                "Bid for cards, deploy dragons, then take two actions "
                "per round. Deployed dragons score points and attempt "
                "quests. Reserve dragons are inactive."
            )

    if "game" not in st.session_state:
        start_game(0, 8)
    game = st.session_state.game
    player = game.players[HUMAN]

    st.markdown(
        '<div class="game-title">🐉 Dragon Realms</div>',
        unsafe_allow_html=True,
    )
    st.progress(
        game.round / game.max_rounds,
        text=(f"Round {game.round}/{game.max_rounds} · "
              f"{game.phase.value.title()}"),
    )
    metric_columns = st.columns(5)
    for column, (name, value) in zip(metric_columns, [
        ("💎 Crystal", player.resources["crystal"]),
        ("🔥 Ember", player.resources["ember"]),
        ("✨ Aether", player.resources["aether"]),
        ("🏆 Prestige", game.score(HUMAN)),
        ("⚔️ Actions", player.actions_left),
    ]):
        column.metric(name, value)

    scores = sorted(
        game.scores().items(), key=lambda pair: -pair[1]
    )
    st.caption(" · ".join(
        f"{pid}: {score}" for pid, score in scores
    ))
    st.caption(chapter(game))
    notice = st.session_state.get("notice")
    if notice:
        if st.session_state.get("notice_kind") == "success":
            st.success(notice, icon="✅")
        else:
            st.caption(f"ℹ️ {notice}")

    if game.phase == Phase.FINISHED:
        victory_screen(game)
        return

    board, decisions = st.columns([1.25, 1], gap="medium")
    with board:
        st.markdown("#### 🛡️ Active dragons · 5 slots")
        st.caption(
            "Deployed dragons contribute prestige, synergy and "
            "quest power. Exhausted dragons recover next round."
        )
        show_dragon_slots(game, player.deployed, 5)
        st.markdown(
            f"#### 🃏 Reserve · {len(player.reserve)} inactive"
        )
        st.caption(
            "Owned dragons waiting to be deployed. "
            "Reserve dragons do not score."
        )
        if player.reserve:
            show_dragon_slots(
                game, player.reserve, len(player.reserve)
            )
        else:
            st.caption("Empty — win or recruit a dragon.")
        with st.expander(
            f"🏰 Buildings ({len(player.buildings)}) · "
            f"✨ Relics ({len(player.relics)})"
        ):
            for item in player.buildings + player.relics:
                card_panel(game, item)
        with st.expander("Scoring and auction history"):
            st.write(score_breakdown(game, HUMAN))
            for result in st.session_state.get("auction", []):
                st.caption(
                    f"{result['winner']}: {result['card']} "
                    f"({result['amount']} Crystal)"
                )
        discovered = codex_summary(game, HUMAN)
        with st.expander(
            f"📖 Dragon Codex · "
            f"{discovered['discovered']}/{discovered['total']}"
        ):
            codex_screen(game)

    with decisions:
        if game.phase == Phase.MARKET:
            st.markdown("#### Step 1 of 3 · Acquire")
            market_screen(game)
        elif game.phase == Phase.ACTIONS:
            deployment_available = (
                not player.swapped and bool(player.reserve)
            )
            if deployment_available:
                st.markdown("#### Step 2 of 3 · Deploy")
                deploy_screen(game)
                st.divider()
            elif player.swapped:
                st.caption("✓ Free deployment used this round")
            if player.actions_left:
                st.markdown("#### Step 3 of 3 · Take actions")
                action_screen(game)
            else:
                st.success("Your actions are complete.")
                if st.button(
                    "End round · Rivals take their turns",
                    type="primary",
                ):
                    finish_round(game)
        else:
            st.error(f"Unexpected game phase: {game.phase.value}")


if __name__ == "__main__":
    main()
