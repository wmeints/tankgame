import pytest

from tankgame.ai import DIFFICULTY, PACE_STATS, bot_caps
from tankgame.data import progression as P


@pytest.mark.parametrize("difficulty", list(DIFFICULTY))
def test_bot_caps_hold_pace_stats(difficulty):
    caps = bot_caps(difficulty)
    assert set(caps) == set(P.STATS)
    for stat in PACE_STATS:
        assert caps[stat] <= DIFFICULTY[difficulty]["pace"]


def test_easier_bots_move_and_fire_slower():
    easy, normal, hard = (bot_caps(d) for d in ("easy", "normal", "hard"))
    for stat in PACE_STATS:
        assert easy[stat] < normal[stat] < hard[stat]
    assert normal["speed"] < P.BASE_CAP and normal["reload"] < P.BASE_CAP
