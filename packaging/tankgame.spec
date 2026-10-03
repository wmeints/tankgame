# PyInstaller spec for the standalone game: `uv run --group build pyinstaller packaging/tankgame.spec`
#
# Windows and Linux get a single executable in dist/. macOS gets dist/Tank Game.app.
# All builds are windowed, so no console window opens next to the game.
import sys

from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ["launcher.py"],
    # Scenes are imported lazily inside functions; collect them all to be safe.
    hiddenimports=collect_submodules("tankgame"),
    excludes=["tkinter", "unittest", "pydoc"],
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="tankgame", console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="tankgame")
    app = BUNDLE(
        coll,
        name="Tank Game.app",
        bundle_identifier="io.github.wmeints.tankgame",
        info_plist={"NSHighResolutionCapable": True},
    )
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="tankgame", console=False)
