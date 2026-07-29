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


import builtins

from .. import settings
from .pyscene.scenemanager import SceneManagerBase  # noqa: F401

if settings.c_scene_manager:
    try:
        from cosmonium_engine import CameraHolder as C_CameraHolder
        from cosmonium_engine import DynamicSceneManager, RegionSceneManager, StaticSceneManager
    except ImportError as e:
        import logging

        logging.warning("Could not load Scene Manager C++ implementation, fallback on Python implementation")
        logging.warning(e)
        from .pyscene.scenemanager import DynamicSceneManager, RegionSceneManager, StaticSceneManager

        C_CameraHolder = None
else:
    from .pyscene.scenemanager import DynamicSceneManager, RegionSceneManager, StaticSceneManager  # noqa: F401

    C_CameraHolder = None


def remove_main_region(camera):
    region = None
    for dr in builtins.base.win.get_display_regions():
        drcam = dr.get_camera()
        if drcam == camera:
            region = dr
            break
    if region is not None:
        builtins.base.win.remove_display_region(region)
        region.set_active(False)
