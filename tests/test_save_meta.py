import copy

from tankgame import meta, save
from tankgame.data import progression as P


def fresh():
    return copy.deepcopy(save.DEFAULT_PROFILE)


def test_save_round_trip(tmp_path):
    prof = fresh()
    prof["gems"] = 1234
    prof["unlocked_tanks"].append("Railgun")
    path = tmp_path / "save.json"
    save.save(prof, path)
    assert save.load(path) == prof


def test_old_save_migrates(tmp_path):
    path = tmp_path / "save.json"
    path.write_text('{"version": 0, "gems": 5, "caps": {"dmg": 2}}')
    prof = save.load(path)
    assert prof["gems"] == 5
    assert prof["caps"]["dmg"] == 2 and prof["caps"]["speed"] == 0
    assert prof["version"] == save.SAVE_VERSION


def test_cap_purchase_limits():
    prof = fresh()
    prof["gems"] = 10**9
    while meta.buy_cap(prof, "bhp"):
        pass
    assert meta.stat_cap(prof, "bhp") == P.MAX_CAPS["bhp"]


def test_codes_once():
    prof = fresh()
    g = prof["gems"]
    assert "gems" in meta.redeem_code(prof, "headstart")
    assert prof["gems"] == g + 25000
    assert "already" in meta.redeem_code(prof, "HEADSTART")
    assert "Invalid" in meta.redeem_code(prof, "NOPE")


def test_quests_complete_and_pay():
    prof = fresh()
    meta.ensure_quests(prof)
    g = prof["gems"]
    msgs = meta.quest_event(prof, "shape:triangle", 1000)
    assert "Twinblast" in prof["unlocked_tanks"]
    assert any("Twinblast" in m for m in msgs)
    assert prof["gems"] >= g


def test_blast_lord_rank_lock():
    prof = fresh()
    assert not meta.tank_unlocked(prof, "Blast Lord")
    prof["total_score"] = P.rank_threshold(P.BLAST_LORD_RANK)
    assert meta.tank_unlocked(prof, "Blast Lord")
