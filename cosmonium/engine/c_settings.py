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

"""C++ engine settings.

This module provides access to the C++ engine settings through the Settings
class. The application uses the singletion instance of this class to copy
the user settings to the C++ engine.
It attempts to import the optimized C++ implementation from the
cosmonium_engine module. If the C++ extension is not available, c_settings
will be set to None.
"""

import logging

try:
    from cosmonium_engine import Settings

    c_settings = Settings.get_global_ptr()
    logging.info("Using C++ Engine")
except ImportError as e:
    logging.warning("Could not load C++ Engine, fallback on Python implementation")
    logging.warning(e)
    c_settings = None


__all__ = ["c_settings"]
