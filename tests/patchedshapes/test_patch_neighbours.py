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

from cosmonium.patchedshapes.patchneighbours import PatchNeighbours, PatchNoNeighbours


def create_mock_patch(x0=0, x1=1, y0=0, y1=1, lod=0):
    """Create a mock patch object for testing."""
    mock = Mock(
        spec_set=[
            'x0',
            'x1',
            'y0',
            'y1',
            'lod',
            'children',
            'tessellation_outer_level',
        ]
    )
    mock.x0 = x0
    mock.x1 = x1
    mock.y0 = y0
    mock.y1 = y1
    mock.lod = lod
    mock.children = []
    mock.tessellation_outer_level = [1, 1, 1, 1]
    return mock


class TestPatchNeighbours:
    """Test suite for PatchNeighbours class."""

    def test_initialization(self):
        """Test that PatchNeighbours initializes correctly."""
        patch = create_mock_patch()
        neighbours = PatchNeighbours(patch)

        assert neighbours.patch == patch
        assert len(neighbours.neighbours) == 4
        for face_neighbours in neighbours.neighbours:
            assert isinstance(face_neighbours, set)
            assert len(face_neighbours) == 0

    def test_add_neighbour(self):
        """Test adding neighbours to different faces."""
        patch = create_mock_patch()
        neighbours = PatchNeighbours(patch)

        north_neighbour = create_mock_patch()
        east_neighbour = create_mock_patch()

        neighbours.add_neighbour(PatchNeighbours.NORTH, north_neighbour)
        neighbours.add_neighbour(PatchNeighbours.EAST, east_neighbour)

        assert north_neighbour in neighbours.neighbours[PatchNeighbours.NORTH]
        assert east_neighbour in neighbours.neighbours[PatchNeighbours.EAST]
        assert len(neighbours.neighbours[PatchNeighbours.SOUTH]) == 0
        assert len(neighbours.neighbours[PatchNeighbours.WEST]) == 0

    def test_add_duplicate_neighbour(self):
        """Test that adding the same neighbour twice doesn't duplicate it."""
        patch = create_mock_patch()
        neighbours = PatchNeighbours(patch)

        neighbour = create_mock_patch()
        neighbours.add_neighbour(PatchNeighbours.NORTH, neighbour)
        neighbours.add_neighbour(PatchNeighbours.NORTH, neighbour)

        assert len(neighbours.neighbours[PatchNeighbours.NORTH]) == 1
        assert neighbour in neighbours.neighbours[PatchNeighbours.NORTH]

    def test_set_neighbours(self):
        """Test setting all neighbours for a face."""
        patch = create_mock_patch()
        neighbours = PatchNeighbours(patch)

        neighbour_set = {create_mock_patch(), create_mock_patch(), create_mock_patch()}
        neighbours.set_neighbours(PatchNeighbours.NORTH, neighbour_set)

        assert neighbours.neighbours[PatchNeighbours.NORTH] == neighbour_set

    def test_get_neighbours(self):
        """Test getting neighbours returns a copy."""
        patch = create_mock_patch()
        neighbours = PatchNeighbours(patch)

        neighbour1 = create_mock_patch()
        neighbour2 = create_mock_patch()
        neighbours.add_neighbour(PatchNeighbours.EAST, neighbour1)
        neighbours.add_neighbour(PatchNeighbours.EAST, neighbour2)

        result = neighbours.get_neighbours(PatchNeighbours.EAST)

        assert isinstance(result, set)
        assert neighbour1 in result
        assert neighbour2 in result
        assert len(result) == 2

    def test_set_all_neighbours(self):
        """Test setting all neighbours at once."""
        patch = create_mock_patch()
        neighbours = PatchNeighbours(patch)

        north = {create_mock_patch()}
        east = {create_mock_patch(), create_mock_patch()}
        south = {create_mock_patch()}
        west = set()

        neighbours.set_all_neighbours(north, east, south, west)

        assert neighbours.neighbours[PatchNeighbours.NORTH] == north
        assert neighbours.neighbours[PatchNeighbours.EAST] == east
        assert neighbours.neighbours[PatchNeighbours.SOUTH] == south
        assert neighbours.neighbours[PatchNeighbours.WEST] == west

    def test_clear_all_neighbours(self):
        """Test clearing all neighbours."""
        patch = create_mock_patch()
        neighbours = PatchNeighbours(patch)

        # Add some neighbours
        neighbours.add_neighbour(PatchNeighbours.NORTH, create_mock_patch())
        neighbours.add_neighbour(PatchNeighbours.EAST, create_mock_patch())

        # Clear them
        neighbours.clear_all_neighbours()

        for face in range(4):
            assert len(neighbours.neighbours[face]) == 0

    def test_get_all_neighbours(self):
        """Test getting all neighbours from all faces."""
        patch = create_mock_patch()
        neighbours = PatchNeighbours(patch)

        n1 = create_mock_patch()
        n2 = create_mock_patch()
        n3 = create_mock_patch()

        neighbours.add_neighbour(PatchNeighbours.NORTH, n1)
        neighbours.add_neighbour(PatchNeighbours.EAST, n2)
        neighbours.add_neighbour(PatchNeighbours.SOUTH, n3)

        all_neighbours = neighbours.get_all_neighbours()

        assert len(all_neighbours) == 3
        assert n1 in all_neighbours
        assert n2 in all_neighbours
        assert n3 in all_neighbours

    def test_get_neighbour_lower_lod(self):
        """Test finding the lowest LOD among neighbours."""
        patch = create_mock_patch(lod=5)
        neighbours = PatchNeighbours(patch)

        n1 = create_mock_patch(lod=3)
        n2 = create_mock_patch(lod=4)
        n3 = create_mock_patch(lod=2)

        neighbours.add_neighbour(PatchNeighbours.NORTH, n1)
        neighbours.add_neighbour(PatchNeighbours.NORTH, n2)
        neighbours.add_neighbour(PatchNeighbours.NORTH, n3)

        lower_lod = neighbours.get_neighbour_lower_lod(PatchNeighbours.NORTH)

        assert lower_lod == 2

    def test_get_neighbour_lower_lod_no_neighbours(self):
        """Test that lower LOD returns patch LOD when no neighbours."""
        patch = create_mock_patch(lod=5)
        neighbours = PatchNeighbours(patch)

        lower_lod = neighbours.get_neighbour_lower_lod(PatchNeighbours.NORTH)

        assert lower_lod == 5

    def test_remove_detached_neighbours_north(self):
        """Test removing neighbours that don't overlap on the north side."""
        patch = create_mock_patch(x0=5, x1=10, y0=5, y1=10)
        neighbours = PatchNeighbours(patch)

        # This neighbour overlaps
        overlapping = create_mock_patch(x0=6, x1=9, y0=10, y1=15)
        # This neighbour doesn't overlap (x range doesn't intersect)
        non_overlapping = create_mock_patch(x0=0, x1=4, y0=10, y1=15)

        neighbours.add_neighbour(PatchNeighbours.NORTH, overlapping)
        neighbours.add_neighbour(PatchNeighbours.NORTH, non_overlapping)

        neighbours.remove_detached_neighbours()

        assert overlapping in neighbours.neighbours[PatchNeighbours.NORTH]
        assert non_overlapping not in neighbours.neighbours[PatchNeighbours.NORTH]

    def test_remove_detached_neighbours_east(self):
        """Test removing neighbours that don't overlap on the east side."""
        patch = create_mock_patch(x0=5, x1=10, y0=5, y1=10)
        neighbours = PatchNeighbours(patch)

        # This neighbour overlaps (y range intersects)
        overlapping = create_mock_patch(x0=10, x1=15, y0=6, y1=9)
        # This neighbour doesn't overlap (y range doesn't intersect)
        non_overlapping = create_mock_patch(x0=10, x1=15, y0=0, y1=4)

        neighbours.add_neighbour(PatchNeighbours.EAST, overlapping)
        neighbours.add_neighbour(PatchNeighbours.EAST, non_overlapping)

        neighbours.remove_detached_neighbours()

        assert overlapping in neighbours.neighbours[PatchNeighbours.EAST]
        assert non_overlapping not in neighbours.neighbours[PatchNeighbours.EAST]


class TestPatchNoNeighbours:
    """Test suite for PatchNoNeighbours class."""

    def test_initialization(self):
        """Test that PatchNoNeighbours initializes correctly."""
        patch = create_mock_patch()
        neighbours = PatchNoNeighbours(patch)

        assert neighbours.patch == patch

    def test_get_neighbours_returns_empty(self):
        """Test that get_neighbours always returns empty list."""
        patch = create_mock_patch()
        neighbours = PatchNoNeighbours(patch)

        result = neighbours.get_neighbours(PatchNoNeighbours.NORTH)

        assert result == set()

    def test_get_all_neighbours_returns_empty(self):
        """Test that get_all_neighbours returns empty list."""
        patch = create_mock_patch()
        neighbours = PatchNoNeighbours(patch)

        result = neighbours.get_all_neighbours()

        assert result == set()

    def test_get_neighbour_lower_lod_returns_patch_lod(self):
        """Test that lower LOD returns the patch's LOD."""
        patch = create_mock_patch(lod=7)
        neighbours = PatchNoNeighbours(patch)

        lower_lod = neighbours.get_neighbour_lower_lod(PatchNoNeighbours.NORTH)

        assert lower_lod == 7

    def test_operations_dont_raise_errors(self):
        """Test that all operations can be called without errors."""
        patch = create_mock_patch()
        neighbours = PatchNoNeighbours(patch)

        # These should all work without raising errors
        neighbours.set_neighbours(PatchNoNeighbours.NORTH, [])
        neighbours.add_neighbour(PatchNoNeighbours.NORTH, create_mock_patch())
        neighbours.set_all_neighbours([], [], [], [])
        neighbours.clear_all_neighbours()
        neighbours.remove_detached_neighbours()
        neighbours.split_neighbours([])
        neighbours.merge_neighbours([])
        neighbours.calc_outer_tessellation_level([])

        # If we reach here, all operations completed without errors
        assert True
