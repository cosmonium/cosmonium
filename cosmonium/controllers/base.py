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


class MovementController:
    """
    Controller for object movement operations.
    """

    context = None
    kinetic_mover = False
    position_mover = False

    def __init__(self, anchor):
        self.anchor = anchor

    # Lifecycle methods
    def init(self):
        """Initializes the controller after the universe is loaded and the anchor is ready to be controlled."""
        pass

    def should_update(self, time, dt):
        """
        Determines if the controller should update this cycle.

        Args:
            time: The time of the simulation expressed in Julian days.
            dt: The interval since the last cycle in seconds.

        Returns:
            True if update should be called, False otherwise.
        """
        return self.anchor.visible

    def update(self, time, dt):
        """
        Updates the physical properties of the object (e.g., position, rotation).

        Args:
            time (float): The time of the simulation expressed in Julian days.
            dt (float): The interval since the last cycle in seconds.
        """
        pass

    def update_obs(self, observer):
        """
        Updates the properties of the object related to the actual position of the observer.
        The anchor's update_obs() method is called before this method.

        Args:
            observer: The current observer (camera).
        """
        pass

    def check_visibility(self, frustum, pixel_size):
        """
        Checks the visibility of the object.
        The anchor's check_visibility() method is called before this method.

        Args:
            frustum: Frustum of the current camera.
            pixel_size: The size factor of a pixel on the screen.
        """
        pass

    def check_and_create_instance(self, camera_pos, camera_rot):
        """
        Updates the instance of the object in the scene, if the anchor is resolved.
        The anchor's check_and_create_instance() method is called before this method.

        Args:
            camera_pos: Absolute position of the camera.
            camera_rot: Absolute rotation of the camera.
        """
        pass

    def check_and_update_instance(self, camera_pos, camera_rot):
        """
        Update instance of the object in the scene, if the anchor is resolved
        The actual check_and_update_instance() method of the anchor will be called before this method

        Args:
            camera_pos: Absolute position of the camera.
            camera_rot: Absolute rotation of the camera.
        """
        pass

    def activate(self):
        """Activate the controller"""
        pass

    def feedback(self):
        """Provide feedback from the physics system"""
        pass

    def set_state(self, new_state):
        """Set animation state"""
        self.anchor.body.set_state(new_state)

    @property
    def orbit_rot_camera(self):
        """Compatibility with existing code"""
        return self.anchor.body.orbit_rot_camera
