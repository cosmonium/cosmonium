#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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


from ..objects.star import Star
from ..procedural.stars import proceduralStarSurfaceFactoryDB
from ..procedural.stars import ProceduralStarSurfaceFactory

from .elementsparser import CloudsYamlParser
from .noiseparser import NoiseYamlParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .surfacesparser import SurfaceYamlParser
from .utilsparser import check_parent, get_radius_scale
from .yamlparser import YamlModuleParser


class StarYamlParser(YamlModuleParser):
    def decode(self, data, parent):
        name = data.get('name')
        (translated_names, source_names) = self.translate_names(name)
        parent_name = data.get('parent')
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None:
            return None
        body_class = data.get('body-class', 'star')
        radius, ellipticity, scale = get_radius_scale(data, None)
        temperature = data.get('temperature')
        abs_magnitude = data.get('magnitude')
        spectral_type = data.get('spectral-type')
        orbit = OrbitYamlParser.decode(data.get('orbit'), None, parent)
        rotation = RotationYamlParser.decode(data.get('rotation'), None, parent)
        surfaces = data.get('surfaces')
        if surfaces is None:
            factory_name = data.get('surface-factory', 'default')
            factory = proceduralStarSurfaceFactoryDB.get(factory_name)
        else:
            factory = None
        clouds = CloudsYamlParser.decode(data.get('clouds'))
        # rings = RingsYamlParser.decode(data.get('rings'))
        star = Star(
            translated_names,
            source_names=source_names,
            body_class=body_class,
            radius=radius,
            oblateness=ellipticity,
            scale=scale,
            surface_factory=factory,
            orbit=orbit,
            rotation=rotation,
            clouds=clouds,
            abs_magnitude=abs_magnitude,
            temperature=temperature,
            spectral_type=spectral_type,
        )
        surfaces = data.get('surfaces')
        if surfaces is not None:
            surfaces = SurfaceYamlParser.decode(data.get('surfaces'), star)
            factory = None
        else:
            surfaces = []
        for surface in surfaces:
            star.add_surface(surface)
        parent.add_child_fast(star)
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


def register_star_parsers():
    ObjectYamlParser.register_object_parser('star', StarYamlParser())
    ObjectYamlParser.register_object_parser('star-surface', StarSurfaceFactoryYamlParser())
