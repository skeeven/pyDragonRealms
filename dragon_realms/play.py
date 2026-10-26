"""Interactive terminal game: python -m dragon_realms.play."""
from __future__ import annotations

import argparse
from random import Random

from .bots import choose_action, deploy_best, quest_options, score_breakdown
from .engine import Game, Phase, RuleError
from .simulate import STRATEGIES, _bid


def describe(game: Game, item) -> str:
    card = game.cards[item.card_id]
    details = f"{card.name} [{card.kind}]"
    if card.kind == "dragon":
        details += f" | {card.element}, power {card.power}, prestige {card.prestige}"
    elif card.kind == "quest":
        details += f" | requires {card.requirement}, rewards {card.reward}"
    else:
        details += f" | cost {card.cost}, prestige {card.prestige}"
    return details


def show(game: Game, pid: str) -> None:
    player = game.players[pid]
    print(f"\n=== Round {game.round}/6 | {game.phase.value.upper()} ===")
    print(f"Resources: {player.resources} | Prestige: {game.score(pid)}")
    print("Deployed dragons:")
    for n, item in enumerate(player.deployed, 1):
        print(f"  {n}. {describe(game, item)} | bond {item.bond}"
              f"{' | exhausted' if item.exhausted else ''}")
    print("Reserve:")
    for n, item in enumerate(player.reserve, 1):
        print(f"  {n}. {describe(game, item)}")
    print("Buildings:", ", ".join(game.cards[b.card_id].name
                                 for b in player.buildings) or "none")
    print("Relics:", ", ".join(game.cards[r.card_id].name
                              for r in player.relics) or "none")
    print("Scores:", game.scores())


def choose(prompt: str, maximum: int, allow_zero: bool = True,
           input_fn=input) -> int:
    while True:
        raw = input_fn(prompt).strip()
        if raw.lower() in ("help", "?"):
            print(f"Enter a number from {0 if allow_zero else 1} to {maximum}.")
            continue
        try:
            n = int(raw)
        except ValueError:
            print("Enter a whole number.")
            continue
        if (0 if allow_zero else 1) <= n <= maximum:
            return n
        print("Choice out of range.")


def affordable(resources, cost) -> bool:
    return all(resources.get(key, 0) >= amount for key, amount in cost.items())


def cost_text(cost) -> str:
    return ", ".join(f"{amount} {key}" for key, amount in cost.items()
                     if amount) or "free"


def advice(game: Game, pid: str) -> None:
    """Explain immediate opportunities, not a guaranteed optimal move."""
    player = game.players[pid]
    print("\\nYOUR OPTIONS — why they matter:")
    quests = list(quest_options(game, pid))
    if quests:
        best = max(quests, key=lambda option: option[2])
        print(f"  QUEST: {game.cards[best[0].card_id].name} is achievable "
              f"for +{best[2]} prestige this round.")
    else:
        print("  QUEST: None achievable yet. Deploy stronger or varied dragons.")
    available = [b for b in game.blueprints if
                 affordable(player.resources, game.cards[b.card_id].cost)]
    if available and len(player.buildings) < 3:
        target = max(available, key=lambda b: game.cards[b.card_id].prestige)
        print(f"  BUILD: {game.cards[target.card_id].name} is affordable "
              "and scores points immediately.")
    bond_costs = ({"ember": 2}, {"ember": 2, "aether": 1},
                  {"ember": 3, "aether": 2})
    if any(d.bond < 3 and affordable(player.resources, bond_costs[d.bond])
           for d in player.deployed):
        print("  BOND: Strengthens a dragon for future quests; "
              "bond levels 2 and 3 also earn prestige.")
    if game.round == 6:
        print("  FINAL ROUND: Unspent resources do not score. "
              "Favor actions that earn prestige now.")
    else:
        print("  CHANNEL: Gain resources to afford future buildings, "
              "bonds or market bids.")


def auction_feedback(game: Game, pid: str, previous_reserve: set,
                     previous_relics: set, previous_crystal: int) -> None:
    player = game.players[pid]
    acquired = [item for item in player.reserve + player.relics
                if item.uid not in previous_reserve | previous_relics]
    print("\\nAUCTION RESULTS")
    if acquired:
        for item in acquired:
            print(f"  WON: {describe(game, item)}")
    else:
        print("  No cards won this round.")
    print(f"  Crystal spent: {previous_crystal - player.resources['crystal']}")
    print("  Dragons won enter your reserve; deploy one to use it.")

def human_market(game: Game, pid: str, input_fn=input) -> None:
    print("\nMARKET — sealed bids; minimum 2 Crystal for dragons,"
          " 3 for relics. Zero skips a card.")
    bids = {}
    remaining = game.players[pid].resources["crystal"]
    for n, item in enumerate(game.market, 1):
        minimum = 3 if game.cards[item.card_id].kind == "relic" else 2
        print(f" {n}. {describe(game, item)}")
        if remaining < minimum:
            print(f"  Cannot bid: need {minimum} Crystal; only {remaining} left.")
            continue
        print("  Higher bids improve your chance of winning, but reserve"
              " Crystal for later cards.")
        while True:
            amount = choose(f"Bid (0 skip, {minimum}-{remaining}): ",
                            remaining, input_fn=input_fn)
            if amount == 0 or amount >= minimum:
                break
            print(f"  Minimum bid is {minimum}; try again or enter 0.")
        if amount:
            bids[item.uid] = amount
            remaining -= amount
    game.submit_bids(pid, bids)


def human_deploy(game: Game, pid: str, input_fn=input) -> None:
    player = game.players[pid]
    if not player.reserve:
        return
    print("\nDEPLOY — one deployment or swap per round (optional).")
    for n, item in enumerate(player.reserve, 1):
        print(f" {n}. {describe(game, item)}")
    selected = choose("Reserve dragon to deploy (0 skip): ",
                      len(player.reserve), input_fn=input_fn)
    if not selected:
        return
    incoming = player.reserve[selected - 1]
    if len(player.deployed) < 5:
        game.deploy(pid, incoming.uid)
        return
    print("Deployment full. Choose a deployed dragon to replace.")
    for n, item in enumerate(player.deployed, 1):
        print(f" {n}. {describe(game, item)}")
    replaced = choose("Replace (0 cancel): ", len(player.deployed),
                      input_fn=input_fn)
    if replaced:
        game.deploy(pid, incoming.uid, player.deployed[replaced - 1].uid)


def human_action(game: Game, pid: str, input_fn=input) -> None:
    player = game.players[pid]
    print(f"\nACTIONS — {player.actions_left} remaining")
    print(" 1. Channel two resources")
    print(" 2. Bond with a deployed dragon (cost: 2 Ember at level 0;"\n          " 2 Ember + 1 Aether at level 1;"\n          " 3 Ember + 2 Aether at level 2)")
    next_dragon = (game.cards[game.decks["dragon"][-1]]\n                   if game.decks["dragon"] else None)\n    recruit_cost = next_dragon.cost if next_dragon else {}\n    print(f" 3. Recruit a dragon (cost: {cost_text(recruit_cost)};"\n          " card enters reserve)")
    print(" 4. Meditate (cost: 2 Crystal; randomly draw two, keep one)")
    print(" 5. Build a sanctuary (cost varies; permanent prestige/effects)")
    print(" 6. Complete a quest (use ready dragons; gain prestige/resources)")
    print(" 7. Show status")
    action = choose("Action: ", 7, allow_zero=False, input_fn=input_fn)
    if action == 7:
        show(game, pid)
        return
    if action == 1:
        resources = ("crystal", "ember", "aether")
        gains = {}
        for i in range(2):
            for n, resource in enumerate(resources, 1):
                print(f" {n}. {resource}")
            chosen = choose(f"Resource {i + 1}: ", 3, False, input_fn)
            key = resources[chosen - 1]
            gains[key] = gains.get(key, 0) + 1
        game.act(pid, "channel", gains=gains)
    elif action == 2:
        for n, item in enumerate(player.deployed, 1):
            print(f" {n}. {describe(game, item)} | bond {item.bond}")
        n = choose("Dragon (0 cancel): ", len(player.deployed),
                   input_fn=input_fn)
        if n:
            game.act(pid, "bond", uid=player.deployed[n - 1].uid)
    elif action == 3:
        game.act(pid, "recruit")
    elif action == 4:
        n = choose("Keep first (1) or second (2): ", 2, False, input_fn)
        game.act(pid, "meditate", keep=n - 1)
    elif action == 5:
        for n, item in enumerate(game.blueprints, 1):
            print(f" {n}. {describe(game, item)}")
        n = choose("Building (0 cancel): ", len(game.blueprints),
                   input_fn=input_fn)
        if n:
            game.act(pid, "build", uid=game.blueprints[n - 1].uid)
    elif action == 6:
        options = sorted(quest_options(game, pid),
                         key=lambda x: (-x[2], len(x[1])))
        if not options:
            print("No quests currently achievable with ready dragons.")
            return
        for n, (quest, dragons, reward) in enumerate(options, 1):
            names = ", ".join(game.cards[d.card_id].name for d in dragons)
            print(f" {n}. {describe(game, quest)} | use {names}"
                  f" | +{reward} prestige")
        n = choose("Quest combination (0 cancel): ", len(options),
                   input_fn=input_fn)
        if n:
            quest, dragons, _ = options[n - 1]
            game.act(pid, "quest", uid=quest.uid,
                     dragons=[d.uid for d in dragons])


def play(seed: int = 0, tutorial: bool = True, input_fn=input) -> Game:
    """Run one interactive six-round match and return the finished game."""
    human = "You"
    bots = ["Bot-Collector", "Bot-Bonding", "Bot-Builder"]
    strategies = dict(zip(bots, ("collector", "bonding", "builder")))
    game = Game([human] + bots, seed=seed)
    rng = Random(seed + 1)
    print("DRAGON REALMS — six rounds, four Wardens")
    if tutorial:
        print("Each round: gather resources, bid for dragons/relics,"
              " trade (bots currently abstain), then take two actions.")
        print("Win by earning the most prestige through dragons, quests,"
              " bonds, buildings, relics, and synergy.")
        print("Enter ? at numeric prompts for guidance.")
    while game.phase != Phase.FINISHED:
        game.gather()
        show(game, human)
        human_market(game, human, input_fn)
        for bot in bots:
            _bid(game, bot, strategies[bot], rng)
        game.resolve_market()
        print("\nMarket results:")
        print("Your reserve and relics have been updated.")
        # Bot trading is not implemented; do not offer fake negotiations.
        game.begin_actions()
        for bot in bots:
            deploy_best(game, bot)
        show(game, human)
        try:
            human_deploy(game, human, input_fn)
        except RuleError as exc:
            print(f"Deployment rejected: {exc}")
        while game.players[human].actions_left:
            before = game.players[human].actions_left
            try:
                human_action(game, human, input_fn)
            except RuleError as exc:
                print(f"Action rejected: {exc}. Try again.")
            if game.players[human].actions_left == before:
                print("No action spent.")
        for bot in bots:
            while game.players[bot].actions_left:
                choose_action(game, bot, strategies[bot])
        print(f"\nRound {game.round} scores: {game.scores()}")
        game.end_round()
    print("\n=== FINAL RESULTS ===")
    for pid, score in sorted(game.scores().items(),
                             key=lambda entry: -entry[1]):
        print(f"{pid}: {score} prestige | {score_breakdown(game, pid)}")
    print("Winner(s):", ", ".join(game.winners()))\n    print("Scores reflect quests, deployed dragons, bonds, buildings,"\n          " relics and elemental synergy. Reserve dragons do not score.")
    return game


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Dragon Realms in terminal")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--no-tutorial", action="store_true")
    args = parser.parse_args()
    try:
        play(seed=args.seed, tutorial=not args.no_tutorial)
    except (EOFError, KeyboardInterrupt):
        print("\nGame ended without saving.")


if __name__ == "__main__":
    main()
