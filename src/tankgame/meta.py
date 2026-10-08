"""Meta progression rules: quests, codes, shop, ranks, rebirth."""

import datetime
import random

from .data import progression as P
from .data.tanks import TANKS


def today() -> str:
    """Return today's date as an ISO string, the key for daily resets."""
    return datetime.date.today().isoformat()


def week_id() -> str:
    """Return the current ISO week as `YYYY-Www`, the key for weekly resets."""
    y, w, _ = datetime.date.today().isocalendar()
    return f"{y}-W{w}"


def _quest_entry(q):
    return {"id": q[0], "progress": 0, "done": False}


def ensure_quests(profile: dict) -> None:
    """Roll new daily and weekly quests when they are stale, and add missing unique quests."""
    qs = profile["quests"]
    if qs["daily_date"] != today():
        rng = random.Random(today())
        qs["daily_date"] = today()
        qs["daily"] = [_quest_entry(q) for q in rng.sample(P.DAILY_POOL, P.DAILY_COUNT)]
    if qs["weekly_id"] != week_id():
        rng = random.Random(week_id())
        qs["weekly_id"] = week_id()
        qs["weekly"] = [_quest_entry(q) for q in rng.sample(P.WEEKLY_POOL, P.WEEKLY_COUNT)]
    for q in P.UNIQUE_QUESTS:
        qs["unique"].setdefault(q[0], {"id": q[0], "progress": 0, "done": False})


QUEST_DEFS = {q[0]: q for q in P.DAILY_POOL + P.WEEKLY_POOL + P.UNIQUE_QUESTS}


def all_quest_entries(profile: dict):
    """Yield `(kind, entry)` for every daily, weekly and unique quest in the profile."""
    qs = profile["quests"]
    for e in qs["daily"]:
        yield "Daily", e
    for e in qs["weekly"]:
        yield "Weekly", e
    for e in qs["unique"].values():
        yield "Unique", e


def quest_event(profile: dict, event: str, amount: float = 1) -> list[str]:
    """Record progress. Returns messages for any quests completed."""
    done_msgs = []
    for _kind, e in all_quest_entries(profile):
        if e["done"]:
            continue
        _qid, text, ev, target, mode, reward = QUEST_DEFS[e["id"]]
        if ev != event:
            continue
        if mode == "sum":
            e["progress"] += amount
        else:
            e["progress"] = max(e["progress"], amount)
        if e["progress"] >= target:
            e["progress"] = target
            e["done"] = True
            done_msgs.append(f"Quest complete: {text}! " + grant_reward(profile, reward))
    return done_msgs


def grant_reward(profile: dict, reward) -> str:
    """Grant a quest reward and return a message describing it.

    Parameters
    ----------
    profile : dict
        The profile to update.
    reward : int or str
        A gem amount, or the name of a tank to unlock.

    Returns
    -------
    str
        A short message describing the reward.
    """
    if isinstance(reward, str):
        if reward not in profile["unlocked_tanks"]:
            profile["unlocked_tanks"].append(reward)
        return f"Unlocked {reward}!"
    profile["gems"] += reward
    return f"+{reward:,} gems"


def redeem_code(profile: dict, code: str) -> str:
    """Redeem a code for gems or head-start XP, and return a status message."""
    code = code.strip().upper()
    if code not in P.CODES:
        return "Invalid code."
    if code in profile["redeemed_codes"]:
        return "Code already redeemed."
    kind, val = P.CODES[code]
    profile["redeemed_codes"].append(code)
    if kind == "gems":
        profile["gems"] += val
        return f"+{val:,} gems!"
    profile["pending_xp"] += val
    return f"+{val:,} XP head start on your next run!"


def stat_cap(profile: dict, stat: str) -> int:
    """Return the maximum number of points the player can put into a stat."""
    return P.BASE_CAP + profile["caps"][stat]


def next_cap_cost(profile: dict, stat: str) -> int | None:
    """Return the gem cost of the next cap upgrade for a stat, or None if maxed."""
    if stat_cap(profile, stat) >= P.MAX_CAPS[stat]:
        return None
    return P.cap_upgrade_cost(profile["caps"][stat] + 1)


def buy_cap(profile: dict, stat: str) -> bool:
    """Buy the next cap upgrade for a stat. Return whether it was bought."""
    cost = next_cap_cost(profile, stat)
    if cost is None or profile["gems"] < cost:
        return False
    profile["gems"] -= cost
    profile["caps"][stat] += 1
    return True


def rank(profile: dict) -> int:
    """Return the player's rank based on their total score."""
    return P.rank_for_score(profile["total_score"])


def tank_unlocked(profile: dict, name: str) -> bool:
    """Return whether the player may evolve into the named tank."""
    t = TANKS[name]
    if t["unlock"] == "rank":
        return rank(profile) >= P.BLAST_LORD_RANK
    if t["unlock"] == "quest" or t["price"] > 0:
        return name in profile["unlocked_tanks"]
    return True


def lock_reason(profile: dict, name: str) -> str:
    """Return a short label saying how a locked tank is unlocked."""
    t = TANKS[name]
    if t["unlock"] == "rank":
        return f"Rank {P.BLAST_LORD_RANK}"
    if t["unlock"] == "quest":
        return "Quest"
    return f"{t['price']:,} gems"


def how_to_get(name: str) -> str:
    """Return a sentence saying how the player gets the named tank, for the tank index."""
    t = TANKS[name]
    if not t["parents"]:
        return "Starting tank"
    if t["unlock"] == "rank":
        return f"Reach rank {P.BLAST_LORD_RANK}, then evolve"
    if t["unlock"] == "quest":
        text = next(q[1] for q in P.UNIQUE_QUESTS if q[5] == name)
        return f"Quest: {text}"
    if t["price"] > 0:
        return f"Buy in the Shop for {t['price']:,} gems"
    return "Evolve for free"


def buy_tank(profile: dict, name: str) -> bool:
    """Buy a tank with gems. Return whether it was bought."""
    t = TANKS[name]
    if t["price"] <= 0 or name in profile["unlocked_tanks"] or profile["gems"] < t["price"]:
        return False
    profile["gems"] -= t["price"]
    profile["unlocked_tanks"].append(name)
    return True


def buy_skin(profile: dict, name: str) -> bool:
    """Buy a skin with gems. Return whether it was bought."""
    for skin, _col, price in P.SKINS:
        if skin == name and skin not in profile["skins"] and profile["gems"] >= price:
            profile["gems"] -= price
            profile["skins"].append(skin)
            return True
    return False


def record_run(profile: dict, score: float, level: int, kills: int) -> list[str]:
    """Record a finished run and award gems and ranks. Return messages to show."""
    msgs = []
    old_rank = rank(profile)
    profile["total_score"] += int(score)
    profile["total_kills"] += kills
    profile["best_score"] = max(profile["best_score"], int(score))
    profile["best_level"] = max(profile["best_level"], level)
    gems = P.death_gems(score)
    profile["gems"] += gems
    if gems:
        msgs.append(f"+{gems:,} gems for your score")
    new_rank = rank(profile)
    if new_rank > old_rank:
        msgs.append(f"Rank up! You are now {P.rank_name(new_rank)}")
        if old_rank < P.BLAST_LORD_RANK <= new_rank:
            msgs.append("Blast Lord unlocked!")
    return msgs
