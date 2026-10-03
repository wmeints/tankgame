"""The tank evolution tree.

Names, evolution levels, parents and shop prices follow the original Roblox
game's build paths. Barrel layouts are our own interpretation, since the
original's per-tank numbers are not published.

Barrel fields (lengths/widths are relative to the tank radius):
  angle    degrees from the aim direction
  length   barrel length from the tank center
  width    barrel width
  offset   sideways shift (positive = right of the aim direction)
  dmg, reload, speed, bhp, range   multipliers on the tank's stats
  spread   random spread in degrees
  kind     bullet | spike | rocket | laser | freeze | flame
  delay    fraction of the reload to wait before the first shot (staggering)
  pellets  bullets per shot (shotguns)
  size     bullet size multiplier
  recoil   push back on the tank per shot
  flare    draw as a trapezoid that widens toward the muzzle
"""

ANY = "*"  # parent wildcard: available from any tank of level 15 or higher


def B(angle=0.0, length=1.9, width=0.85, offset=0.0, dmg=1.0, reload=1.0,
      speed=1.0, spread=3.0, kind="bullet", delay=0.0, pellets=1, size=1.0,
      recoil=1.0, bhp=1.0, range=1.0, flare=False):
    return dict(angle=angle, length=length, width=width, offset=offset,
                dmg=dmg, reload=reload, speed=speed, spread=spread, kind=kind,
                delay=delay, pellets=pellets, size=size, recoil=recoil,
                bhp=bhp, range=range, flare=flare)


TANKS: dict[str, dict] = {}


def T(name, level, parents, barrels, hp=1.0, speed=1.0, body=1.0, price=0,
      unlock=None, fov=1.0, orbiters=0, grinder=0, invis=False, desc=""):
    TANKS[name] = dict(name=name, level=level, parents=list(parents),
                       barrels=barrels, hp=hp, speed=speed, body=body,
                       price=price, unlock=unlock, fov=fov, orbiters=orbiters,
                       grinder=grinder, invis=invis, desc=desc)


def fan(n, total_angle, **kw):
    """n barrels spread evenly over total_angle degrees."""
    if n == 1:
        return [B(**kw)]
    step = total_angle / (n - 1)
    return [B(angle=-total_angle / 2 + i * step, delay=(i % 2) * 0.5, **kw)
            for i in range(n)]


def ring(n, **kw):
    return [B(angle=i * 360 / n, delay=(i % 2) * 0.5, **kw) for i in range(n)]


def thrusters(**kw):
    return [B(angle=160, length=1.6, width=0.7, dmg=0.35, reload=0.6,
              recoil=2.5, range=0.6, delay=0.0, **kw),
            B(angle=200, length=1.6, width=0.7, dmg=0.35, reload=0.6,
              recoil=2.5, range=0.6, delay=0.5, **kw)]


# --- Start ----------------------------------------------------------------
T("Basic", 1, [], [B()], desc="Where every tank begins.")

# --- Level 15 -------------------------------------------------------------
T("Spammer", 15, ["Basic"],
  [B(width=1.0, length=1.8, reload=0.5, dmg=0.7, spread=12, flare=True)],
  desc="Sprays lots of small bullets.")
T("Scout", 15, ["Basic"],
  [B(length=2.4, width=0.8, reload=1.5, speed=1.5, dmg=1.5, range=1.6)],
  fov=1.15, desc="Long-range sniper.")
T("Double", 15, ["Basic"],
  [B(offset=-0.45, width=0.75, dmg=0.75), B(offset=0.45, width=0.75, dmg=0.75, delay=0.5)],
  desc="Two barrels side by side.")
T("Freezer", 15, ["Basic"],
  [B(kind="freeze", length=1.6, width=1.0, reload=0.08, dmg=0.12, range=0.3,
     spread=22, speed=1.1, flare=True, recoil=0.1)],
  desc="Freezing cone that slows enemies and destroys bullets.")
T("Flame", 15, ["Basic"],
  [B(kind="flame", length=1.6, width=1.0, reload=0.08, dmg=0.1, range=0.3,
     spread=22, speed=1.1, flare=True, recoil=0.1)],
  desc="Sets enemies on fire.")
T("Grinder", 15, ["Basic"], [], hp=1.25, speed=1.05, body=2.5, grinder=8,
  desc="No gun. Spinning blades shred anything you ram.")
T("Slide", 15, ["Basic"], [B()] + thrusters(), speed=1.15,
  desc="Rear thrusters push you forward while you shoot.")

# --- Spammer branch -------------------------------------------------------
T("Thunder", 30, ["Spammer"],
  [B(width=1.1, length=1.9, reload=0.42, dmg=0.7, spread=14, flare=True),
   B(width=1.1, length=1.55, reload=0.42, dmg=0.7, spread=14, flare=True, delay=0.5)],
  desc="Double-stacked machine gun.")
T("Eater", 30, ["Spammer"],
  [B(width=1.2, length=1.9, reload=2.0, dmg=2.6, bhp=2.5, size=1.4, speed=0.8, recoil=3)],
  desc="Fires huge bullets that eat through shapes.")
T("Storm", 42, ["Thunder"],
  [B(width=1.2, length=2.0, reload=0.36, dmg=0.7, spread=16, flare=True),
   B(width=1.2, length=1.7, reload=0.36, dmg=0.7, spread=16, flare=True, delay=0.33),
   B(width=1.2, length=1.4, reload=0.36, dmg=0.7, spread=16, flare=True, delay=0.66)],
  desc="A storm of bullets.")
T("Blaster", 42, ["Spammer", "Thunder"],
  [B(width=1.3, length=1.8, reload=0.9, dmg=0.6, pellets=3, spread=18, flare=True)],
  desc="Every shot is a burst of three.")
T("Devourer", 42, ["Eater"],
  [B(width=1.4, length=2.0, reload=2.5, dmg=4.0, bhp=4.0, size=1.6, speed=0.75, recoil=5)],
  desc="Even bigger bullets.")
T("Shadow", 42, ["Eater", "Hitman"],
  [B(length=2.3, width=0.85, reload=1.4, speed=1.6, dmg=2.0, range=1.6)],
  invis=True, fov=1.2, desc="Turns invisible when standing still.")
T("Ultra-Thunder", 60, ["Thunder", "Storm"],
  [B(width=1.3, length=2.1, reload=0.17, dmg=0.6, spread=18, flare=True)],
  price=15000, desc="Absurd fire rate.")
T("Powerhouse", 60, ["Storm", "Fury", "Double Spiker"],
  [B(width=1.5, length=2.1, reload=2.4, dmg=4.5, bhp=3.5, size=1.6, recoil=6)],
  hp=1.15, desc="One massive cannon.")
T("Splitstorm", 60, ["Shadow"], fan(5, 50, reload=1.0, dmg=0.8, width=0.7),
  desc="Five-way spread.")
T("Beastmode", 60, ["Blaster"], fan(5, 40, reload=0.7, dmg=0.8, width=0.8, flare=True),
  desc="Pure destruction.")
T("Machinima", 60, ["Blaster"],
  [B(width=1.1, reload=0.3, dmg=0.7, spread=12, flare=True),
   B(angle=-35, width=0.9, reload=0.35, dmg=0.6, spread=12, flare=True, delay=0.5),
   B(angle=35, width=0.9, reload=0.35, dmg=0.6, spread=12, flare=True, delay=0.5)],
  price=20000, desc="Three machine guns.")
T("Trilord", 90, ["Splitstorm"],
  ring(3, width=1.2, length=2.0, reload=1.2, dmg=2.2, bhp=2.0, size=1.2),
  hp=1.15, desc="Three heavy cannons.")
T("Railgun", 105, ["Devourer", "Watcher"],
  [B(kind="laser", length=2.6, width=0.7, reload=2.2, dmg=10, range=2.2, spread=0, recoil=4)],
  price=75000, fov=1.3, desc="Instant piercing laser.")
T("Tundra", 130, ["Powerhouse"],
  [B(width=1.6, length=2.2, reload=2.2, dmg=5.5, bhp=4.0, size=1.7, recoil=6),
   B(angle=-90, kind="freeze", length=1.5, width=0.9, reload=0.1, dmg=0.12, range=0.28,
     spread=20, flare=True, recoil=0.05),
   B(angle=90, kind="freeze", length=1.5, width=0.9, reload=0.1, dmg=0.12, range=0.28,
     spread=20, flare=True, recoil=0.05)],
  hp=1.25, desc="Cannon with frost flanks.")
T("Sparta", 130, ["Beastmode", "Machinima"], fan(7, 60, reload=0.6, dmg=0.9, width=0.8, flare=True),
  hp=1.2, desc="Seven-barrel phalanx.")
T("Godfather", 150, ["Ultra-Thunder"],
  [B(angle=a, width=1.2, length=2.0, reload=0.18, dmg=0.6, spread=15, flare=True,
     delay=i * 0.33) for i, a in enumerate((-22, 0, 22))],
  hp=1.2, desc="Three Ultra-Thunders at once.")
T("Orchestra", 150, ["Trilord", "Side Triple"],
  ring(8, width=0.8, reload=0.6, dmg=0.9)
  + [B(offset=-0.4, width=0.7, length=2.2, reload=0.5, dmg=0.9),
     B(offset=0.4, width=0.7, length=2.2, reload=0.5, dmg=0.9, delay=0.5)],
  hp=1.2, desc="Bullets in every direction.")
T("Double Railgun", 150, ["Railgun"],
  [B(kind="laser", offset=-0.45, length=2.6, width=0.6, reload=2.0, dmg=9, range=2.2, spread=0, recoil=3),
   B(kind="laser", offset=0.45, length=2.6, width=0.6, reload=2.0, dmg=9, range=2.2, spread=0,
     recoil=3, delay=0.5)],
  fov=1.3, desc="Two railguns.")

# --- Scout branch ---------------------------------------------------------
T("Hitman", 30, ["Scout"],
  [B(length=2.6, width=0.85, reload=1.7, speed=1.7, dmg=2.1, range=1.8)],
  fov=1.25, desc="Assassin with a long reach.")
T("Wrath", 30, ["Scout"],
  [B(length=2.3, width=0.8, reload=0.8, speed=1.6, dmg=1.2, range=1.5)],
  fov=1.15, desc="Rapid-fire sniper.")
T("Spiker", 30, ["Scout"],
  [B(kind="spike", length=2.0, width=1.0, reload=1.6, speed=0.7, dmg=1.8, bhp=6, size=1.3, range=1.6)],
  desc="Slow spikes that plow through everything.")
T("Buckshot", 30, ["Scout"],
  [B(width=1.1, length=1.8, reload=1.4, dmg=0.45, pellets=6, spread=25, range=0.7,
     speed=1.1, size=0.6, recoil=3, flare=True)],
  desc="Shotgun.")
T("Ace", 42, ["Hitman"],
  [B(length=2.8, width=0.85, reload=1.8, speed=1.9, dmg=2.8, range=2.0)],
  fov=1.35, desc="Elite sniper.")
T("Fury", 42, ["Wrath"],
  [B(length=2.3, width=0.7, offset=-0.35, reload=0.75, speed=1.6, dmg=1.1, range=1.5),
   B(length=2.3, width=0.7, offset=0.35, reload=0.75, speed=1.6, dmg=1.1, range=1.5, delay=0.5)],
  fov=1.15, desc="Twin rapid snipers.")
T("Double Spiker", 42, ["Spiker"],
  [B(kind="spike", length=2.0, width=0.9, offset=-0.45, reload=1.6, speed=0.7, dmg=1.7, bhp=6,
     size=1.2, range=1.6),
   B(kind="spike", length=2.0, width=0.9, offset=0.45, reload=1.6, speed=0.7, dmg=1.7, bhp=6,
     size=1.2, range=1.6, delay=0.5)],
  desc="Two spike launchers.")
T("Double Buckshot", 60, ["Buckshot"],
  [B(width=1.0, length=1.8, offset=-0.45, reload=1.3, dmg=0.45, pellets=6, spread=25, range=0.7,
     speed=1.1, size=0.6, recoil=2, flare=True),
   B(width=1.0, length=1.8, offset=0.45, reload=1.3, dmg=0.45, pellets=6, spread=25, range=0.7,
     speed=1.1, size=0.6, recoil=2, flare=True, delay=0.5)],
  price=20000, desc="Two shotguns.")
T("Watcher", 90, ["Ace"],
  [B(length=3.0, width=0.9, reload=1.9, speed=2.0, dmg=4.0, range=2.4)],
  fov=1.45, desc="Sees and hits from very far away.")
T("Intruder", 90, ["Shadow"],
  [B(length=2.6, width=0.9, reload=1.5, speed=1.8, dmg=3.0, range=1.9)],
  invis=True, fov=1.3, speed=1.1, desc="Invisible assassin.")
T("Megashot", 130, ["Double Buckshot"],
  [B(width=1.5, length=2.0, reload=1.4, dmg=0.6, pellets=14, spread=32, range=0.8,
     speed=1.15, size=0.65, recoil=6, flare=True)],
  hp=1.2, desc="The ultimate shotgun.")

# --- Double branch --------------------------------------------------------
T("Triway", 30, ["Double"], fan(3, 60, width=0.75, dmg=0.8), desc="Three-way shot.")
T("Twinblast", 42, ["Double"],
  [B(offset=-0.45, width=0.9, dmg=1.6, reload=1.3, size=1.3, bhp=1.8),
   B(offset=0.45, width=0.9, dmg=1.6, reload=1.3, size=1.3, bhp=1.8, delay=0.5)],
  unlock="quest", desc="Unlocked by a unique quest.")
T("Triple", 42, ["Triway", "Double"],
  [B(offset=-0.5, width=0.65, length=1.75, dmg=0.7, delay=0.33),
   B(offset=0.5, width=0.65, length=1.75, dmg=0.7, delay=0.66),
   B(width=0.7, length=2.0, dmg=0.7)],
  desc="Three barrels stacked side by side.")
T("Side Triple", 90, ["Triple"],
  [B(offset=-0.5, width=0.65, length=1.75, dmg=0.8, delay=0.33),
   B(offset=0.5, width=0.65, length=1.75, dmg=0.8, delay=0.66),
   B(width=0.7, length=2.0, dmg=0.8),
   B(angle=-90, width=0.75, dmg=0.8, delay=0.5),
   B(angle=90, width=0.75, dmg=0.8, delay=0.5)],
  desc="Triple plus side guns.")

# --- Freezer / Flame ------------------------------------------------------
_FZ = dict(kind="freeze", length=1.6, width=0.9, reload=0.08, dmg=0.12, range=0.3,
           spread=22, flare=True, recoil=0.05)
T("Double Freezer", 37, ["Freezer"], [B(offset=-0.45, **_FZ), B(offset=0.45, **_FZ)],
  desc="Two freeze cones.")
T("Triple Freezer", 55, ["Double Freezer"],
  [B(angle=-25, **_FZ), B(**_FZ), B(angle=25, **_FZ)], desc="Three freeze cones.")
T("Mega Freezer", 80, ["Triple Freezer"],
  [B(kind="freeze", length=1.8, width=1.4, reload=0.05, dmg=0.13, range=0.38,
     spread=30, flare=True, recoil=0.05),
   B(angle=-90, **_FZ), B(angle=90, **_FZ)],
  hp=1.2, desc="A blizzard.")
T("Inferno", 55, ["Flame"],
  [B(kind="flame", offset=-0.45, length=1.7, width=1.0, reload=0.07, dmg=0.11, range=0.34,
     spread=24, flare=True, recoil=0.05),
   B(kind="flame", offset=0.45, length=1.7, width=1.0, reload=0.07, dmg=0.11, range=0.34,
     spread=24, flare=True, recoil=0.05)],
  desc="Twin flamethrowers.")

# --- Grinder branch -------------------------------------------------------
T("Shredder", 35, ["Grinder"], [], hp=1.3, speed=1.08, body=3.0, grinder=10,
  desc="Bigger blades.")
T("Fuse", 47, ["Shredder"], thrusters(), hp=1.35, speed=1.12, body=3.3, grinder=10,
  desc="Thrusters for faster ramming.")
T("Plower", 60, ["Fuse"], [], hp=1.55, speed=1.05, body=4.0, grinder=12,
  desc="Heavy plow.")
T("Smashinator", 60, ["Fuse"], [], hp=1.6, speed=1.1, body=4.5, grinder=14,
  price=25000, desc="Smash everything.")
T("Mega Shredder", 90, ["Plower", "Smashinator"], [], hp=1.8, speed=1.08, body=5.0,
  grinder=16, desc="Huge blades.")
T("Turbine", 130, ["Mega Shredder"], thrusters(), hp=1.9, speed=1.25, body=5.5,
  grinder=16, orbiters=3, desc="Fast, with orbiting blades.")
T("Apollo", 130, ["Mega Shredder"], [], hp=2.3, speed=1.0, body=6.2, grinder=20,
  desc="A walking fortress.")

# --- Slide branch ---------------------------------------------------------
T("Apex", 30, ["Slide"], fan(3, 30, width=0.75, dmg=0.8) + thrusters(), speed=1.2,
  desc="Tri-shot with thrusters.")
T("Blast Lord", 30, ["Slide"],
  [B(kind="rocket", width=1.1, length=1.9, reload=1.6, dmg=2.2, speed=0.55, size=1.2, range=1.4,
     recoil=3)],
  unlock="rank", desc=f"Rockets! Unlocked at rank 10.")
T("Rocket", 42, ["Apex", "Blast Lord"],
  [B(kind="rocket", width=1.0, length=1.9, reload=1.4, dmg=2.0, speed=0.55, range=1.4,
     recoil=2)] + thrusters(),
  speed=1.15, desc="Rocket launcher.")
T("Guardian", 42, ["Apex"],
  [B(offset=-0.4, width=0.7, dmg=0.85), B(offset=0.4, width=0.7, dmg=0.85, delay=0.5),
   B(angle=180, width=0.8, dmg=0.8)],
  hp=1.4, desc="Tough, covers its back.")
T("Phoenix", 130, ["Rocket", "Guardian", "Blast Lord"],
  [B(kind="rocket", angle=a, width=1.0, length=1.9, reload=1.2, dmg=2.4, speed=0.6, range=1.5,
     recoil=1.5, delay=i * 0.33) for i, a in enumerate((-20, 0, 20))] + thrusters(),
  hp=1.25, speed=1.15, desc="Rises from the ashes with rocket barrages.")

# --- Orbitron line (any branch) -------------------------------------------
T("Orbitron Jr.", 60, [ANY], [B(dmg=1.1)], orbiters=2, desc="Two orbiting drones.")
T("Orbitron", 80, ["Orbitron Jr."], [B(dmg=1.2)], orbiters=4, desc="Four orbiting drones.")
T("Side Orbitron", 130, ["Orbitron Jr.", "Orbitron"],
  [B(dmg=1.2), B(angle=-90, dmg=1.0, delay=0.5), B(angle=90, dmg=1.0, delay=0.5)],
  orbiters=6, hp=1.15, desc="Six drones and side guns.")
T("Orbitron Sr.", 150, ["Orbitron", "Side Orbitron"],
  [B(offset=-0.45, width=0.75, dmg=1.1), B(offset=0.45, width=0.75, dmg=1.1, delay=0.5)],
  orbiters=8, hp=1.25, desc="A ring of eight drones.")

# --- Special --------------------------------------------------------------
T("Ultraship", 60, [ANY],
  [B(angle=a, width=0.9, reload=0.5, dmg=0.9, flare=True, delay=(i % 2) * 0.5)
   for i, a in enumerate((45, 135, 225, 315))] + [B(dmg=1.4, width=0.9)],
  orbiters=3, hp=1.2, unlock="wheel", desc="Prize wheel legend.")


def evolution_options(current: str, level: int) -> list[dict]:
    """Tanks the current tank can evolve into at this level (locks not applied)."""
    cur = TANKS[current]
    out = []
    for t in TANKS.values():
        if t["name"] == current or t["level"] > level or t["level"] <= cur["level"]:
            continue
        if current in t["parents"] or (ANY in t["parents"] and cur["level"] >= 15
                                       and ANY not in cur["parents"]
                                       and not cur["name"].startswith("Orbitron")):
            out.append(t)
    return sorted(out, key=lambda t: (t["level"], t["name"]))
