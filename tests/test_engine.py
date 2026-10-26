"""Tests for the standalone Dragon Realms rules engine."""

import pytest

from dragon_realms import Game, Phase, RuleError, make_catalog


def game():
    """Create a repeatable three-player game."""
    return Game(["alice", "bob", "cara"], seed=7)


def to_actions(match):
    """Advance to Warden actions."""
    match.gather()
    match.resolve_market()
    match.begin_actions()


def test_catalog_counts():
    catalog = make_catalog()
    assert len(catalog) == 104
    assert sum(card.kind == "dragon" for card in catalog.values()) == 50
    assert sum(card.kind == "quest" for card in catalog.values()) == 24


def test_player_count():
    with pytest.raises(RuleError):
        Game(["a", "b"])
    with pytest.raises(RuleError):
        Game(["a", "a", "b"])


def test_gather_and_phase():
    match = game()
    match.gather()
    assert match.phase == Phase.MARKET
    assert match.players["alice"].resources == {
        "crystal": 7, "ember": 3, "aether": 3
    }
    with pytest.raises(RuleError):
        match.gather()


def test_sealed_bids_and_tie_break():
    match = game()
    match.gather()
    uid = match.market[0].uid
    match.submit_bids("alice", {uid: 3})
    match.submit_bids("bob", {uid: 3})
    assert match.view("cara")["my_bids"] == {}
    expected = next(pid for pid in match.priority()
                    if pid in ("alice", "bob"))
    match.resolve_market()
    assert any(item.uid == uid for item in match.players[expected].reserve)
    assert match.players[expected].resources["crystal"] == 4


def test_bid_limits():
    match = game()
    match.gather()
    uid = match.market[0].uid
    with pytest.raises(RuleError):
        match.submit_bids("alice", {uid: 1})
    with pytest.raises(RuleError):
        match.submit_bids("alice", {uid: 50})


def test_bond_and_scoring():
    match = game()
    to_actions(match)
    uid = match.players["alice"].deployed[0].uid
    match.act("alice", "bond", uid=uid)
    assert match.players["alice"].deployed[0].bond == 1
    assert match.players["alice"].resources["ember"] == 1
    match.act("alice", "channel", gains={"ember": 2})
    with pytest.raises(RuleError):
        match.act("alice", "bond", uid=uid)


def test_channel_validation():
    match = game()
    to_actions(match)
    with pytest.raises(RuleError):
        match.act("alice", "channel", gains={"crystal": -1,
                                              "ember": 3})
    assert match.players["alice"].actions_left == 2


def test_trade_is_atomic():
    match = game()
    match.gather()
    match.resolve_market()
    alice = match.players["alice"]
    bob = match.players["bob"]
    trade_id = match.propose_trade(
        "alice", "bob", {"resources": {"crystal": 2}},
        {"resources": {"ember": 1}}
    )
    match.accept_trade("bob", trade_id)
    assert alice.resources["crystal"] == 5
    assert alice.resources["ember"] == 4
    assert bob.resources["crystal"] == 9
    assert bob.resources["ember"] == 2


def test_six_round_completion():
    match = game()
    for round_number in range(1, 7):
        assert match.round == round_number
        to_actions(match)
        match.end_round()
    assert match.phase == Phase.FINISHED
    assert len(match.scores()) == 3
    assert match.winners()


def test_deployment_and_quest():
    match = game()
    to_actions(match)
    with pytest.raises(RuleError):
        match.act("alice", "quest", uid=match.quests[0].uid,
                  dragons=[match.players["alice"].deployed[0].uid])
    assert match.players["alice"].actions_left == 2


def test_view_does_not_leak_other_resources():
    match = game()
    view = match.view("alice")
    assert view["players"]["bob"]["resources"] is None
    assert isinstance(view["players"]["bob"]["reserve"], int)
