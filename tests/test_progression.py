import itertools

from tankgame.data import progression as P


def test_xp_curve_increases():
    vals = [P.xp_to_next(lv) for lv in range(1, P.MAX_LEVEL)]
    assert all(b > a for a, b in itertools.pairwise(vals))


def test_total_xp_ranges():
    assert 1000 < P.total_xp_for_level(15) < 3000
    assert 20000 < P.total_xp_for_level(45) < 40000
    assert 300_000 < P.total_xp_for_level(150) < 2_000_000


def test_level_for_xp_round_trip():
    for lv in (1, 2, 15, 42, 99, 150):
        assert P.level_for_xp(P.total_xp_for_level(lv)) == lv
    assert P.level_for_xp(10**12) == P.MAX_LEVEL


def test_stat_points_allow_full_build_only_with_caps():
    total = P.stat_points_for_level(P.MAX_LEVEL)
    assert total > P.BASE_CAP * len(P.STATS)  # more than base caps hold
    assert total <= sum(P.MAX_CAPS.values())  # max caps can hold everything


def test_max_caps_match_original():
    assert P.MAX_CAPS == {
        "dmg": 12,
        "bspd": 13,
        "reload": 12,
        "bhp": 11,
        "maxhp": 12,
        "regen": 11,
        "speed": 13,
        "body": 12,
    }


def test_ranks():
    assert P.rank_for_score(0) == 1
    assert P.rank_for_score(P.rank_threshold(10)) == 10
    assert P.rank_for_score(10**12) == P.RANK_COUNT
