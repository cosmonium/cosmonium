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


from ...events import EventsDispatcher
from ..managers.window_manager import WindowManager
from ..widgets.tips_overlay import TipsOverlay


def _show_tips_window():
    window_manager = WindowManager.instance()
    if window_manager.get_window_by_id('tips'):
        return
    gui = window_manager.gui
    tips = gui.tips_config
    if not tips:
        return
    overlay = TipsOverlay(gui, tips)
    window_manager.open_window(overlay, 'tips')


def register_tips_window():
    dispatcher = EventsDispatcher.instance()
    dispatcher.register('gui-show-tips', _show_tips_window)
