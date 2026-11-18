"""Streamlit visual prototype for Dragon Realms.

Run with: streamlit run app.py
"""
from __future__ import annotations

from random import Random

import streamlit as st

from dragon_realms.advisor import chapter, quest_previews, recommendation
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
    .block-container {max-width: 1500px; padding-top: 3.25rem;}
    h1 {font-size: 1.65rem !important;}
    .game-title {font-size: 1.65rem; font-weight: 750;
        line-height: 1.3; margin: 0 0 0.4rem 0;}
    div[data-testid="stVerticalBlock"] {gap: 0.45rem;}
    div[data-testid="stMetricValue"] {font-size: 1.45rem;}
    div[data-testid="stMetric"] {
        background: #15283a;
        border: 1px solid #35536a;
        border-radius: 12px;
        padding: 10px 14px;
    }
    .dragon-slot {
        min-height: 132px; padding: 9px 6px;
        border: 1px solid #46617a; border-radius: 10px;
        background: #142638; text-align: center;
        display: flex; flex-direction: column;
        justify-content: center; gap: 4px;
    }
    .dragon-slot strong {font-size: .85rem; line-height: 1.1;}
    .dragon-slot small {font-size: .73rem; color: #c0d1dd;}
    .dragon-icon {font-size: 1.55rem;}
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
    columns = st.columns(min(slots, 5), gap="small")
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
            symbol = ELEMENT_EMOJI.get(card.element, "🐉")
            exhausted = " · Resting" if dragon.exhausted else ""
            ability = DRAGON_ABILITIES.get(card.effect, "")
            title = ability.replace('"', "&quot;")
            st.markdown(
                f'<div class="dragon-slot" title="{title}">'
                f'<div class="dragon-icon">{symbol}</div>'
                f'<strong>{card.name}</strong>'
                f'<small>{card.element}{exhausted}</small>'
                f'<small>⚔ {card.power + dragon.bond} '
                f'· 🏆 {card.prestige} '
                f'· 🤝 {dragon.bond}</small>'
                f'<small>{ABILITY_SHORT.get(card.effect, "")}</small>'
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
    st.markdown(f"**🐉 {card.name}**" if card.kind == "dragon"
                else f"**{card.name}**")
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
    st.write(
        "Bid Crystal to win dragons and relics. You only pay for "
        "winning bids. You can win at most two cards per round. "
        "New dragons go into your reserve until deployed."
    )
    st.info(
        "Tip: Powerful dragons help with quests, but buying more "
        "than you can deploy may waste Crystal."
    )
    with st.form(f"market_{game.round}"):
        columns = st.columns(2)
        bids = {}
        for index, item in enumerate(game.market):
            column = columns[index % len(columns)]
            card = game.cards[item.card_id]
            minimum = 3 if card.kind == "relic" else 2
            with column:
                card_panel(game, item)
                bids[item.uid] = st.number_input(
                    f"Bid · min {minimum} or 0",
                    min_value=0,
                    max_value=player.resources["crystal"],
                    value=0,
                    step=1,
                    key=f"bid_{game.round}_{item.uid}",
                )
        total = sum(bids.values())
        st.caption(
            f"Committed bids: {total} / "
            f"{player.resources['crystal']} Crystal"
        )
        submitted = st.form_submit_button(
            "Resolve auction", type="primary"
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
        st.session_state.notice = "Auction resolved. Deploy a dragon next."
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
                f"Deployed {label(game, incoming)}."
            )
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
            f"Swapped {label(game, outgoing)} for "
            f"{label(game, incoming)} ({change:+d} prestige)."
        )
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
            requirements = [
                f"Power {req.get('power', 0)}",
                f"Element: {req['element']}"
                if req.get("element") else "Any element",
                f"{req['distinct']} different elements"
                if req.get("distinct") else "No diversity requirement",
            ]
            st.markdown(
                f"**{preview['name']}** · "
                f"🏆 +{preview['prestige']} prestige"
            )
            st.caption(" · ".join(requirements))
            if preview["ready"]:
                st.caption(
                    "Listed prestige includes any Shadow bonuses."
                )
            extra_rewards = {
                key: value for key, value in preview["reward"].items()
                if key != "prestige" and value
            }
            if extra_rewards:
                st.caption(
                    "Additional rewards: " + cost_label(extra_rewards)
                )
            if preview["ready"]:
                st.caption(
                    "✅ Ready team: "
                    + ", ".join(preview["dragon_names"])
                    + " · These dragons rest after the quest."
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
                    "🔒 Not ready: " + " ".join(preview["reasons"])
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
        game.act(HUMAN, action, **kwargs)
        change = game.score(HUMAN) - before
        st.session_state.notice = (
            f"{action.title()} completed. "
            f"Prestige change: {change:+d}."
        )
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
    else:
        st.session_state.notice = "The match is finished!"
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
        st.divider()
        st.subheader("Save and resume")
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
        st.caption(f"ℹ️ {notice}")

    if game.phase == Phase.FINISHED:
        st.success(
            f"Game over! Winner: {', '.join(game.winners())}"
        )
        st.dataframe(
            [
                dict(Warden=pid, **score_breakdown(game, pid),
                     Total=game.score(pid))
                for pid in game.players
            ],
            hide_index=True,
            use_container_width=True,
        )
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
