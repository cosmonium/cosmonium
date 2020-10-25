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
from ..parameters import ParametersGroup, SettingParameter, ParametricFunctionParameter
from .. import settings

from .editor import ParamEditor

class Preferences(ParamEditor):
    def __init__(self, cosmonium, font_family, font_size = 14, owner=None):
        ParamEditor.__init__(self, font_family, font_size, owner)
        self.cosmonium = cosmonium

    def show(self):
        if self.shown():
            print("Editor already shown")
            return
        self.create_layout(self.make_entries())
        if self.last_pos is None:
            self.last_pos = (0, 0, -100)
        self.window.setPos(self.last_pos)
        self.window.update()

    def update_parameter(self, param):
        ParamEditor.update_parameter(self, param)
        self.cosmonium.update_settings()

    def make_entries(self):
        return ParametersGroup('Preferences',
                               [ParametersGroup('General', self.make_general()),
                                ParametersGroup('Orbits', self.make_orbits()),
                                ParametersGroup('Labels', self.make_labels()),
                                ParametersGroup('Render', self.make_render()),
                                ])


    def make_general(self):
        return [
                SettingParameter('Invert mouse wheel', 'invert_wheel', SettingParameter.TYPE_BOOL)
               ]

    def make_orbits(self):
        orbits = [
                ('Stars', 'star'),
                ('Planets', 'planet'),
                ('Dwarf planets','dwarfplanet'),
                ('Moons', 'moon'),
                ('Minor moons', 'minormoon'),
                ('Lost moons', 'lostmoon'),
                ('Comets', 'comet'),
                ('Asteroids', 'asteroid'),
                ('Interstellars', 'interstellar'),
                ('Spacecrafts', 'spacecraft'),
               ]
        params = [ SettingParameter('All orbits', 'show_orbits', SettingParameter.TYPE_BOOL) ]
        params += [ParametricFunctionParameter(label, param_name, bodyClasses.set_show_orbit, bodyClasses.get_show_orbit, SettingParameter.TYPE_BOOL)
                for (label, param_name) in orbits]
        return params

    def make_labels(self):
        labels = [
                  ('Galaxies', 'galaxy'),
                  #('Globular', 'globular'),
                  ('Stars', 'star'),
                  ('Planets', 'planet'),
                  ('Dwarf planets', 'dwarfplanet'),
                  ('Moons', 'moon'),
                  ('Minor moons', 'minormoon'),
                  ('Lost moons', 'lostmoon'),
                  ('Comets', 'comet'),
                  ('Asteroids', 'asteroid'),
                  ('Interstellars', 'interstellar'),
                  ('Spacecrafts', 'spacecraft'),
                  ('Constellations', 'constellation'),
                  #('Locations', 'location'),
                ]
        return [ParametricFunctionParameter(label, param_name, bodyClasses.set_show_label, bodyClasses.get_show_label, SettingParameter.TYPE_BOOL)
                for (label, param_name) in labels]

    def make_render(self):
        return [
                ParametersGroup('Objects',
                                [ParametricFunctionParameter('Galaxies', 'galaxy',bodyClasses.set_show, bodyClasses.get_show, SettingParameter.TYPE_BOOL),
                                ]),
                #('shift-u', self.cosmonium.toggle_globulars)
                #('^', self.cosmonium.toggle_nebulae)
                ParametersGroup('Components',
                                [SettingParameter('Atmospheres', 'show_atmospheres', SettingParameter.TYPE_BOOL),
                                 SettingParameter('Clouds', 'show_clouds', SettingParameter.TYPE_BOOL),
                                 ]),
                #('control-e', self.toggle_shadows)
                #('control-l', self.cosmonium.toggle_nightsides)
                #('control-t', self.cosmonium.toggle_comet_tails)
                ParametersGroup('Constellations',
                                [SettingParameter('Boundaries', 'show_boundaries', SettingParameter.TYPE_BOOL),
                                 SettingParameter('Asterisms', 'show_asterisms', SettingParameter.TYPE_BOOL),
                                 ]),
                ParametersGroup('Grids',
                                [SettingParameter('Equatorial', 'show_equatorial_grid', SettingParameter.TYPE_BOOL),
                                 SettingParameter('Ecliptic', 'show_ecliptic_grid', SettingParameter.TYPE_BOOL),
                                 ]),
                ParametersGroup('Annotations',
                                [SettingParameter('Rotation axis', 'show_rotation_axis', SettingParameter.TYPE_BOOL),
                                 SettingParameter('Reference frame', 'show_reference_axis', SettingParameter.TYPE_BOOL),
                                 ]),
                ]
