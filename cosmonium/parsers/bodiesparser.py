from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LColor, LVector3

from ..patchedshapes import VertexSizePatchLodControl, TextureOrVertexSizePatchLodControl
from ..bodies import ReflectiveBody
from ..surfaces import FlatSurface, surfaceCategoryDB, SurfaceCategory
from ..shaders import BasicShader
from ..catalogs import objectsDB
from .. import settings

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .appearancesparser import AppearanceYamlParser
from .shadersparser import LightingModelYamlParser
from .shapesparser import ShapeYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .atmospheresparser import AtmosphereYamlParser
from .elementsparser import CloudsYamlParser, RingsYamlParser
from .surfacesparser import SurfaceYamlParser

class ReflectiveYamlParser(YamlModuleParser):
    def __init__(self, body_class):
        self.body_class = body_class

    def decode(self, data):
        name = data.get('name')
        parent_name = data.get('parent')
        body_class = data.get('body-class', self.body_class)
        radius = data.get('radius', None)
        if radius is None:
            diameter = data.get('diameter', None)
            if diameter is not None:
                radius = diameter / 2.0
                #Needed by surface parser
                data['radius'] = radius
        ellipticity = data.get('ellipticity', None)
        scale = data.get('axes', None)
        if scale is not None:
            if radius is None:
                radius = max(scale) / 2.0
                #Needed by surface parser
                data['radius'] = radius
            scale = LVector3(*scale) / 2.0
        radius = float(radius)
        albedo = data.get('albedo', 0.5)
        atmosphere = AtmosphereYamlParser.decode(data.get('atmosphere'))
        if data.get('surfaces') is None:
            shape, extra = ShapeYamlParser.decode(data.get('shape'))
            appearance = AppearanceYamlParser.decode(data.get('appearance'), shape)
            lighting_model = LightingModelYamlParser.decode(data.get('lighting-model'), appearance)
            if shape.patchable:
                if appearance.texture is None or appearance.texture.source.procedural:
                    shape.set_lod_control(VertexSizePatchLodControl(settings.max_vertex_size_patch))
                else:
                    shape.set_lod_control(TextureOrVertexSizePatchLodControl(settings.max_vertex_size_patch))
            shader = BasicShader(lighting_model=lighting_model,
                                 use_model_texcoord=not extra.get('create-uv', False))
            category = surfaceCategoryDB.get('visible')
            if category is None:
                print("Category 'visible' unknown")
                category = SurfaceCategory('visible')
                surfaceCategoryDB.add(category)
            surface = FlatSurface(name=None, category=category, resolution=None, source=None,
                                  shape=shape, appearance=appearance, shader=shader)
            surfaces = []
            atmosphere.add_shape_object(surface)
        else:
            surfaces = SurfaceYamlParser.decode(data.get('surfaces'), atmosphere, data)
            surface = surfaces.pop(0)
        clouds = CloudsYamlParser.decode(data.get('clouds'), atmosphere)
        rings = RingsYamlParser.decode(data.get('rings'))
        point_color = data.get('point-color', [1, 1, 1])
        point_color = LColor(point_color[0], point_color[1], point_color[2], 1.0)
        orbit = OrbitYamlParser.decode(data.get('orbit'))
        rotation = RotationYamlParser.decode(data.get('rotation'))
        body = ReflectiveBody(names=name,
                              body_class=body_class,
                              radius=radius,
                              oblateness=ellipticity,
                              scale=scale,
                              surface=surface,
                              orbit=orbit,
                              rotation=rotation,
                              ring=rings,
                              atmosphere=atmosphere,
                              clouds=clouds,
                              point_color=point_color)
        for surface in surfaces:
            body.add_surface(surface)
        if parent_name is not None:
            parent = objectsDB.get(parent_name)
            if parent is not None:
                parent.add_child_fast(body)
            else:
                print("ERROR: Parent '%s' of '%s' not found" % (parent_name, name))
            return None
        else:
            return body

ObjectYamlParser.register_object_parser('reflective', ReflectiveYamlParser(None))
ObjectYamlParser.register_object_parser('planet', ReflectiveYamlParser('planet'))
ObjectYamlParser.register_object_parser('dwarfplanet', ReflectiveYamlParser('dwarfplanet'))
ObjectYamlParser.register_object_parser('moon', ReflectiveYamlParser('moon'))
ObjectYamlParser.register_object_parser('asteroid', ReflectiveYamlParser('asteroid'))
ObjectYamlParser.register_object_parser('comet', ReflectiveYamlParser('comet'))
ObjectYamlParser.register_object_parser('spacecraft', ReflectiveYamlParser('spacecraft'))
