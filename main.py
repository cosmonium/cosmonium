#!/usr/bin/env python
#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


import os
import sys

# Disable stdout block buffering
sys.stdout.flush()
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

# Add lib/ directory to import path to be able to load the c++ libraries
sys.path.insert(1, 'lib')
# Add third-party/ directory to import path to be able to load the external libraries
sys.path.insert(1, 'third-party')
# CEFPanda and glTF modules aree not at top level
sys.path.insert(1, 'third-party/cefpanda')
sys.path.insert(1, 'third-party/gltf')


if getattr(sys, 'frozen', False) and sys.platform == "win32":
    # Create a fake win32com.gen_py package as Panda3D freeze tool does not set up a proper __path__
    # for win32com to create its cache package for COM object
    # It's not needed by Cosmonium, but still required to be able to import win32
    import types

    from panda3d.core import ExecutionEnvironment

    gen_py = types.ModuleType("win32com.gen_py")
    gen_py.__path__ = [ExecutionEnvironment.getEnvironmentVariable("MAIN_DIR")]
    sys.modules[gen_py.__name__] = gen_py


if __name__ == '__main__':
    from cosmonium.app.main import main

    main()
