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


from .stellarbody import StellarBody

from ..engine.anchors import StellarAnchor
from ..astro.astro import abs_mag_to_lum

class EmissiveBody(StellarBody):
    anchor_class = StellarAnchor.Emissive
    has_halo = True
    has_resolved_halo = True
    def __init__(self, *args, **kwargs):
        abs_magnitude = kwargs.pop('abs_magnitude', None)
        StellarBody.__init__(self, *args, **kwargs)
        #TODO: This should be done in create_anchor
        self.anchor._abs_magnitude = abs_magnitude

    def is_emissive(self):
        return True

    def get_luminosity(self):
        return abs_mag_to_lum(self.get_abs_magnitude())
    
    def get_phase(self):
        return 1
