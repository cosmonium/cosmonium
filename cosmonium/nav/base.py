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


from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from direct.showbase import DirectObject
    from direct.showbase.ShowBase import ShowBase

    from ..camera.base import CameraController, CameraHolder
    from ..controllers.base import MovementController
    from ..objects.stellarobject import StellarObject


class NavigationController(ABC):
    """Abstract base class for all navigation controllers.

    A navigation controller translates user input (keyboard, mouse, etc.) into
    camera and scene-body movement.  Subclasses override :meth:`register_events`,
    :meth:`remove_events`, and :meth:`update` to provide concrete behaviour.
    """

    def __init__(self) -> None:
        self.base: Optional[ShowBase] = None
        self.camera: Optional[CameraHolder] = None
        self.camera_controller: Optional[CameraController] = None
        self.controller: Optional[MovementController] = None

    def init(
        self, base: ShowBase, camera: CameraHolder, camera_controller: CameraController, controller: MovementController
    ) -> None:
        self.base = base
        self.camera = camera
        self.camera_controller = camera_controller
        self.controller = controller

    def set_target(self, target: StellarObject) -> None:
        """Set the navigation target (e.g. a celestial body for surface walk).

        The base implementation is a no-op. Subclasses that require a target
        (i.e. require_target returns True) must override this method.

        Args:
            target: The target scene object.
        """

    @abstractmethod
    def get_name(self) -> str:
        """Return a human-readable name for this navigation mode.

        Returns:
            Display name string.
        """

    @abstractmethod
    def get_id(self) -> str:
        """Return the identifier for this navigation mode.

        Returns:
            Identifier string.
        """

    def require_target(self) -> bool:
        """Whether this controller requires a target body to be active.

        Returns:
            True if a target must be provided before activation.
        """
        return False

    def require_controller(self) -> bool:
        """Whether this controller requires a movement controller to be active.

        Returns:
            True if a movement controller must be provided.
        """
        return False

    @abstractmethod
    def register_events(self, event_ctrl: DirectObject) -> None:
        """Attach input event handlers.

        Args:
            event_ctrl: An object that exposes accept(event, callback, args)
                (typically the Panda3D ShowBase instance).

        Note:
            Each call to register_events **must** be paired with a
            corresponding call to remove_events when this controller is
            deactivated to avoid stale event handlers.
            Instead of relying on the event_ctrl, this class should inherit
            from DirectObject and use its own event handler.
        """

    @abstractmethod
    def remove_events(self, event_ctrl: DirectObject) -> None:
        """Detach previously registered input event handlers.

        Args:
            event_ctrl: The same object passed to register_events.
        """

    def set_controller(self, controller: MovementController) -> None:
        """Replace the movement controller.

        Args:
            controller: New movement controller.
        """
        self.controller = controller

    def set_camera_controller(self, camera_controller: CameraController) -> None:
        """Replace the camera orientation controller.

        Args:
            camera_controller: New camera controller.
        """
        self.camera_controller = camera_controller

    def stash_position(self) -> None:
        """Convert internally tracked positions to absolute frame before a
        reference point change (called by the engine on anchor switches).

        The base implementation is a no-op. Subclasses that track positions
        (e.g. InteractiveNavigationController) override this method.
        """

    def pop_position(self) -> None:
        """Convert internally tracked positions back to the local frame after a
        reference-frame change.

        The base implementation is a no-op. Subclasses that track positions
        (e.g. InteractiveNavigationController) override this method.
        """

    def update(self, time: float, dt: float) -> None:
        """Advance the navigation state for one simulation tick.

        The base implementation is a no-op. Concrete navigation controllers
        must override this method to process input and move the observer.

        Args:
            time: Current simulation time (seconds).
            dt: Elapsed time since the previous tick (seconds).
        """
