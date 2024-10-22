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


from .appearancesparser import register_appearance_parsers
from .asterismsparser import register_asterism_parsers
from .bodiesparser import register_body_parsers
from .cameraparser import register_camera_parsers
from .constellationsparser import register_constellation_parsers
from .fogscatterparser import register_fog_parsers
from .galaxiesparser import register_galaxy_parsers
from .heightmapsparser import register_heightmap_parsers
from .nebulasparser import register_nebula_parsers
from .objectparser import register_object_parsers
from .oneilscatteringparser import register_oneil_parsers
from .orbitsparser import register_orbit_parsers
from .pluginparser import register_plugin_parsers
from .raymarchingparser import register_raymarching_parsers
from .rotationsparser import register_rotation_parsers
from .shipsparser import register_ship_parsers
from .starsparser import register_star_parsers
from .systemsparser import register_system_parsers
from .texturesourceparser import register_texture_source_parsers


def register_parsers():
    register_appearance_parsers()
    register_asterism_parsers()
    register_body_parsers()
    register_camera_parsers()
    register_constellation_parsers()
    register_fog_parsers()
    register_galaxy_parsers()
    register_heightmap_parsers()
    register_nebula_parsers()
    register_object_parsers()
    register_oneil_parsers()
    register_orbit_parsers()
    register_plugin_parsers()
    register_raymarching_parsers()
    register_rotation_parsers()
    register_ship_parsers()
    register_star_parsers()
    register_system_parsers()
    register_texture_source_parsers()
