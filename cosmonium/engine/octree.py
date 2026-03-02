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

"""Octree spatial partitioning structure.

This module provides the OctreeNode class for efficient spatial partitioning.
It attempts to import the optimized C++ implementation from the cosmonium_engine module,
falling back to the pure Python implementation from the pyengine submodule if the C++
extension is not available.
"""


try:
    from cosmonium_engine import OctreeNode, Settings

    c_settings = Settings.get_global_ptr()
except ImportError as e:
    print("WARNING: Could not load Octree C implementation, fallback on python implementation")
    print("\t", e)
    from .pyengine.octree import OctreeNode

    c_settings = None


__all__ = ["OctreeNode", "c_settings"]
