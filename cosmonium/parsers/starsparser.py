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


from ..objects.star import Star
from ..procedural.stars import ProceduralStarSurfaceFactory, proceduralStarSurfaceFactoryDB
from .cloudsparser import CloudsYamlParser
from .noiseparser import NoiseYamlParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .schemas.stellarobjects import StarConfig, StarSurfaceFactoryConfig
from .surfacesparser import SurfaceYamlParser
from .utilsparser import check_parent, get_radius_scale
from .yamlparser import YamlModuleParser


class StarYamlParser(YamlModuleParser):
    def __init__(self, body_class):
        self.body_class = body_class

    def decode(self, data, parent):
        name = data.name
        parent_name = data.parent
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None:
            return None
        body_class = data.body_class or self.body_class
        radius, ellipticity, scale = get_radius_scale(data, None)
        orbit = OrbitYamlParser.decode(data.orbit, None, parent)
        rotation = RotationYamlParser.decode(data.rotation, None, parent)
        surfaces = data.surfaces
        if surfaces is None:
            factory_name = data.surface_factory if data.surface_factory else 'default'
            factory = proceduralStarSurfaceFactoryDB.get(factory_name)
        else:
            factory = None
        clouds = CloudsYamlParser.decode(data.clouds)
        # rings = RingsYamlParser.decode(data.rings)
        star = Star(
            name,
            body_class=body_class,
            radius=radius,
            oblateness=ellipticity,
            scale=scale,
            surface_factory=factory,
            orbit=orbit,
            rotation=rotation,
            clouds=clouds,
            abs_magnitude=data.magnitude,
            temperature=data.temperature,
            spectral_type=data.spectral_type,
        )
        self.translate_object_names(star, star.anchor.get_names())
        surfaces = data.surfaces
        if surfaces is not None:
            surfaces = SurfaceYamlParser.decode(data.surfaces, star)
            factory = None
        else:
            surfaces = []
        for surface in surfaces:
            star.add_surface(surface)
        parent.add_child_fast(star)
        return star


class StarSurfaceFactoryYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        name = data.name
        noise_parser = NoiseYamlParser()
        func = data.func
        if func is None:
            func = data.noise
            print("Warning: 'noise' entry is deprecated, use 'func' instead'")
        func = noise_parser.decode(func)
        size = int(data.size)
        factory = ProceduralStarSurfaceFactory(func, size)
        proceduralStarSurfaceFactoryDB.add(name, factory)
        return None


def register_star_parsers():
    ObjectYamlParser.register_object_parser('star', StarYamlParser('star'), model=StarConfig)
    ObjectYamlParser.register_object_parser(
        'star-surface', StarSurfaceFactoryYamlParser(), model=StarSurfaceFactoryConfig
    )
