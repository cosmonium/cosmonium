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


from .. import settings

if settings.c_scene_manager:
    try:
        from cosmonium_engine import AbsoluteSceneAnchor, ObserverSceneAnchor, SceneAnchor, SceneAnchorCollection
    except ImportError as e:
        import logging

        logging.warning("Could not load Scene Anchor C++ implementation, fallback on Python implementation")
        logging.warning(e)
        from .pyscene.sceneanchor import AbsoluteSceneAnchor, ObserverSceneAnchor, SceneAnchor, SceneAnchorCollection
else:
    from .pyscene.sceneanchor import AbsoluteSceneAnchor, ObserverSceneAnchor, SceneAnchor, SceneAnchorCollection

__all__ = [
    "AbsoluteSceneAnchor",
    "ObserverSceneAnchor",
    "SceneAnchor",
    "SceneAnchorCollection",
]
