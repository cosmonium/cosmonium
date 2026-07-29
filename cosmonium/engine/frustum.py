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

"""View frustum for visibility culling.

This module provides the InfiniteFrustum class for determining object visibility
in the scene. It attempts to import the optimized C++ implementation from the
cosmonium_engine module, falling back to the pure Python implementation from
the pyengine submodule if the C++ extension is not available.
"""

try:
    from cosmonium_engine import InfiniteFrustum
except ImportError as e:
    import logging

    logging.warning("Could not load Frustum C++ implementation, fallback on Python implementation")
    logging.warning(e)
    from .pyengine.frustum import InfiniteFrustum


__all__ = ["InfiniteFrustum"]
