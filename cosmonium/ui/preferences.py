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

from ..bodyclass import bodyClasses
from .. import settings

from .preferencespanel import PreferencesPanel

class Preferences(PreferencesPanel):
    def __init__(self, cosmonium, font_family, font_size = 14, owner=None):
        PreferencesPanel.__init__(self, font_family, font_size, owner)
        self.cosmonium = cosmonium
        self.preferences = [['General', self.make_general()],
                            ['Orbits', self.make_orbits()],
                            ['Labels', self.make_labels()],
                            ['Render', self.make_render()],
                           ]

    def toggle_attribute(self, attribute):
        setattr(settings, attribute, not getattr(settings, attribute))

    def make_general(self):
        return [
                ('Invert mouse wheel', settings.invert_wheel, self.toggle_attribute, 'invert_wheel')
               ]

    def make_orbits(self):
        return [
                ('All orbits', settings.show_orbits, self.cosmonium.toggle_orbits),
                0,
                ('Stars', bodyClasses.get_show_orbit('star'), self.cosmonium.toggle_orbit, 'star'),
                ('Planets', bodyClasses.get_show_orbit('planet'), self.cosmonium.toggle_orbit, 'planet'),
                ('Dwarf planets', bodyClasses.get_show_orbit('dwarfplanet'), self.cosmonium.toggle_orbit, 'dwarfplanet'),
                ('Moons', bodyClasses.get_show_orbit('moon'), self.cosmonium.toggle_orbit, 'moon'),
                ('Minor moons', bodyClasses.get_show_orbit('minormoon'), self.cosmonium.toggle_orbit, 'minormoon'),
                ('Comets', bodyClasses.get_show_orbit('comet'), self.cosmonium.toggle_orbit, 'comet'),
                ('Asteroids', bodyClasses.get_show_orbit('asteroid'), self.cosmonium.toggle_orbit, 'asteroid'),
                ('Interstellars', bodyClasses.get_show_orbit('interstellar'), self.cosmonium.toggle_orbit, 'interstellar'),
                ('Spacecrafts', bodyClasses.get_show_orbit('spacecraft'), self.cosmonium.toggle_orbit, 'spacecraft'),
               ]

    def make_labels(self):
        return [
                  ('Galaxies', bodyClasses.get_show_label('galaxy'), self.cosmonium.toggle_label, 'galaxy'),
                  #('Globular', self.toggle_label, 'globular'),
                  ('Stars', bodyClasses.get_show_label('star'), self.cosmonium.toggle_label, 'star'),
                  ('Planets', bodyClasses.get_show_label('planet'), self.cosmonium.toggle_label, 'planet'),
                  ('Dwarf planets', bodyClasses.get_show_label('dwarfplanet'), self.cosmonium.toggle_label, 'dwarfplanet'),
                  ('Moons', bodyClasses.get_show_label('moon'), self.cosmonium.toggle_label, 'moon'),
                  ('Minor Moons', bodyClasses.get_show_label('minormoon'), self.cosmonium.toggle_label, 'minormoon'),
                  ('Comets', bodyClasses.get_show_label('comet'), self.cosmonium.toggle_label, 'comet'),
                  ('Asteroids', bodyClasses.get_show_label('asteroid'), self.cosmonium.toggle_label, 'asteroid'),
                  ('Interstellars', bodyClasses.get_show_label('interstellar'), self.cosmonium.toggle_label, 'interstellar'),
                  ('Spacecrafts', bodyClasses.get_show_label('spacecraft'), self.cosmonium.toggle_label, 'spacecraft'),
                  ('Constellations', bodyClasses.get_show_label('constellation'), self.cosmonium.toggle_label, 'constellation'),
                  #('Locations', self.toggle_label, 'location'),
                ]

    def make_render(self):
        return [
                'Objects',
                ('Galaxies', bodyClasses.get_show('galaxy'), self.cosmonium.toggle_body_class, 'galaxy'),
                #('shift-u', self.cosmonium.toggle_globulars)
                #('^', self.cosmonium.toggle_nebulae)
                'Components',
                ('Atmospheres', settings.show_atmospheres, self.cosmonium.toggle_atmosphere),
                ('Clouds', settings.show_clouds, self.cosmonium.toggle_clouds),
                #('control-e', self.toggle_shadows)
                #('control-l', self.cosmonium.toggle_nightsides)
                #('control-t', self.cosmonium.toggle_comet_tails)
                'Constellations',
                ('Boundaries', settings.show_boundaries, self.cosmonium.toggle_boundaries),
                ('Asterisms', settings.show_asterisms, self.cosmonium.toggle_asterisms),
                'Grids',
                ('Equatorial', settings.show_equatorial_grid, self.cosmonium.toggle_grid_equatorial),
                ('Ecliptic', settings.show_ecliptic_grid, self.cosmonium.toggle_grid_ecliptic),
                'Annotations',
                ('Rotation axis', settings.show_rotation_axis, self.cosmonium.toggle_rotation_axis),
                ('Reference frame', settings.show_reference_axis, self.cosmonium.toggle_reference_axis),
                ]