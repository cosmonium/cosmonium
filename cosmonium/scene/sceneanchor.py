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


from .. import settings


if settings.c_scene_manager:
    try:
        from cosmonium_engine import SceneAnchor, AbsoluteSceneAnchor, ObserverSceneAnchor, SceneAnchorCollection
    except ImportError as e:
        print("WARNING: Could not load Scene Anchor C implementation, fallback on python implementation")
        print("\t", e)
        from .pyscene.sceneanchor import SceneAnchor, AbsoluteSceneAnchor, ObserverSceneAnchor, SceneAnchorCollection
else:
    from .pyscene.sceneanchor import SceneAnchor, AbsoluteSceneAnchor, ObserverSceneAnchor  # noqa: F401
    from .pyscene.sceneanchor import SceneAnchorCollection  # noqa: F401
