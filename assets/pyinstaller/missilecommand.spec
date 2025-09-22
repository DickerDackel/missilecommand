# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/missilecommand/assets/DSEG14Classic-Regular.ttf', 'missilecommand/assets'),
        ('src/missilecommand/assets/__init__.py', 'missilecommand/assets'),
        ('src/missilecommand/assets/bonus-city.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/brzzz.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/city-count.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/demo.in', 'missilecommand/assets'),
        ('src/missilecommand/assets/diiuuu.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/explosion.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/flyer.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/gameover.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/launch.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/low-ammo.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/silo-count.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/smartbomb.wav', 'missilecommand/assets'),
        ('src/missilecommand/assets/spritesheet.png', 'missilecommand/assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='missilecommand',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
