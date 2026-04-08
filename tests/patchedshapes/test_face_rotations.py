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

"""Tests for cube face rotation convention and xyz_to_face_xy inverse mappings."""

import pytest
from panda3d.core import LVector3d

from cosmonium.patchedshapes.patchedshapes import SquarePatchBase


class TestFaceRotationConvention:
    """Verify face rotations produce correct normals and UV orientations."""

    # Expected face properties: (normal, u direction, v direction)
    EXPECTED = {
        SquarePatchBase.RIGHT: ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        SquarePatchBase.LEFT: ((-1, 0, 0), (0, -1, 0), (0, 0, 1)),
        SquarePatchBase.BACK: ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
        SquarePatchBase.FRONT: ((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
        SquarePatchBase.TOP: ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
        SquarePatchBase.BOTTOM: ((0, 0, -1), (1, 0, 0), (0, -1, 0)),
    }

    @pytest.fixture
    def rotations(self):
        return SquarePatchBase.rotations

    def _round_vec(self, v):
        return tuple(round(v[i]) for i in range(3))

    @pytest.mark.parametrize("face", range(6))
    def test_face_normal(self, rotations, face):
        """Each face normal should point in the expected axis direction."""
        expected_normal = self.EXPECTED[face][0]
        actual = self._round_vec(rotations[face].xform(LVector3d(0, 0, 1)))
        assert actual == expected_normal

    @pytest.mark.parametrize("face", range(6))
    def test_face_u_direction(self, rotations, face):
        """Each face u direction should match the documented convention."""
        expected_u = self.EXPECTED[face][1]
        actual = self._round_vec(rotations[face].xform(LVector3d(1, 0, 0)))
        assert actual == expected_u

    @pytest.mark.parametrize("face", range(6))
    def test_face_v_direction(self, rotations, face):
        """Each face v direction should match the documented convention."""
        expected_v = self.EXPECTED[face][2]
        actual = self._round_vec(rotations[face].xform(LVector3d(0, 1, 0)))
        assert actual == expected_v

    @pytest.mark.parametrize("face", range(6))
    def test_rotation_is_proper(self, rotations, face):
        """Each rotation should be a proper rotation (determinant +1, unit quaternion)."""
        q = rotations[face]
        # Unit quaternion check
        length = q.get_r() ** 2 + q.get_i() ** 2 + q.get_j() ** 2 + q.get_k() ** 2
        assert abs(length - 1.0) < 1e-10

    def test_side_faces_v_points_up(self, rotations):
        """All side face v directions should point upward (+Z)."""
        side_faces = [SquarePatchBase.RIGHT, SquarePatchBase.LEFT, SquarePatchBase.BACK, SquarePatchBase.FRONT]
        for face in side_faces:
            v_dir = self._round_vec(rotations[face].xform(LVector3d(0, 1, 0)))
            assert v_dir == (0, 0, 1), f"Face {SquarePatchBase.face_to_string(face)} v should be +Z"


class TestEdgeAdjacency:
    """Verify that adjacent faces share edge vertices correctly."""

    @pytest.fixture
    def face_corners(self):
        """Compute all face corner positions in world space."""
        corners_local = {
            'u0v0': LVector3d(-1, -1, 1),
            'u1v0': LVector3d(1, -1, 1),
            'u0v1': LVector3d(-1, 1, 1),
            'u1v1': LVector3d(1, 1, 1),
        }
        result = {}
        for face in range(6):
            q = SquarePatchBase.rotations[face]
            corners = {}
            for name, vec in corners_local.items():
                normalized = LVector3d(vec)
                normalized.normalize()
                world = q.xform(normalized)
                corners[name] = tuple(round(world[i], 6) for i in range(3))
            result[face] = corners
        return result

    def test_all_12_edges_found(self, face_corners):
        """Every edge of the cube should be shared by exactly two faces."""
        edges_local = [
            ('u0v0', 'u0v1'),  # left edge
            ('u1v0', 'u1v1'),  # right edge
            ('u0v0', 'u1v0'),  # bottom edge
            ('u0v1', 'u1v1'),  # top edge
        ]
        shared_count = 0
        for i in range(6):
            for j in range(i + 1, 6):
                for ei_name in edges_local:
                    ei_s = face_corners[i][ei_name[0]]
                    ei_e = face_corners[i][ei_name[1]]
                    for ej_name in edges_local:
                        ej_s = face_corners[j][ej_name[0]]
                        ej_e = face_corners[j][ej_name[1]]
                        if (ei_s == ej_s and ei_e == ej_e) or (ei_s == ej_e and ei_e == ej_s):
                            shared_count += 1
        assert shared_count == 12
