#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from .emissive import EmissiveBody

from ..astro.astro import temp_to_radius
from ..astro.spectraltype import SpectralType, spectralTypeStringDecoder
from ..astro.blackbody import temp_to_RGB
from ..astro import units


class Star(EmissiveBody):
    def __init__(self, names, source_names, radius=None, oblateness=None, scale=None,
                 surface=None, surface_factory=None,
                 orbit=None, rotation=None,
                 abs_magnitude=None, temperature=None, spectral_type=None,
                 atmosphere=None, clouds=None,
                 body_class='star',  point_color=None,
                 description=''):
        if spectral_type is None:
            self.spectral_type = SpectralType()
        elif isinstance(spectral_type, SpectralType):
            self.spectral_type = spectral_type
        else:
            self.spectral_type = spectralTypeStringDecoder.decode(spectral_type)
        if temperature is None:
            if spectral_type is None:
                self.temperature = units.sun_temperature
            else:
                self.temperature = self.spectral_type.temperature
        else:
            self.temperature = temperature
        if point_color is None:
            point_color = temp_to_RGB(self.temperature)
        if radius is None:
            if self.spectral_type.white_dwarf:
                #TODO: Find radius-luminosity relationship or use mass
                radius = 7000.0
            else:
                radius = temp_to_radius(self.temperature, abs_magnitude)
        EmissiveBody.__init__(self, names=names, source_names=source_names,
                              radius=radius, oblateness=oblateness, scale=scale,
                              surface=surface, surface_factory=surface_factory,
                              orbit=orbit, rotation=rotation,
                              abs_magnitude=abs_magnitude,
                              atmosphere=atmosphere, clouds=clouds,
                              body_class=body_class, point_color=point_color,
                              description=description)

