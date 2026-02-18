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
Unit tests for physics-based movement controllers (kinetic controllers)
"""

import math
from unittest.mock import create_autospec

from panda3d.core import LPoint3d, LQuaterniond, LVector3, NodePath

from cosmonium.engine.pyengine.anchors import CartesianAnchor
from cosmonium.entities.entity import Entity
from cosmonium.physics.bullet import BulletMovementController, KineticMovementController


class MockAnchor(CartesianAnchor):
    body = None
    visible = None


class MockBody:
    anchor = None
    ship_object = None
    physics_node = None
    physics_instance = None


class MockEntity(Entity):
    instance = None
    scene_anchor = None


class MockBulletCharacterControllerNode:
    def get_pos(self): ...

    def set_linear_movement(self, movement, is_local): ...

    def set_pos(self, pos): ...


def make_mock_anchor():
    """Create a bare mock anchor."""
    return create_autospec(MockAnchor, spec_set=True, instance=True)


def make_mock_body(anchor=None):
    """Create a mock body linked to a mock anchor."""
    mock_body = create_autospec(MockBody, spec_set=True, instance=True)
    if anchor is None:
        anchor = make_mock_anchor()
    mock_body.anchor = anchor
    anchor.body = mock_body
    return mock_body


def make_mock_physics_node():
    """Create a mock BulletCharacterControllerNode."""
    return create_autospec(MockBulletCharacterControllerNode, spec_set=True, instance=True)


class TestKineticMovementController:
    """Test KineticMovementController functionality"""

    def test_init(self):
        """Test initialization"""
        mock_body = make_mock_body()
        mock_body.physics_node = None
        controller = KineticMovementController(mock_body)
        assert controller.entity is not None
        assert controller.anchor is not None
        assert controller.kinetic_mover is True
        assert controller.position_mover is False


class TestBulletMovementController:
    """Test BulletMovementController functionality"""

    def test_init(self):
        """Test initialization"""
        mock_body = make_mock_body()
        mock_body.physics_node = None
        controller = BulletMovementController(mock_body)
        assert controller.entity is not None
        assert controller.anchor is not None
        assert controller.kinetic_mover is True
        assert controller.position_mover is False

    def test_set_local_position_with_physics_node(self):
        """Test set_local_position delegates to physics node when present"""
        mock_body = make_mock_body()
        mock_physics_node = make_mock_physics_node()
        mock_body.physics_node = mock_physics_node
        mock_body.physics_instance = None
        mock_body.ship_object = None

        controller = BulletMovementController(mock_body)
        position = LPoint3d(5, 10, 15)
        controller.set_local_position(position)

        mock_physics_node.set_pos.assert_called_once_with(position)

    def test_set_local_position_without_physics_node(self):
        """Test set_local_position falls back to anchor when no physics node"""
        mock_anchor = make_mock_anchor()
        mock_body = make_mock_body(anchor=mock_anchor)
        mock_body.physics_node = None

        controller = BulletMovementController(mock_body)
        position = LPoint3d(5, 10, 15)
        controller.set_local_position(position)

        mock_anchor.set_frame_position.assert_called_once_with(position)

    def test_set_speed_relative(self):
        """Test velocity-based movement sets linear movement on physics node"""
        mock_anchor = make_mock_anchor()
        mock_anchor.get_frame_orientation.return_value = LQuaterniond.ident_quat()
        mock_body = make_mock_body(anchor=mock_anchor)
        mock_physics_node = make_mock_physics_node()
        mock_body.physics_node = mock_physics_node
        mock_body.physics_instance = None
        mock_body.ship_object = None

        controller = BulletMovementController(mock_body)
        speed = LVector3(1, 2, 3)
        controller.set_speed_relative(speed)

        mock_physics_node.set_linear_movement.assert_called_once_with(LQuaterniond.ident_quat().xform(speed), True)

    def test_turn_relative(self):
        """Test relative rotation updates frame orientation on anchor"""
        mock_anchor = make_mock_anchor()
        initial_orientation = LQuaterniond.ident_quat()
        mock_anchor.get_frame_orientation.return_value = initial_orientation
        mock_body = make_mock_body(anchor=mock_anchor)
        mock_body.physics_node = None
        controller = BulletMovementController(mock_body)
        controller.turn_relative(math.pi / 4)

        mock_anchor.set_frame_orientation.assert_called_once()
        new_orientation = mock_anchor.set_frame_orientation.call_args[0][0]
        assert new_orientation != initial_orientation

    def test_feedback_with_physics_instance(self):
        """Test feedback updates anchor position from physics simulation"""
        mock_anchor = make_mock_anchor()
        mock_body = make_mock_body(anchor=mock_anchor)
        mock_physics_node = make_mock_physics_node()
        mock_body.physics_node = mock_physics_node
        mock_body.ship_object = None
        mock_physics_instance = create_autospec(NodePath, spec_set=True, instance=True)
        mock_physics_instance.get_pos.return_value = LPoint3d(10, 20, 30)
        mock_body.physics_instance = mock_physics_instance
        controller = BulletMovementController(mock_body)
        controller.feedback()

        mock_physics_instance.get_pos.assert_called_once_with()
        mock_anchor.set_frame_position.assert_called_once_with(LPoint3d(10, 20, 30))
