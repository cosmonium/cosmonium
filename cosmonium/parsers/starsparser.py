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
from __future__ import absolute_import

from panda3d.core import LVector3

from ..bodies import Star
from ..catalogs import objectsDB
from ..procedural.stars import proceduralStarSurfaceFactoryDB
from ..procedural.stars import ProceduralStarSurfaceFactory

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .noiseparser import NoiseYamlParser
from .surfacesparser import SurfaceYamlParser
from .elementsparser import CloudsYamlParser, RingsYamlParser

class StarYamlParser(YamlModuleParser):
    def decode(self, data):
        (translated_names, source_names) = self.translate_names(data.get('name'))
        parent_name = data.get('parent')
        body_class = data.get('body-class', 'star')
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
        if radius is not None:
            radius = float(radius)
        temperature = data.get('temperature')
        abs_magnitude = data.get('magnitude')
        spectral_type = data.get('spectral-type')
        orbit = OrbitYamlParser.decode(data.get('orbit'))
        rotation = RotationYamlParser.decode(data.get('rotation'))
        surfaces = data.get('surfaces')
        if surfaces is not None:
            surfaces = SurfaceYamlParser.decode(data.get('surfaces'), None, data)
            surface = surfaces.pop(0)
            factory = None
        else:
            factory_name = data.get('surface-factory', 'default')
            factory = proceduralStarSurfaceFactoryDB.get(factory_name)
            surface = None
            surfaces = []
        clouds = CloudsYamlParser.decode(data.get('clouds'), None)
        rings = RingsYamlParser.decode(data.get('rings'))
        star = Star(translated_names,
                    source_names=source_names,
                    body_class=body_class,
                    radius=radius,
                    oblateness=ellipticity,
                    scale=scale,
                    surface_factory=factory,
                    surface=surface,
                    orbit=orbit,
                    rotation=rotation,
                    ring=rings,
                    clouds=clouds,
                    abs_magnitude=abs_magnitude,
                    temperature=temperature,
                    spectral_type=spectral_type)
        for surface in surfaces:
            star.add_surface(surface)
        if parent_name is not None:
            parent = objectsDB.get(parent_name)
            if parent is not None:
                parent.add_child_star_fast(star)
            else:
                print("ERROR: Parent '%s' of '%s' not found" % (parent_name, name))
            return None
        else:
            return star
    
class StarSurfaceFactoryYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        noise_parser = NoiseYamlParser()
        func = data.get('func')
        if func is None:
            func = data.get('noise')
            print("Warning: 'noise' entry is deprecated, use 'func' instead'")
        func = noise_parser.decode(func)
        size = int(data.get('size', 256))
        factory = ProceduralStarSurfaceFactory(func, size)
        proceduralStarSurfaceFactoryDB.add(name, factory)
        return None

ObjectYamlParser.register_object_parser('star', StarYamlParser())
ObjectYamlParser.register_object_parser('star-surface', StarSurfaceFactoryYamlParser())
