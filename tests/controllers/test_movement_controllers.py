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


"""
Unit tests for the MovementController architecture
"""

import math
from unittest.mock import create_autospec

from panda3d.core import LPoint3d, LQuaterniond, LVector3d

from cosmonium.components.elements.surfaces import FlatSurface
from cosmonium.controllers.base import MovementController
from cosmonium.controllers.position import CartesianMovementController, FlatSurfaceMovementController
from cosmonium.engine.pyengine.anchors import CartesianAnchor
from cosmonium.ships import ShipBase


class MockAnchor(CartesianAnchor):
    body = None
    visible = None


def make_mock_anchor():
    """Create a bare mock anchor with a mock body attached."""
    mock_anchor = create_autospec(MockAnchor, spec_set=True, instance=True)
    mock_body = create_autospec(ShipBase, spec_set=True, instance=True)
    mock_anchor.body = mock_body
    return mock_anchor


def make_mock_terrain():
    """Create a bare mock FlatSurface terrain."""
    return create_autospec(FlatSurface, spec_set=True, instance=True)


class TestMovementController:
    """Test base MovementController functionality"""

    def test_init(self):
        """Test initialization"""
        mock_anchor = make_mock_anchor()
        controller = MovementController(mock_anchor)
        assert controller.anchor is not None
        assert controller.context is None

    def test_should_update_when_visible(self):
        """Test update check when anchor is visible"""
        mock_anchor = make_mock_anchor()
        mock_anchor.visible = True
        controller = MovementController(mock_anchor)
        assert controller.should_update(0, 0) is True

    def test_should_not_update_when_invisible(self):
        """Test update check when anchor is invisible"""
        mock_anchor = make_mock_anchor()
        mock_anchor.visible = False
        controller = MovementController(mock_anchor)
        assert controller.should_update(0, 0) is False

    def test_set_state(self):
        """Test animation state is delegated to body"""
        mock_anchor = make_mock_anchor()
        controller = MovementController(mock_anchor)
        controller.set_state('moving')
        mock_anchor.body.set_state.assert_called_once_with('moving')

    def test_orbit_rot_camera_property(self):
        """Test orbit_rot_camera compatibility property reads from body"""
        mock_anchor = make_mock_anchor()
        controller = MovementController(mock_anchor)
        result = controller.orbit_rot_camera
        assert isinstance(result, bool)


class TestCartesianMovementController:
    """Test CartesianMovementController functionality"""

    def test_set_and_get_position(self):
        """Test set_frame_position delegates to anchor"""
        mock_anchor = make_mock_anchor()
        controller = CartesianMovementController(mock_anchor)
        position = LPoint3d(1, 2, 3)
        mock_anchor.get_frame_position.return_value = position
        controller.set_frame_position(position)
        result = controller.get_frame_position()
        mock_anchor.set_frame_position.assert_called_once_with(position)
        assert result == position

    def test_delta_movement(self):
        """Test delta adds to current frame position"""
        mock_anchor = make_mock_anchor()
        controller = CartesianMovementController(mock_anchor)
        initial = LPoint3d(0, 0, 0)
        delta = LVector3d(1, 1, 1)
        mock_anchor.get_frame_position.return_value = initial
        controller.delta(delta)
        mock_anchor.set_frame_position.assert_called_once_with(initial + delta)

    def test_step_relative(self):
        """Test step_relative moves forward along orientation"""
        mock_anchor = make_mock_anchor()
        controller = CartesianMovementController(mock_anchor)
        mock_anchor.get_frame_position.return_value = LPoint3d(0, 0, 0)
        mock_anchor.get_frame_orientation.return_value = LQuaterniond.ident_quat()
        controller.step_relative(10.0)
        expected = LPoint3d(0, 0, 0) + LQuaterniond.ident_quat().xform(LVector3d.forward()) * 10.0
        mock_anchor.set_frame_position.assert_called_once_with(expected)

    def test_turn_relative(self):
        """Test turn_relative rotates around vertical axis"""
        mock_anchor = make_mock_anchor()
        controller = CartesianMovementController(mock_anchor)
        initial_orientation = LQuaterniond.ident_quat()
        mock_anchor.get_frame_orientation.return_value = initial_orientation
        controller.turn_relative(math.pi / 2)
        mock_anchor.set_frame_orientation.assert_called_once()
        new_orientation = mock_anchor.set_frame_orientation.call_args[0][0]
        # Rotation by 90° around Z should give ~90° heading
        assert abs(new_orientation.get_hpr().x - 90) < 0.001

    def test_local_position(self):
        """Test set_local_position and get_local_position delegate to anchor"""
        mock_anchor = make_mock_anchor()
        controller = CartesianMovementController(mock_anchor)
        position = LPoint3d(5, 10, 15)
        mock_anchor.get_local_position.return_value = position
        controller.set_local_position(position)
        result = controller.get_local_position()
        mock_anchor.set_local_position.assert_called_once_with(position)
        assert result == position

    def test_absolute_orientation(self):
        """Test set_absolute_orientation and get_absolute_orientation delegate to anchor"""
        mock_anchor = make_mock_anchor()
        controller = CartesianMovementController(mock_anchor)
        orientation = LQuaterniond()
        orientation.set_from_axis_angle_rad(math.pi / 4, LVector3d.up())
        mock_anchor.get_absolute_orientation.return_value = orientation
        controller.set_absolute_orientation(orientation)
        result = controller.get_absolute_orientation()
        mock_anchor.set_absolute_orientation.assert_called_once_with(orientation)
        assert result == orientation


class TestFlatSurfaceMovementController:
    """Test FlatSurfaceMovementController functionality"""

    def test_init(self):
        """Test flat surface controller stores terrain reference"""
        mock_anchor = make_mock_anchor()
        mock_terrain = make_mock_terrain()
        controller = FlatSurfaceMovementController(mock_anchor, mock_terrain)
        assert controller.terrain is mock_terrain
        assert controller.altitude == 0.0

    def test_position_initialization(self):
        """Test init() calls set_altitude and update on the anchor"""
        mock_anchor = make_mock_anchor()
        mock_anchor.get_local_position.return_value = LPoint3d(0, 0, 0)
        mock_anchor.get_frame_position.return_value = LPoint3d(0, 0, 0)
        mock_terrain = make_mock_terrain()
        mock_terrain.get_height_under.return_value = 0.0
        controller = FlatSurfaceMovementController(mock_anchor, mock_terrain)
        controller.init()
        mock_anchor.update.assert_called_once_with(0, 0)
        assert controller.get_position() == LPoint3d(0, 0, 0)

    def test_set_altitude(self):
        """Test set_altitude applies terrain height and stores altitude"""
        mock_anchor = make_mock_anchor()
        mock_anchor.get_local_position.return_value = LPoint3d(0, 0, 0)
        mock_anchor.get_frame_position.return_value = LPoint3d(0, 0, 0)
        mock_terrain = make_mock_terrain()
        mock_terrain.get_height_under.return_value = 0.0
        controller = FlatSurfaceMovementController(mock_anchor, mock_terrain)
        controller.set_altitude(50.0)
        assert controller.altitude == 50.0
        mock_anchor.set_frame_position.assert_called_with(LPoint3d(0, 0, 50.0))

    def test_set_position(self):
        """Test set_local_position applies x/y and terrain+altitude for z"""
        mock_anchor = make_mock_anchor()
        mock_anchor.get_local_position.return_value = LPoint3d(0, 0, 0)
        mock_anchor.get_frame_position.return_value = LPoint3d(0, 0, 0)
        mock_terrain = make_mock_terrain()
        mock_terrain.get_height_under.return_value = 0.0
        controller = FlatSurfaceMovementController(mock_anchor, mock_terrain)
        controller.altitude = 50.0
        controller.set_local_position(LPoint3d(10, 20, 0))
        # set_frame_position is called twice with the same LPoint3d object (mutated in place);
        # verify two calls were made and the final position has x=10, y=20, z=terrain+altitude=50
        assert mock_anchor.set_frame_position.call_count == 2
        final_pos = mock_anchor.set_frame_position.call_args[0][0]
        assert final_pos == LPoint3d(10, 20, 50.0)
