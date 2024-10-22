# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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
        from cosmonium_engine import StaticSceneManager, DynamicSceneManager, RegionSceneManager
    except ImportError as e:
        print("WARNING: Could not load Scene Manager C implementation, fallback on python implementation")
        print("\t", e)
        from .pyscene.scenemanager import StaticSceneManager, DynamicSceneManager, RegionSceneManager

        C_CameraHolder = None
else:
    from .pyscene.scenemanager import StaticSceneManager, DynamicSceneManager, RegionSceneManager  # noqa: F401

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
