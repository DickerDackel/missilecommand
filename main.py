#!/usr/bin/env python3

import platform
import sys
import missilecommand.__main__

if sys.platform == 'emscripten':
    platform.window.canvas.style.imageRendering = 'pixelated'

sys.path.append('src')

missilecommand.__main__.main()
