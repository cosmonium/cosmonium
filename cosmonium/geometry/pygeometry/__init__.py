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

"""Python geometry module for Cosmonium.

This package provides comprehensive geometry generation functions for 3D
graphics, including spheres, patches, tiles, and various mesh primitives.

Sub-modules:
    core: Core utility functions for geometry creation
    primitives: Basic geometric primitives (boxes, cubes)
    spheres: Sphere generation (UV, icosahedral, displacement-mapped)
    patches: UV patch generation for spherical surfaces
    cube_patches: Cube-mapped patch generation
    tiles: Flat tile and patch generation
    tessellation: Tessellation configuration and primitive generation
    rings: Ring geometry for planetary rings
    ui: Geometry for user interface elements

Note:
    The package attempts to use optimized C implementations for performance-critical
    functions, with Python fallbacks if the C extensions are not available.
"""
