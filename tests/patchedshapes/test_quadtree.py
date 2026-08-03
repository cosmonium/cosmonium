#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


from unittest.mock import Mock

from panda3d.core import LVector3d

from cosmonium.patchedshapes.lodresult import LodResult
from cosmonium.patchedshapes.quadtree import QuadTreeNode


def create_mock_patch():
    """Create a mock patch object for QuadTreeNode testing."""
    mock = Mock(spec_set=['x0', 'x1', 'y0', 'y1'])
    mock.x0 = 0
    mock.x1 = 1
    mock.y0 = 0
    mock.y1 = 1
    return mock


def create_mock_bounds():
    """Create a mock bounding box."""
    return Mock(spec_set=[])


def create_mock_culling_frustum(patch_in_view=True, bb_in_view=True):
    """Create a mock culling frustum for visibility tests."""
    mock = Mock(spec_set=['is_patch_in_view', 'is_bb_in_view'])
    mock.is_patch_in_view.return_value = patch_in_view
    mock.is_bb_in_view.return_value = bb_in_view
    return mock


def create_mock_lod_control(should_split=False, should_merge=False, should_instanciate=True, should_remove=False):
    """Create a mock LOD control for testing."""
    mock = Mock(spec_set=['should_split', 'should_merge', 'should_instanciate', 'should_remove'])
    mock.should_split.return_value = should_split
    mock.should_merge.return_value = should_merge
    mock.should_instanciate.return_value = should_instanciate
    mock.should_remove.return_value = should_remove
    return mock


class TestQuadTreeNode:
    """Test suite for QuadTreeNode class."""

    def test_initialization(self):
        """Test QuadTreeNode initialization."""
        patch = create_mock_patch()
        bounds = create_mock_bounds()
        centre = LVector3d(0.5, 0.5, 0)
        offset_vector = LVector3d(0, 0, 1)

        node = QuadTreeNode(
            patch=patch,
            lod=0,
            density=32,
            centre=centre,
            length=1.0,
            offset_vector=offset_vector,
            offset=0,
            bounds=bounds,
        )

        assert node.patch == patch
        assert node.lod == 0
        assert node.density == 32
        assert node.centre == centre
        assert node.length == 1.0
        assert node.offset_vector == offset_vector
        assert node.offset == 0
        assert node.bounds == bounds
        assert node.children == []
        assert node.shown is False
        assert node.visible is False
        assert node.instance_ready is False

    def test_set_shown(self):
        """Test setting shown state."""
        node = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())

        node.set_shown(True)
        assert node.shown is True

        node.set_shown(False)
        assert node.shown is False

    def test_set_instance_ready(self):
        """Test setting instance ready state."""
        node = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())

        node.set_instance_ready(True)
        assert node.instance_ready is True

        node.set_instance_ready(False)
        assert node.instance_ready is False

    def test_add_child(self):
        """Test adding children to a node."""
        parent = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())
        child1 = QuadTreeNode(create_mock_patch(), 1, 32, LVector3d(), 0.5, LVector3d(), 0, create_mock_bounds())
        child2 = QuadTreeNode(create_mock_patch(), 1, 32, LVector3d(), 0.5, LVector3d(), 0, create_mock_bounds())

        parent.add_child(child1)
        parent.add_child(child2)

        assert len(parent.children) == 2
        assert child1 in parent.children
        assert child2 in parent.children
        assert len(parent.children_bb) == 2
        assert len(parent.children_offset_vector) == 2
        assert len(parent.children_offset) == 2

    def test_remove_children(self):
        """Test removing all children from a node."""
        parent = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())
        child = QuadTreeNode(create_mock_patch(), 1, 32, LVector3d(), 0.5, LVector3d(), 0, create_mock_bounds())

        parent.add_child(child)
        assert len(parent.children) == 1

        parent.remove_children()

        assert len(parent.children) == 0
        assert len(parent.children_bb) == 0
        assert len(parent.children_offset_vector) == 0
        assert len(parent.children_offset) == 0

    def test_can_merge_children_no_children(self):
        """Test that nodes without children cannot merge."""
        node = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())

        assert node.can_merge_children() is False

    def test_can_merge_children_leaf_children(self):
        """Test that nodes with leaf children can merge."""
        parent = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())

        for i in range(4):
            child = QuadTreeNode(create_mock_patch(), 1, 32, LVector3d(), 0.5, LVector3d(), 0, create_mock_bounds())
            parent.add_child(child)

        assert parent.can_merge_children() is True

    def test_can_merge_children_with_grandchildren(self):
        """Test that nodes with grandchildren cannot merge."""
        parent = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())

        for i in range(4):
            child = QuadTreeNode(create_mock_patch(), 1, 32, LVector3d(), 0.5, LVector3d(), 0, create_mock_bounds())
            parent.add_child(child)

        # Add a grandchild to one of the children
        grandchild = QuadTreeNode(create_mock_patch(), 2, 32, LVector3d(), 0.25, LVector3d(), 0, create_mock_bounds())
        parent.children[0].add_child(grandchild)

        assert parent.can_merge_children() is False

    def test_in_patch(self):
        """Test checking if a coordinate is inside the patch."""
        patch = create_mock_patch()
        node = QuadTreeNode(patch, 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())
        # Set bounds on the node directly (as QuadTreeNode accesses them)
        node.x0, node.x1 = 0, 1
        node.y0, node.y1 = 0, 1

        assert node.in_patch(0.5, 0.5) is True
        assert node.in_patch(0, 0) is True
        assert node.in_patch(1, 1) is True
        assert node.in_patch(-0.1, 0.5) is False
        assert node.in_patch(1.1, 0.5) is False
        assert node.in_patch(0.5, -0.1) is False
        assert node.in_patch(0.5, 1.1) is False

    def test_check_visibility_visible(self):
        """Test visibility check when patch is in view."""
        node = QuadTreeNode(
            create_mock_patch(), 0, 32, LVector3d(0.5, 0.5, 1.0), 1.0, LVector3d(0, 0, 1), 0, create_mock_bounds()
        )
        culling_frustum = create_mock_culling_frustum(patch_in_view=True)
        model_camera_pos = LVector3d(0.5, 0.5, 10.0)

        node.check_visibility(culling_frustum, (0.5, 0.5), model_camera_pos, LVector3d(), 9.0, 0.01)

        assert node.visible is True
        assert node.patch_in_view is True
        assert node.distance > 0
        assert node.apparent_size is not None

    def test_check_visibility_not_visible(self):
        """Test visibility check when patch is not in view."""
        node = QuadTreeNode(
            create_mock_patch(), 0, 32, LVector3d(0.5, 0.5, 1.0), 1.0, LVector3d(0, 0, 1), 0, create_mock_bounds()
        )
        culling_frustum = create_mock_culling_frustum(patch_in_view=False)
        model_camera_pos = LVector3d(0.5, 0.5, 10.0)

        node.check_visibility(culling_frustum, (2.0, 2.0), model_camera_pos, LVector3d(), 9.0, 0.01)

        assert node.visible is False
        assert node.patch_in_view is False

    def test_are_children_visibles_no_children(self):
        """Test children visibility when there are no children."""
        node = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())
        culling_frustum = create_mock_culling_frustum()

        assert node.are_children_visibles(culling_frustum) is True

    def test_are_children_visibles_some_visible(self):
        """Test children visibility when some are visible."""
        parent = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())
        child = QuadTreeNode(create_mock_patch(), 1, 32, LVector3d(), 0.5, LVector3d(), 0, create_mock_bounds())
        parent.add_child(child)

        culling_frustum = create_mock_culling_frustum(bb_in_view=True)

        assert parent.are_children_visibles(culling_frustum) is True

    def test_are_children_visibles_none_visible(self):
        """Test children visibility when none are visible."""
        parent = QuadTreeNode(create_mock_patch(), 0, 32, LVector3d(), 1.0, LVector3d(), 0, create_mock_bounds())
        child = QuadTreeNode(create_mock_patch(), 1, 32, LVector3d(), 0.5, LVector3d(), 0, create_mock_bounds())
        parent.add_child(child)

        culling_frustum = create_mock_culling_frustum(bb_in_view=False)

        assert parent.are_children_visibles(culling_frustum) is False

    def test_check_lod_leaf_should_split(self):
        """Test LOD check for a leaf that should split."""
        node = QuadTreeNode(
            create_mock_patch(), 0, 32, LVector3d(0.5, 0.5, 1.0), 2.0, LVector3d(0, 0, 1), 0, create_mock_bounds()
        )
        node.set_instance_ready(True)

        culling_frustum = create_mock_culling_frustum(patch_in_view=True, bb_in_view=True)
        lod_control = create_mock_lod_control(should_split=True)
        lod_result = LodResult()

        node.check_lod(
            lod_result, culling_frustum, (0.5, 0.5), LVector3d(0.5, 0.5, 10.0), LVector3d(), 10.0, 0.01, lod_control
        )

        assert node in lod_result.to_split
        assert len(lod_result.to_show) == 0
        assert len(lod_result.to_remove) == 0

        # Verify mock interactions
        culling_frustum.is_patch_in_view.assert_called_with(node)
        lod_control.should_split.assert_called_once_with(node, 20, 10)

    def test_check_lod_leaf_should_show(self):
        """Test LOD check for a leaf that should be shown."""
        node = QuadTreeNode(
            create_mock_patch(), 0, 32, LVector3d(0.5, 0.5, 1.0), 2.0, LVector3d(0, 0, 1), 0, create_mock_bounds()
        )

        culling_frustum = create_mock_culling_frustum(patch_in_view=True)
        lod_control = create_mock_lod_control(should_split=False, should_instanciate=True)
        lod_result = LodResult()

        node.check_lod(
            lod_result, culling_frustum, (0.5, 0.5), LVector3d(0.5, 0.5, 10.0), LVector3d(), 10.0, 0.01, lod_control
        )

        assert node in lod_result.to_show
        assert len(lod_result.to_split) == 0

        # Verify mock interactions
        lod_control.should_split.assert_called_once_with(node, 20, 10.0)
        lod_control.should_instanciate.assert_called_once_with(node, 20, 10)

    def test_check_lod_shown_should_remove(self):
        """Test LOD check for a shown node that should be removed."""
        node = QuadTreeNode(
            create_mock_patch(), 0, 32, LVector3d(0.5, 0.5, 1.0), 2.0, LVector3d(0, 0, 1), 0, create_mock_bounds()
        )
        node.set_shown(True)

        culling_frustum = create_mock_culling_frustum(patch_in_view=True)
        lod_control = create_mock_lod_control(should_remove=True)
        lod_result = LodResult()

        node.check_lod(
            lod_result, culling_frustum, (0.5, 0.5), LVector3d(0.5, 0.5, 10.0), LVector3d(), 10.0, 0.01, lod_control
        )

        assert node in lod_result.to_remove

        # Verify mock interactions
        lod_control.should_split.assert_called_once_with(node, 20, 10.0)
        lod_control.should_remove.assert_called_once_with(node, 20, 10)

    def test_check_lod_invisible_shown_should_remove(self):
        """Test LOD check for an invisible shown node."""
        node = QuadTreeNode(
            create_mock_patch(), 0, 32, LVector3d(0.5, 0.5, 1.0), 2.0, LVector3d(0, 0, 1), 0, create_mock_bounds()
        )
        node.set_shown(True)

        culling_frustum = create_mock_culling_frustum(patch_in_view=False)
        lod_control = create_mock_lod_control()
        lod_result = LodResult()

        node.check_lod(
            lod_result, culling_frustum, (5.0, 5.0), LVector3d(5.0, 5.0, 10.0), LVector3d(), 5.0, 0.01, lod_control
        )

        assert node in lod_result.to_remove

    def test_check_lod_parent_should_merge(self):
        """Test LOD check for a parent that should merge its children."""
        parent = QuadTreeNode(
            create_mock_patch(), 0, 32, LVector3d(0.5, 0.5, 1.0), 1.0, LVector3d(0, 0, 1), 0, create_mock_bounds()
        )

        # Add leaf children
        for i in range(4):
            child = QuadTreeNode(create_mock_patch(), 1, 32, LVector3d(), 0.5, LVector3d(), 0, create_mock_bounds())
            parent.add_child(child)

        culling_frustum = create_mock_culling_frustum(patch_in_view=True)
        lod_control = create_mock_lod_control(should_merge=True)
        lod_result = LodResult()

        parent.check_lod(
            lod_result, culling_frustum, (0.5, 0.5), LVector3d(0.5, 0.5, 10.0), LVector3d(), 9.0, 0.01, lod_control
        )

        assert parent in lod_result.to_merge

        # Verify mock interactions
        lod_control.should_merge.assert_called_once()

    def test_check_lod_parent_recurse_to_children(self):
        """Test LOD check recursion to children when not merging."""
        parent = QuadTreeNode(
            create_mock_patch(), 0, 32, LVector3d(0.5, 0.5, 1.0), 1.0, LVector3d(0, 0, 1), 0, create_mock_bounds()
        )

        # Add leaf children
        for i in range(4):
            child = QuadTreeNode(create_mock_patch(), 1, 32, LVector3d(), 0.5, LVector3d(), 0, create_mock_bounds())
            parent.add_child(child)

        culling_frustum = create_mock_culling_frustum(patch_in_view=True)
        lod_control = create_mock_lod_control(should_merge=False, should_instanciate=True)
        lod_result = LodResult()

        parent.check_lod(
            lod_result, culling_frustum, (0.5, 0.5), LVector3d(0.5, 0.5, 10.0), LVector3d(), 9.0, 0.01, lod_control
        )

        # Parent should not be in any list
        assert parent not in lod_result.to_merge
        assert parent not in lod_result.to_show

        # Children should be processed (shown)
        assert len(lod_result.to_show) == 4
