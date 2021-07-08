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


from panda3d.core import LVector3d, LQuaterniond

from ..shapes import SphereShape, IcoSphereShape, MeshShape
from ..patchedshapes import PatchedSpherePatchFactory, SquaredDistanceSquarePatchFactory, NormalizedSquarePatchFactory
from ..patchedshapes import PatchedSphereShape, NormalizedSquareShape, SquaredDistanceSquareShape
from ..spaceengine.shapes import SpaceEnginePatchedSquareShape
from ..procedural.raymarching import RayMarchingShape

from .yamlparser import YamlModuleParser

class MeshYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, radius):
        if isinstance(data, str):
            data = {'model': data}
        model = data.get('model')
        create_uv = data.get('create-uv', False)
        panda = data.get('panda', False)
        auto_scale_mesh = data.get('auto-scale', True)
        offset = data.get('offset', None)
        rotation_data = data.get('rotation', None)
        if auto_scale_mesh and radius is not None:
            scale = LVector3d(radius)
        else:
            scale = data.get('scale', None)
        if offset is not None:
            offset = LVector3d(*offset)
        if rotation_data is not None:
            if len(rotation_data) == 3:
                rotation = LQuaterniond()
                rotation.set_hpr(LVector3d(*rotation_data))
            else:
                rotation = LQuaterniond(*rotation_data)
        else:
            rotation = None
        flatten = data.get('flatten', True)
        attribution = data.get('attribution', None)
        shape = MeshShape(model, offset, rotation, scale, auto_scale_mesh, flatten, panda, attribution, context=YamlModuleParser.context)
        return (shape, {'create-uv': create_uv})

class RayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        shape = RayMarchingShape()
        return (shape, {})

class ShapeYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, default='patched-sphere', radius=None):
        shape = None
        extra = {}
        (shape_type, shape_data) = self.get_type_and_data(data, default)
        if shape_type == 'patched-sphere':
            factory = PatchedSpherePatchFactory()
            shape = PatchedSphereShape(factory)
        elif shape_type == 'sphere':
            shape = SphereShape()
        elif shape_type == 'icosphere':
            subdivisions = shape_data.get('subdivisions', 3)
            shape = IcoSphereShape(subdivisions)
        elif shape_type == 'sqrt-sphere':
            factory = NormalizedSquarePatchFactory()
            shape = NormalizedSquareShape(factory)
        elif shape_type == 'cube-sphere':
            factory = SquaredDistanceSquarePatchFactory
            shape = SquaredDistanceSquareShape(factory)
        elif shape_type == 'se-sphere':
            shape = SpaceEnginePatchedSquareShape()
        elif shape_type == 'mesh':
            shape, extra = MeshYamlParser.decode(shape_data, radius)
        elif shape_type == 'raymarching':
            shape, extra = RayMarchingYamlParser.decode(shape_data)
        else:
            print("Unknown shape", shape_type)
        return shape, extra
