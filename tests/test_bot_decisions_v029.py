"""Regression tests for v0.29 Collector and Meditate bot choices."""

from dataclasses import replace

from dragon_realms.bots import choose_action
from dragon_realms.engine import Game
from dragon_realms.simulate import simulate


def ready_match():
    """Create a legal eight-round game ready for bot decisions."""
    game = Game(["A", "B", "C"], seed=18, max_rounds=8)
    game.gather()
    game.resolve_market()
    game.begin_actions()
    return game


def prevent_other_scoring(game):
    """Remove quest and building alternatives in controlled scenarios."""
    game.quests.clear()
    game.blueprints.clear()


def test_collector_meditates_when_recruit_is_unaffordable():
    """Two Crystal can draw a dragon even if recruiting costs more."""
    game = ready_match()
    prevent_other_scoring(game)
    player = game.players["A"]
    player.resources["crystal"] = 2
    before = len(game.decks["dragon"])
    assert choose_action(game, "A", "collector") == "meditate"
    assert len(player.reserve) == 1
    assert len(game.decks["dragon"]) == before - 2
    assert player.resources["crystal"] == 0
    assert player.actions_left == 1


def test_collector_recruits_when_budget_can_cover_dragon():
    """A cheap recruit remains preferable to blind meditation."""
    game = ready_match()
    prevent_other_scoring(game)
    player = game.players["A"]
    next_id = game.decks["dragon"][-1]
    card = game.cards[next_id]
    game.cards[next_id] = replace(
        card, cost={"crystal": 3}
    )
    player.resources["crystal"] = 12
    assert choose_action(game, "A", "collector") == "recruit"
    assert len(player.reserve) == 1
    assert player.reserve[0].card_id == next_id


def test_meditation_choice_does_not_peek_at_deck_top():
    """Hidden dragon cost must not change a blind-draw decision."""
    for cost in (3, 7):
        game = ready_match()
        prevent_other_scoring(game)
        player = game.players["A"]
        next_id = game.decks["dragon"][-1]
        game.cards[next_id] = replace(
            game.cards[next_id], cost={"crystal": cost}
        )
        player.resources["crystal"] = 7
        assert choose_action(game, "A", "collector") == "meditate"
        assert len(player.reserve) == 1


def test_collector_bonds_when_dragon_team_is_full():
    """Collector converts spare Ember into stronger deployed dragons."""
    game = ready_match()
    prevent_other_scoring(game)
    player = game.players["A"]
    game.decks["dragon"].clear()
    player.deployed.extend([
        game._instance("dragon_stone_1"),
        game._instance("dragon_tide_1"),
    ])
    player.resources["ember"] = 12
    before = sum(dragon.bond for dragon in player.deployed)
    assert choose_action(game, "A", "collector") == "bond"
    assert sum(dragon.bond for dragon in player.deployed) == before + 1


def test_collector_does_not_meditate_in_final_round():
    """Blindly buying reserve dragons late cannot improve a full game."""
    game = ready_match()
    prevent_other_scoring(game)
    game.round = game.max_rounds
    player = game.players["A"]
    player.resources["crystal"] = 2
    player.resources["ember"] = 0
    assert choose_action(game, "A", "collector") == "channel"
    assert len(player.reserve) == 0


def test_collector_never_meditates_with_full_reserve():
    """The bot must honor the same seven-card reserve cap as players."""
    game = ready_match()
    prevent_other_scoring(game)
    player = game.players["A"]
    player.reserve = [
        game._instance(f"dragon_flame_{index}")
        for index in range(1, 8)
    ]
    player.resources["crystal"] = 10
    action = choose_action(game, "A", "collector")
    assert action != "meditate"
    assert len(player.reserve) == 7


def test_new_bot_choices_keep_match_scoring_consistent():
    """Short deterministic simulation still spends all 16 actions."""
    result = simulate(games=4, players=4, seed=31, rounds=8)
    for stats in result["strategies"].values():
        assert sum(stats["average_actions"].values()) == 16
    assert result["games"] == 4


def test_collector_recruits_when_only_one_card_remains():
    """Meditation needs two cards; a safe recruit uses the last one."""
    game = ready_match()
    prevent_other_scoring(game)
    game.decks["dragon"][:] = game.decks["dragon"][-1:]
    player = game.players["A"]
    player.resources["crystal"] = 12
    assert choose_action(game, "A", "collector") == "recruit"
    assert len(player.reserve) == 1
    assert not game.decks["dragon"]


def test_collector_prioritizes_ready_quest_over_meditation():
    """A confirmed scoring quest takes precedence over blind drawing."""
    game = ready_match()
    player = game.players["A"]
    quest = game.quests[0]
    card = game.cards[quest.card_id]
    game.cards[card.id] = replace(
        card,
        requirement={"power": 1, "element": "Flame"},
        reward={"prestige": 4},
    )
    player.resources["crystal"] = 7
    assert choose_action(game, "A", "collector") == "quest"
    assert player.quest_prestige == 4
    assert not player.reserve
