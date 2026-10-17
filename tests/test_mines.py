import copy
import math
import random

from tankgame import config as C
from tankgame import save
from tankgame.data.tanks import TANKS
from tankgame.entities.bullet import Bullet
from tankgame.world import World


def _world():
    random.seed(1)
    w = World(copy.deepcopy(save.DEFAULT_PROFILE))
    w.tanks = w.tanks[:2]
    w.shapes = []
    layer, victim = w.tanks
    layer.set_tank("Mine Layer")
    victim.brain = None
    layer.immune = victim.immune = 0
    layer.x, layer.y = 1000, 1000
    victim.x, victim.y = 2500, 2500
    return w, layer, victim


def _lay(layer):
    barrel = next(b for b in layer.tdef["barrels"] if b["kind"] == "mine")
    layer.fire(barrel)
    mine = layer.mines[-1]
    layer.x += 1000  # step away so the layer's body stays clear of the test
    return mine


def _armed(layer):
    mine = _lay(layer)
    mine.arm = 0
    mine.vx = mine.vy = 0
    return mine


def test_every_mine_tank_has_a_mine_cap():
    for t in TANKS.values():
        if any(b["kind"] == "mine" for b in t["barrels"]):
            assert t["mines"] > 0, t["name"]


def test_mine_stops_and_arms():
    _, layer, _ = _world()
    mine = _lay(layer)
    assert mine.arm > 0
    for _ in range(60):
        mine.update(C.DT)
    assert math.hypot(mine.vx, mine.vy) < 1
    assert mine.arm == 0
    assert mine.alive


def test_armed_mine_explodes_under_an_enemy():
    w, layer, victim = _world()
    mine = _armed(layer)
    victim.x, victim.y = mine.x, mine.y
    hp = victim.hp
    w.update(C.DT)
    assert not mine.alive
    assert victim.hp < hp


def test_unarmed_mine_ignores_contact():
    w, layer, victim = _world()
    mine = _lay(layer)
    victim.x, victim.y = mine.x, mine.y
    hp = victim.hp
    w.update(C.DT)
    assert mine.alive
    assert victim.hp == hp


def test_mine_ignores_its_owner():
    w, layer, _ = _world()
    mine = _armed(layer)
    layer.x, layer.y = mine.x, mine.y
    w.update(C.DT)
    assert mine.alive


def test_laying_past_the_cap_fizzles_the_oldest():
    _, layer, _ = _world()
    first = _lay(layer)
    for _ in range(layer.tdef["mines"]):
        _lay(layer)
    assert len(layer.mines) == layer.tdef["mines"]
    assert not first.alive
    assert first.explode_radius == 0


def test_expired_mine_fizzles():
    _, layer, _ = _world()
    mine = _lay(layer)
    mine.life = C.DT / 2
    mine.update(C.DT)
    assert not mine.alive
    assert mine.explode_radius == 0


def test_shot_down_mine_detonates():
    w, layer, victim = _world()
    mine = _armed(layer)
    victim.x, victim.y = mine.x + mine.radius + victim.radius + 10, mine.y
    hp = victim.hp
    w.bullets.append(
        Bullet(owner=victim, x=mine.x, y=mine.y, vx=0, vy=0, radius=5, damage=1e6, hp=1e6, life=1)
    )
    w.update(C.DT)
    assert not mine.alive
    assert victim.hp < hp


def test_mines_fizzle_when_their_owner_dies():
    _, layer, _ = _world()
    mine = _armed(layer)
    layer.take_damage(1e9, None)
    assert not mine.alive
    assert mine.explode_radius == 0
