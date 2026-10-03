import copy
import random
from types import SimpleNamespace

from tankgame import config as C
from tankgame import save
from tankgame.data.tanks import ANY, TANKS, evolution_options
from tankgame.world import World


def test_parents_exist_and_are_lower_level():
    for t in TANKS.values():
        for p in t["parents"]:
            if p == ANY:
                continue
            assert p in TANKS, f"{t['name']}: unknown parent {p}"
            assert TANKS[p]["level"] < t["level"], f"{t['name']} <= parent {p}"


def test_every_tank_reachable_from_basic():
    seen, todo = set(), ["Basic"]
    while todo:
        cur = todo.pop()
        if cur in seen:
            continue
        seen.add(cur)
        todo.extend(o["name"] for o in evolution_options(cur, 150))
    assert seen == set(TANKS)


def test_original_evolution_levels():
    assert TANKS["Railgun"]["level"] == 105 and TANKS["Railgun"]["price"] == 75000
    assert {TANKS[n]["level"] for n in ("Spammer", "Scout", "Double", "Freezer", "Grinder")} == {15}
    assert TANKS["Double Freezer"]["level"] == 37
    assert TANKS["Orbitron Sr."]["level"] == 150


def test_every_tank_can_fire():
    random.seed(0)
    prof = copy.deepcopy(save.DEFAULT_PROFILE)
    w = World(prof)
    w.player_hurt = 0
    p = w.player
    p.add_xp(10**7)
    for name in TANKS:
        p.set_tank(name)
        p.firing = True
        p.immune = 0
        for _ in range(90):
            w.update(C.DT)
        if TANKS[name]["barrels"]:
            assert len(w.bullets) + len(w.beams) > 0, name
        assert p.alive or w.dead


def _flame(damage):
    return SimpleNamespace(kind="flame", damage=damage, owner=None)


def test_burn_keeps_higher_rate_while_active():
    w = World(copy.deepcopy(save.DEFAULT_PROFILE))
    tank = w.tanks[1]
    w._apply_status(_flame(50), tank)
    w._apply_status(_flame(2), tank)
    assert tank.burn_dps == 200


def test_burn_rate_resets_after_burn_expires():
    w = World(copy.deepcopy(save.DEFAULT_PROFILE))
    tank = w.tanks[1]
    w._apply_status(_flame(50), tank)
    tank.burn_timer = 0
    w._apply_status(_flame(2), tank)
    assert tank.burn_dps == 8
