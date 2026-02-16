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

"""Shadow system package.

This package provides a comprehensive shadow rendering system with support for:
- Standard shadow maps
- Parallel Split Shadow Maps (PSSM)
- Ring shadows
- Sphere shadows (analytic)

The shadow system follows a strategy pattern where different shadow techniques
are encapsulated in separate modules for better maintainability.

Modules:
    base: Base classes and interfaces
    projector: Shadow projection and frustum calculations
    buffer_creator: Shadow map buffer creation and management
    shadowmap: Standard shadow map implementation
    pssm: Parallel Split Shadow Map implementation
    ring: Ring shadow implementation
    sphere: Sphere shadow implementation
    manager: Shadow management and coordination classes
"""
