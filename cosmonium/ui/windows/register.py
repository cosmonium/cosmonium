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


from .about import register_about_window
from .help import register_help_window
from .info import register_info_window
from .license import register_license_window
from .objecteditor import register_object_editor_window
from .open_script import register_open_script_window
from .preferences import register_preferences_window
from .select_screenshots import register_select_screenshots_window
from .ship_editor import register_ship_editor_window
from .time import register_time_editor_window


def register_windows():
    register_about_window()
    register_help_window()
    register_info_window()
    register_license_window()
    register_object_editor_window()
    register_open_script_window()
    register_preferences_window()
    register_select_screenshots_window()
    register_ship_editor_window()
    register_time_editor_window()
