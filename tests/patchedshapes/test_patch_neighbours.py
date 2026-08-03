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


def create_mock_patch(x0=0, x1=1, y0=0, y1=1, lod=0, max_level=2):
    """Create a mock patch object for testing."""
    mock = Mock(
        spec_set=[
            'x0',
            'x1',
            'y0',
            'y1',
            'lod',
            'max_level',
            'children',
            'neighbours',
            'tessellation_outer_level',
        ]
    )
    mock.x0 = x0
    mock.x1 = x1
    mock.y0 = y0
    mock.y1 = y1
    mock.lod = lod
    mock.max_level = max_level
    mock.children = []
    mock.neighbours = PatchNeighbours(mock)
    density = 1 << max_level  # 2^max_level
    mock.tessellation_outer_level = [density] * 4
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


class TestSpherePatchHemisphereJunction:
    """Tests for adaptation at UV sphere hemisphere boundaries.

    At LOD 0 there are only two patches (one per hemisphere).  When one of them
    is split the children at the shared longitude boundary must know about the
    unsplit neighbour so that calc_outer_tessellation_level computes a ratio > 1
    and the edge triangulation is adapted.
    """

    # Mapping produced by conv = [WEST, SOUTH, EAST, NORTH]
    TESS_IDX_WEST = 0
    TESS_IDX_SOUTH = 1
    TESS_IDX_EAST = 2
    TESS_IDX_NORTH = 3
    # Note: In geometry, the edges are named [left, bottom, right, top].

    def _make_sphere_root_patches(self):
        """Create two LOD-0 hemisphere patches linked as in PatchedSphereShape."""
        # p0: longitude 0.0–0.5,  p1: longitude 0.5–1.0
        p0 = create_mock_patch(x0=0.0, x1=0.5, y0=0.0, y1=1.0, lod=0, max_level=2)
        p1 = create_mock_patch(x0=0.5, x1=1.0, y0=0.0, y1=1.0, lod=0, max_level=2)
        # The two hemispheres wrap: p0.EAST↔p1.WEST and p0.WEST↔p1.EAST
        # set_all_neighbours(north, east, south, west)
        p0.neighbours.set_all_neighbours(set(), {p1}, set(), {p1})
        p1.neighbours.set_all_neighbours(set(), {p0}, set(), {p0})
        return p0, p1

    def _split_patch(self, parent):
        """Simulate splitting a patch into four children (bl, br, tr, tl)."""
        bl = create_mock_patch(
            x0=parent.x0,
            x1=(parent.x0 + parent.x1) / 2,
            y0=parent.y0,
            y1=(parent.y0 + parent.y1) / 2,
            lod=parent.lod + 1,
            max_level=parent.max_level,
        )
        br = create_mock_patch(
            x0=(parent.x0 + parent.x1) / 2,
            x1=parent.x1,
            y0=parent.y0,
            y1=(parent.y0 + parent.y1) / 2,
            lod=parent.lod + 1,
            max_level=parent.max_level,
        )
        tr = create_mock_patch(
            x0=(parent.x0 + parent.x1) / 2,
            x1=parent.x1,
            y0=(parent.y0 + parent.y1) / 2,
            y1=parent.y1,
            lod=parent.lod + 1,
            max_level=parent.max_level,
        )
        tl = create_mock_patch(
            x0=parent.x0,
            x1=(parent.x0 + parent.x1) / 2,
            y0=(parent.y0 + parent.y1) / 2,
            y1=parent.y1,
            lod=parent.lod + 1,
            max_level=parent.max_level,
        )
        for child in (bl, br, tr, tl):
            child.neighbours = PatchNeighbours(child)
        parent.children = [bl, br, tr, tl]
        return bl, br, tr, tl

    def test_root_patches_are_east_west_neighbours(self):
        """After create_root_patches the two hemispheres know about each other."""
        p0, p1 = self._make_sphere_root_patches()

        assert p1 in p0.neighbours.get_neighbours(PatchNeighbours.EAST)
        assert p1 in p0.neighbours.get_neighbours(PatchNeighbours.WEST)
        assert p0 in p1.neighbours.get_neighbours(PatchNeighbours.EAST)
        assert p0 in p1.neighbours.get_neighbours(PatchNeighbours.WEST)

    def test_east_junction_children_get_adapted_when_neighbour_is_coarser(self):
        """Children at the EAST junction of a split patch adapt to the unsplit neighbour.

        When p0 (LOD 0) is split and p1 (LOD 0) remains unsplit, the children
        tr and br on the EAST side of p0 should compute tessellation_outer_level
        for the EAST edge to a value smaller than the density (ratio > 1).
        """
        p0, p1 = self._make_sphere_root_patches()
        bl, br, tr, tl = self._split_patch(p0)
        update = []
        p0.neighbours.split_neighbours(update)

        density = 1 << tr.max_level
        half_density = 1 << (tr.max_level - 1)
        # EAST side (junction) patches should adapt to the unsplit neighbour
        assert tr.tessellation_outer_level[self.TESS_IDX_EAST] == half_density
        assert br.tessellation_outer_level[self.TESS_IDX_EAST] == half_density

        # WEST side (interior) patches should remain at full density
        assert tr.tessellation_outer_level[self.TESS_IDX_WEST] == density
        assert br.tessellation_outer_level[self.TESS_IDX_WEST] == density

    def test_west_junction_children_get_adapted_when_neighbour_is_coarser(self):
        """Children at the WEST junction of a split patch adapt to the unsplit neighbour.

        When p0 (LOD 0) is split and p1 (LOD 0) remains unsplit, the children
        tl and bl on the WEST side of p0 should compute tessellation_outer_level
        for the WEST edge to a value smaller than the density.
        """
        p0, p1 = self._make_sphere_root_patches()
        bl, br, tr, tl = self._split_patch(p0)
        update = []
        p0.neighbours.split_neighbours(update)

        density = 1 << tr.max_level
        half_density = 1 << (tr.max_level - 1)
        # WEST side (junction) patches should adapt to the unsplit neighbour
        assert tl.tessellation_outer_level[self.TESS_IDX_WEST] == half_density
        assert bl.tessellation_outer_level[self.TESS_IDX_WEST] == half_density

        # EAST side (interior) patches should remain at full density
        assert tl.tessellation_outer_level[self.TESS_IDX_EAST] == density
        assert bl.tessellation_outer_level[self.TESS_IDX_EAST] == density

    def test_p1_neighbour_list_updated_after_p0_splits(self):
        """When p0 splits, p1's own neighbour list is updated to point to p0's children."""
        p0, p1 = self._make_sphere_root_patches()
        bl, br, tr, tl = self._split_patch(p0)
        p0.neighbours.split_neighbours([])

        # p1's WEST neighbours should now be tr and br (the EAST side of p0)
        west_of_p1 = p1.neighbours.get_neighbours(PatchNeighbours.WEST)
        assert tr in west_of_p1
        assert br in west_of_p1
        assert p0 not in west_of_p1

        # p1's EAST neighbours should now be tl and bl (the WEST side of p0)
        east_of_p1 = p1.neighbours.get_neighbours(PatchNeighbours.EAST)
        assert tl in east_of_p1
        assert bl in east_of_p1
        assert p0 not in east_of_p1

    def test_no_adaptation_when_both_patches_same_lod(self):
        """When both hemispheres are at the same LOD no adaptation is needed."""
        p0, p1 = self._make_sphere_root_patches()
        density = 1 << p0.max_level  # 4
        update = []
        p0.neighbours.calc_outer_tessellation_level(update)
        p1.neighbours.calc_outer_tessellation_level(update)

        # Both at LOD 0, delta = 0, outer_level = max_level, new_level = density
        for idx in range(4):
            assert p0.tessellation_outer_level[idx] == density
            assert p1.tessellation_outer_level[idx] == density
