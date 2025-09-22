#!/bin/bash

pyinstaller --name=missilecommand \
    --onefile \
    --add-data="src/missilecommand/assets/DSEG14Classic-Regular.ttf:missilecommand/assets" \
    --add-data="src/missilecommand/assets/__init__.py:missilecommand/assets" \
    --add-data="src/missilecommand/assets/bonus-city.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/brzzz.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/city-count.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/demo.in:missilecommand/assets" \
    --add-data="src/missilecommand/assets/diiuuu.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/explosion.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/flyer.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/gameover.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/launch.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/low-ammo.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/silo-count.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/smartbomb.wav:missilecommand/assets" \
    --add-data="src/missilecommand/assets/spritesheet.png:missilecommand/assets" \
    assets/pyinstaller/main.py
