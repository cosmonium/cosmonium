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

"""Object-name search logic class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

from direct.task.TaskManagerGlobal import taskMgr

if TYPE_CHECKING:
    from ...objects.stellarobject import StellarObject
    from ..gui import Gui


class NameSearchController:
    """Debounced object-name search and suggestion list management.

    Implements partial object-name search, search debouncing, suggestion list and selection management.
    """

    def __init__(
        self, gui: Gui, query_delay: float, on_suggestions_updated: Callable, max_results: Optional[int] = None
    ):
        self.gui = gui
        self.query_delay = query_delay
        self.on_suggestions_updated = on_suggestions_updated
        self.max_results = max_results
        # List of objects matching the current query, as (name, object) tuples,
        # name being the display name of the object.
        self.current_list: List[Tuple[str, StellarObject]] = []
        # Current selection index in the current_list, or None if no selection is made.
        self.current_selection: Optional[int] = None
        # Handle of the pending debounced update task, or None if no update is pending.
        self.completion_task: Optional[str] = None

    def reset(self) -> None:
        """Clear the search state and cancel any pending debounced update."""
        self.current_list = []
        self.current_selection = None
        self.cancel_pending()

    def cancel_pending(self) -> None:
        if self.completion_task is not None:
            taskMgr.remove(self.completion_task)
            self.completion_task = None

    def update_query(self, text: str) -> None:
        """Start a debounced lookup of the matches for the current entry text."""
        self.cancel_pending()
        self.completion_task = taskMgr.doMethodLater(
            self.query_delay, self._fire_update, 'debounce-search-task', extraArgs=[text]
        )

    def _fire_update(self, text: str) -> None:
        """Perform the actual lookup of the matches for the current entry text."""
        if text:
            results = self.gui.list_objects(text)
            if self.max_results is not None:
                results = results[: self.max_results]
            self.current_list = results
        else:
            self.current_list = []
        self.current_selection = None
        self.completion_task = None
        self.on_suggestions_updated()

    def move_selection(self, increment: int) -> None:
        """Move the highlighted suggestion by `increment`, wrapping around."""
        if not self.current_list:
            return
        if self.current_selection is None:
            new_selection = 0
        else:
            new_selection = (self.current_selection + increment) % len(self.current_list)
        self.current_selection = new_selection
        self.on_suggestions_updated()

    def resolve(self, text: str) -> Optional[StellarObject]:
        """Return the body to select: either the highlighted suggestion, or an exact-name lookup."""
        if self.current_selection is not None:
            if self.current_selection < len(self.current_list):
                return self.current_list[self.current_selection][1]
            return None
        return self.gui.get_object(text)
