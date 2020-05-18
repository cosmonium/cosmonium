#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from __future__ import print_function

from ..patchedshapes import SquarePatchBase, NormalizedSquareShape
from .. import geometry

class SpaceEngineTextureSquarePatch(SquarePatchBase):
    xy_params = [
                 {'x_inverted':True,  'y_inverted':False, 'xy_swap':True},  # Right  # Africa
                 {'x_inverted':False, 'y_inverted':True,  'xy_swap':True},  # Left   # Pacific
                 {'x_inverted':False, 'y_inverted':False, 'xy_swap':False}, # Back   # America
                 {'x_inverted':True,  'y_inverted':True,  'xy_swap':False}, # Face   # Asia
                 {'x_inverted':True,  'y_inverted':True,  'xy_swap':False}, # Top    # Arctic
                 {'x_inverted':True,  'y_inverted':True,  'xy_swap':False}  # Bottom # Antartic
             ]

    def __init__(self, *args, **kwargs):
        SquarePatchBase.__init__(self, *args, **kwargs)
        self.inv_u = self.xy_params[self.face]['x_inverted']
        self.inv_v = self.xy_params[self.face]['y_inverted']
        self.swap_uv = self.xy_params[self.face]['xy_swap']

    def face_normal(self, x, y):
        (x, y) = self.calc_xy(x, y)
        return geometry.NormalizedSquarePatchNormal(float(x) / self.div,
                                                  float(y) / self.div,
                                                  float(x + 1) / self.div,
                                                  float(y + 1) / self.div)

    def create_bounding_volume(self, x, y, min_radius, max_radius):
        (x, y) = self.calc_xy(x, y)
        return geometry.NormalizedSquarePatchAABB(min_radius, max_radius,
                                                  float(x) / self.div,
                                                  float(y) / self.div,
                                                  float(x + 1) / self.div,
                                                  float(y + 1) / self.div,
                                                  offset=self.offset)

    def create_centre(self, x, y, radius):
        (x, y) = self.calc_xy(x, y)
        return geometry.NormalizedSquarePatchPoint(radius,
                                                  0.5, 0.5,
                                                  float(x) / self.div,
                                                  float(y) / self.div,
                                                  float(x + 1) / self.div,
                                                  float(y + 1) / self.div)

    def create_patch_instance(self, x, y):
        (x, y) = self.calc_xy(x, y)
        return geometry.NormalizedSquarePatch(1.0,
                                              self.density,
                                              self.tessellation_outer_level,
                                              float(x) / self.div,
                                              float(y) / self.div,
                                              float(x + 1) / self.div,
                                              float(y + 1) / self.div,
                                              offset=self.offset)

    def calc_xy(self, x, y):
        if self.xy_params[self.face]['xy_swap']:
            x, y = y, x
        if self.xy_params[self.face]['x_inverted']:
            x = self.div - x - 1
        if self.xy_params[self.face]['y_inverted']:
            y = self.div - y - 1
        return x, y

class SpaceEnginePatchedSquareShape(NormalizedSquareShape):
    def __init__(self, *args, **kwargs):
        NormalizedSquareShape.__init__(self, *args, **kwargs)
        self.face_unique = True

    def create_patch(self, parent, lod, face, x, y):
        density = self.lod_control.get_density_for(lod)
        (min_radius, max_radius, mean_radius) = self.get_patch_limits(parent)
        patch = SpaceEngineTextureSquarePatch(face, x, y, parent, lod, density, self.parent, min_radius, max_radius, mean_radius, self.use_shader, self.use_tessellation)
        #TODO: Temporary or make right
        patch.owner = self
        return patch
