from itertools import combinations

from tankgame.data.tanks import ANY, TANKS
from tankgame.scenes.index import CARDS, EDGES, MAP_H, MAP_W


def test_every_tank_has_a_card_inside_the_map():
    assert set(CARDS) == set(TANKS)
    for rect in CARDS.values():
        assert rect.left >= 0 and rect.top >= 0
        assert rect.right <= MAP_W and rect.bottom <= MAP_H


def test_cards_do_not_overlap():
    for a, b in combinations(CARDS.values(), 2):
        assert not a.colliderect(b)


def test_map_reads_left_to_right():
    for parent, child in EDGES:
        assert CARDS[parent].right < CARDS[child].left
    level_15 = min(CARDS[n].right for n, t in TANKS.items() if t["level"] == 15)
    for name, t in TANKS.items():
        if ANY in t["parents"]:
            assert CARDS[name].left > level_15
