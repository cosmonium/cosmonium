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


from panda3d.core import LQuaterniond, LVector3d

from ..astro import units
from ..patchedshapes.patchedshapes import (
    NormalizedSquarePatchFactory,
    NormalizedSquareShape,
    PatchedSpherePatchFactory,
    PatchedSphereShape,
    SquaredDistanceSquarePatchFactory,
    SquaredDistanceSquareShape,
)
from ..patchedshapes.tiles import TiledShape
from ..shapes.billboard import BillboardShape
from ..shapes.mesh import MeshShape
from ..shapes.spheres import IcoSphereShape, SphereShape
from ..spaceengine.shapes import SpaceEnginePatchedSquareShape, SpaceEngineTextureSquarePatchFactory
from .schemas.shape import (
    BillboardShapeConfig,
    IcoSphereShapeConfig,
    MeshShapeConfig,
    PatchedShapeConfig,
    SphereShapeConfig,
    TiledPlaneShapeConfig,
)
from .utilsparser import DistanceUnitsYamlParser
from .yamlparser import TypedYamlParser, YamlModuleParser


class PatchedSphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, use_skirt=True, **kwargs):
        factory = PatchedSpherePatchFactory(use_skirt)
        shape = PatchedSphereShape(factory)
        return (shape, {})


class SphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, **kwargs):
        shape = SphereShape()
        return (shape, {})


class IcoSphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, **kwargs):
        shape = IcoSphereShape(data.subdivisions)
        return (shape, {})


class SqrtSphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, use_skirt=True, **kwargs):
        factory = NormalizedSquarePatchFactory(use_skirt)
        shape = NormalizedSquareShape(factory)
        return (shape, {})


class CubeSphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, use_skirt=True, **kwargs):
        factory = SquaredDistanceSquarePatchFactory(use_skirt)
        shape = SquaredDistanceSquareShape(factory)
        return (shape, {})


class SeSphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, use_skirt=True, **kwargs):
        factory = SpaceEngineTextureSquarePatchFactory(use_skirt)
        shape = SpaceEnginePatchedSquareShape(factory)
        return (shape, {})


class MeshYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, radius=None, **kwargs):
        auto_scale_mesh = data.auto_scale
        offset = data.offset if data.offset is not None else LVector3d()
        rotation_data = data.rotation
        scale = data.scale
        scale_units = DistanceUnitsYamlParser.decode(data.scale_units, units.m)
        if scale is not None:
            if isinstance(scale, list):
                scale = LVector3d(*scale)
            else:
                scale = LVector3d(scale)
            scale *= scale_units
        else:
            if auto_scale_mesh and radius is not None:
                scale = LVector3d(radius)
            else:
                scale = LVector3d(scale_units)
        if rotation_data is not None:
            if len(rotation_data) == 3:
                rotation = LQuaterniond()
                rotation.set_hpr(LVector3d(*rotation_data))
            else:
                rotation = LQuaterniond(*rotation_data)
        else:
            rotation = LQuaterniond()
        shape = MeshShape(
            data.model,
            offset,
            rotation,
            scale,
            auto_scale_mesh,
            data.auto_center,
            data.flatten,
            data.panda,
            data.attribution,
            context=YamlModuleParser.context,
        )
        return (shape, {'create-uv': data.create_uv})


class BillboardYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, radius=None):
        shape = BillboardShape()
        return (shape, {})


class TiledPlaneYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, radius=None):
        shape = TiledShape(None, data.tile_size, None)
        return (shape, {})


class ShapeYamlParser(TypedYamlParser):
    default_type = 'patched-sphere'


def register_shape_parsers():
    """Register shape parsers with their corresponding Pydantic models."""
    ShapeYamlParser.register_parser('patched-sphere', PatchedSphereYamlParser, PatchedShapeConfig)
    ShapeYamlParser.register_parser('sqrt-sphere', SqrtSphereYamlParser, PatchedShapeConfig)
    ShapeYamlParser.register_parser('cube-sphere', CubeSphereYamlParser, PatchedShapeConfig)
    ShapeYamlParser.register_parser('se-sphere', SeSphereYamlParser, PatchedShapeConfig)
    ShapeYamlParser.register_parser('sphere', SphereYamlParser, SphereShapeConfig)
    ShapeYamlParser.register_parser('icosphere', IcoSphereYamlParser, IcoSphereShapeConfig)
    ShapeYamlParser.register_parser('mesh', MeshYamlParser, MeshShapeConfig)
    ShapeYamlParser.register_parser('raymarching', BillboardYamlParser, BillboardShapeConfig)
    ShapeYamlParser.register_parser('billboard', BillboardYamlParser, BillboardShapeConfig)
    ShapeYamlParser.register_parser('tiled-plane', TiledPlaneYamlParser, TiledPlaneShapeConfig)
