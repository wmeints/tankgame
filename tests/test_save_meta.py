import copy

from tankgame import meta, save
from tankgame.data import progression as P
from tankgame.data.tanks import TANKS


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


def test_save_path_per_os(monkeypatch, tmp_path):
    monkeypatch.setattr(save.Path, "home", lambda: tmp_path)
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(save.sys, "platform", "win32")
    assert save.default_save_path() == tmp_path / "Roaming" / "tankgame" / "save.json"
    monkeypatch.setattr(save.sys, "platform", "darwin")
    expected = tmp_path / "Library" / "Application Support" / "tankgame" / "save.json"
    assert save.default_save_path() == expected
    monkeypatch.setattr(save.sys, "platform", "linux")
    assert save.default_save_path() == tmp_path / "xdg" / "tankgame" / "save.json"
    monkeypatch.delenv("XDG_DATA_HOME")
    assert save.default_save_path() == tmp_path / ".local" / "share" / "tankgame" / "save.json"


def test_legacy_save_is_read_then_moved(monkeypatch, tmp_path):
    monkeypatch.setattr(save.Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(save.sys, "platform", "darwin")
    prof = fresh()
    prof["gems"] = 4321
    save.save(prof, save.legacy_save_path())
    assert save.load()["gems"] == 4321
    save.save(save.load())
    assert save.default_save_path().exists()
    prof["gems"] = 1
    save.save(prof)
    assert save.load()["gems"] == 1


def test_how_to_get_names_every_unlock_route():
    assert meta.how_to_get("Basic") == "Starting tank"
    assert meta.how_to_get("Scout") == "Evolve for free"
    assert meta.how_to_get("Railgun") == "Buy in the Shop for 75,000 gems"
    assert meta.how_to_get("Blast Lord") == f"Reach rank {P.BLAST_LORD_RANK}, then evolve"
    assert meta.how_to_get("Twinblast") == "Quest: Destroy 1,000 triangles"
    assert all(meta.how_to_get(name) for name in TANKS)


def test_ultraship_is_a_quest_reward():
    prof = fresh()
    meta.ensure_quests(prof)
    assert not meta.tank_unlocked(prof, "Ultraship")
    meta.quest_event(prof, "kill", 300)
    assert meta.tank_unlocked(prof, "Ultraship")
