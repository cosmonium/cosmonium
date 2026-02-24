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
Unit tests for collision physics controllers
"""

from unittest.mock import create_autospec

from panda3d.core import LPoint3, LPoint3d

from cosmonium.engine.pyengine.anchors import CartesianAnchor
from cosmonium.entities.entity import Entity
from cosmonium.physics.collision import ReactBodyController
from cosmonium.scene.pyscene.sceneanchor import SceneAnchor


class MockAnchor(CartesianAnchor):
    body = None
    scene_anchor = None
    visible = None


class MockBody:
    ship_object = None
    scene_anchor = None


class MockEntity(Entity):
    instance = None


class MockNodePath:
    def get_pos(self): ...

    def set_pos(self, pos): ...


class MockSceneAnchor(SceneAnchor):
    instance = None


def make_mock_anchor():
    """Create a mock anchor with nested mock dependencies."""
    mock_anchor = create_autospec(MockAnchor, spec_set=True, instance=True)
    mock_body = create_autospec(MockBody, spec_set=True, instance=True)
    mock_scene_anchor = create_autospec(MockSceneAnchor, spec_set=True, instance=True)
    mock_scene_instance = create_autospec(MockNodePath, spec_set=True, instance=True)
    mock_scene_anchor.instance = mock_scene_instance
    mock_anchor.scene_anchor = mock_scene_anchor
    mock_body.ship_object = None
    mock_anchor.body = mock_body
    return mock_anchor


class TestReactBodyController:
    """Test ReactBodyController functionality"""

    def test_update_without_ship_object(self):
        """Test update when no ship object exists"""
        mock_anchor = make_mock_anchor()
        mock_anchor.get_local_position.return_value = LPoint3d(0, 0, 0)
        mock_anchor.scene_anchor.instance.get_pos.return_value = LPoint3(10, 20, 30)

        controller = ReactBodyController(mock_anchor)
        controller.update(0, 0.1)

        # Anchor position should be updated with scene position
        mock_anchor.set_local_position.assert_called_once_with(LPoint3(10, 20, 30))
        mock_anchor.update.assert_called_once_with(0, 0.1)

    def test_update_with_ship_object(self):
        """Test update when ship object exists"""
        mock_anchor = make_mock_anchor()
        mock_anchor.get_local_position.return_value = LPoint3d(1, 2, 3)

        mock_ship_instance = create_autospec(MockNodePath, spec_set=True, instance=True)
        mock_ship_instance.get_pos.return_value = LPoint3(5, 10, 15)

        mock_ship_object = create_autospec(MockEntity, spec_set=True, instance=True)
        mock_ship_object.instance = mock_ship_instance

        mock_anchor.body.ship_object = mock_ship_object

        controller = ReactBodyController(mock_anchor)
        controller.update(0, 0.1)

        # ship instance position should be reset to origin
        mock_ship_instance.set_pos.assert_called_once_with(LPoint3())
        # anchor position should be the sum of local + scene position
        mock_anchor.set_local_position.assert_called_once_with(LPoint3d(6, 12, 18))
        mock_anchor.update.assert_called_once_with(0, 0.1)

    def test_set_local_position(self):
        """Test setting local position directly"""
        mock_anchor = make_mock_anchor()
        controller = ReactBodyController(mock_anchor)

        position = LPoint3d(7, 8, 9)
        controller.set_local_position(position)

        mock_anchor.set_local_position.assert_called_once_with(position)
