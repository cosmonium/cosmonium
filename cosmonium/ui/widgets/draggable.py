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

"""Base classes for modern UI widgets."""

from __future__ import annotations

from direct.gui.DirectGuiBase import DGG


class DraggableWidgetMixin:
    """
    Mixin for making widgets draggable.

    Widgets can be dragged by binding mouse events to drag handlers.
    """

    def __init__(self):
        """Initialize draggable properties."""
        self.draggable = True
        self.drag_start = None
        self.drag_task_name = None
        self.drag_limits = None

    def setup_dragging(self, drag_widget):
        """
        Setup dragging for a widget.
        This method can be called mutiple times.

        Args:
            drag_widget: The DirectGUI widget to make draggable (e.g., title frame)
        """

        drag_widget.bind(DGG.B1PRESS, self._start_drag)
        drag_widget.bind(DGG.B1RELEASE, self._stop_drag)

    def cleanup_drag(self):
        """Cancel any running drag task and reset drag state."""
        if self.drag_task_name is not None:
            self.base.taskMgr.remove(self.drag_task_name)
            self.drag_task_name = None
        self.drag_start = None

    def _start_drag(self, event):
        """Start dragging operation."""
        if not self.draggable:
            return

        if not self.base.mouseWatcherNode.hasMouse():
            return

        # Get mouse position
        mpos = self.base.mouseWatcherNode.get_mouse()

        # Get current position relative to parent
        if self.instance is not None:
            current_pos = self.instance.parent.get_relative_point(self.base.render2d, (mpos.get_x(), 0, mpos.get_y()))
            self.drag_start = current_pos - self.instance.get_pos()

            # Add drag task with a unique name to avoid conflicts when multiple windows are open
            self.drag_task_name = "drag-widget-task-{}".format(id(self))
            self.base.taskMgr.add(self._drag_task, self.drag_task_name, -1)

    def _drag_task(self, task):
        """Drag task that runs each frame."""
        if not self.base.mouseWatcherNode.has_mouse():
            return task.again

        # Get current mouse position
        mpos = self.base.mouseWatcherNode.get_mouse()

        if self.instance is not None:
            current_pos = self.instance.parent.get_relative_point(self.base.render2d, (mpos.get_x(), 0, mpos.get_y()))

            # Calculate new position
            pos = current_pos - self.drag_start

            # Apply limits if set
            if self.drag_limits is not None:
                min_x, max_x, max_z, min_z = self.drag_limits
                new_pos = (min(max(pos[0], min_x), max_x), 0, max(min(pos[2], max_z), min_z))
            else:
                new_pos = (pos[0], 0, pos[2])

            self.instance.set_pos(new_pos)

        return task.again

    def _stop_drag(self, event):
        """Stop dragging operation."""
        if self.drag_task_name is not None:
            self.base.taskMgr.remove(self.drag_task_name)
            self.drag_task_name = None

    def set_draggable(self, draggable):
        """
        Enable or disable dragging.

        Args:
            draggable: True to enable dragging, False to disable
        """
        self.draggable = draggable

    def set_drag_limits(self, limits):
        """
        Set drag limits to constrain widget movement.

        Args:
            limits: New dragging limits
        """
        self.drag_limits = limits
