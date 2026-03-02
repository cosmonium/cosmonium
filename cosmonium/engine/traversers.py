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

"""Visitor pattern traversers for the anchor hierarchy.

This module provides traverser classes that implement the visitor pattern
for traversing and processing the anchor graph. It attempts to import
the optimized C++ implementations from the cosmonium_engine module, falling
back to the pure Python implementations from the pyengine submodule if the
C++ extension is not available.
"""


try:
    from cosmonium_engine import (
        FindClosestSystemTraverser,
        FindLightSourceTraverser,
        FindShadowCastersTraverser,
        UpdateTraverser,
    )
except ImportError as e:
    print("WARNING: Could not load Traversers C implementation, fallback on python implementation")
    print("\t", e)
    from .pyengine.traversers import (
        FindClosestSystemTraverser,
        FindLightSourceTraverser,
        FindShadowCastersTraverser,
        UpdateTraverser,
    )


__all__ = [
    "FindClosestSystemTraverser",
    "FindLightSourceTraverser",
    "FindShadowCastersTraverser",
    "UpdateTraverser",
]
