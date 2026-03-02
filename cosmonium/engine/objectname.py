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


"""
Object name registry and management.
This module provides the CatalogRegistry, ObjectName, and ObjectNames classes for managing
object names in the simulation. It attempts to import optimized C++ implementations
from the cosmonium_engine module, falling back to pure Python implementations from the
pyengine submodule if the C++ extension is not available.
"""

try:
    from cosmonium_engine import CatalogRegistry, ObjectName, ObjectNames
except ImportError as e:
    print("WARNING: Could not load ObjectName C implementation, fallback on python implementation")
    print("\t", e)
    from .pyengine.objectname import CatalogRegistry, ObjectName, ObjectNames


__all__ = ["CatalogRegistry", "ObjectName", "ObjectNames"]
