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


from panda3d.core import LQuaternion, LVector3d

from ..patchedshapes.boundingbox import PatchBoundingBox
from ..patchedshapes.patchedshapes import PatchFactory, PatchLayer, SquarePatchBase, NormalizedSquareShape
from ..geometry import geometry
from .. import settings


class SpaceEngineTextureSquarePatch(SquarePatchBase):
    xy_params = [
        {'x_inverted': True, 'y_inverted': False, 'xy_swap': True},  # Right  # Africa
        {'x_inverted': False, 'y_inverted': True, 'xy_swap': True},  # Left   # Pacific
        {'x_inverted': False, 'y_inverted': False, 'xy_swap': False},  # Back   # America
        {'x_inverted': True, 'y_inverted': True, 'xy_swap': False},  # Face   # Asia
        {'x_inverted': False, 'y_inverted': False, 'xy_swap': False},  # Top    # Arctic
        {'x_inverted': False, 'y_inverted': False, 'xy_swap': False},  # Bottom # Antartic
    ]

    def face_offset_vector(self, axes):
        (x0, y0, x1, y1) = self.calc_xy()
        return geometry.NormalizedSquarePatchOffsetVector(axes, x0, y0, x1, y1)

    def create_bounding_volume(self, axes, min_height, max_height):
        (x0, y0, x1, y1) = self.calc_xy()
        points = geometry.NormalizedSquarePatchBoundingPoints(
            axes, min_height, max_height, x0, y0, x1, y1, offset=self.offset
        )
        bounding_volume = PatchBoundingBox(points)
        return bounding_volume

    def create_centre(self, axes):
        (x0, y0, x1, y1) = self.calc_xy()
        return geometry.NormalizedSquarePatchPoint(axes, 0.5, 0.5, x0, y0, x1, y1)

    def calc_xy(self):
        div = 1 << self.lod
        x = self.x
        y = self.y
        if self.xy_params[self.face]['xy_swap']:
            x, y = y, x
        if self.xy_params[self.face]['x_inverted']:
            x = div - x - 1
        if self.xy_params[self.face]['y_inverted']:
            y = div - y - 1
        x0 = float(x) / div
        y0 = float(y) / div
        x1 = float(x + 1) / div
        y1 = float(y + 1) / div
        return (x0, y0, x1, y1)


class SpaceEngineTextureSquareLayer(PatchLayer):

    def create_instance(self, patch, tasks_tree):
        (x0, y0, x1, y1) = patch.calc_xy()
        orientation = patch.rotations[patch.face]
        rotated_axes = orientation.conjugate().xform(patch.owner.axes)
        rotated_axes = LVector3d(abs(rotated_axes[0]), abs(rotated_axes[1]), abs(rotated_axes[2]))
        self.instance = geometry.NormalizedSquarePatch(
            rotated_axes / patch.owner.radius,
            geometry.TessellationInfo(patch.density, patch.tessellation_outer_level),
            x0,
            y0,
            x1,
            y1,
            has_offset=patch.offset is not None,
            offset=patch.offset if patch.offset is not None else 0.0,
            inv_u=patch.xy_params[patch.face]['x_inverted'],
            inv_v=patch.xy_params[patch.face]['y_inverted'],
            swap_uv=patch.xy_params[patch.face]['xy_swap'],
            use_patch_adaptation=settings.use_patch_adaptation,
            use_patch_skirts=settings.use_patch_skirts,
        )
        self.instance.reparent_to(patch.instance)
        self.instance.set_quat(LQuaternion(*orientation))

    def update_instance(self, patch):
        if self.instance is not None and patch.shown:
            self.remove_instance()
            self.create_instance(patch, None)


class SpaceEngineTextureSquarePatchFactory(PatchFactory):

    def create_patch(self, parent, lod, face, x, y):
        density = self.lod_control.get_density_for(lod)
        (min_height, max_height, mean_height) = self.get_patch_limits(parent)
        patch = SpaceEngineTextureSquarePatch(
            face,
            x,
            y,
            parent,
            lod,
            density,
            self.surface.height_scale,
            min_height,
            max_height,
            mean_height,
            self.owner.axes,
        )
        patch.add_layer(SpaceEngineTextureSquareLayer())
        # TODO: Temporary or make right
        patch.owner = self.owner
        return patch


class SpaceEnginePatchedSquareShape(NormalizedSquareShape):

    def __init__(self, *args, **kwargs):
        NormalizedSquareShape.__init__(self, *args, **kwargs)
        self.face_unique = True
