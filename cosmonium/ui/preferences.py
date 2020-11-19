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
from ..parameters import ParametersGroup, UserParameter, SettingParameter, ParametricFunctionParameter

from .editor import ParamEditor
from cosmonium import settings

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
                                ParametersGroup('Advanced', self.make_advanced()),
                                ParametersGroup('Debug', self.make_debug()),
                                ])


    def make_general(self):
        return [ParametersGroup('UI',
                                []),
                ParametersGroup('Mouse',
                                [SettingParameter('Invert mouse wheel', 'invert_wheel', SettingParameter.TYPE_BOOL),
                                 ]),
                ParametersGroup('Keyboard',
                                [SettingParameter('Damped navigation keys', 'damped_nav', SettingParameter.TYPE_BOOL),
                                 SettingParameter('Invert Up/Down', 'celestia_nav', SettingParameter.TYPE_BOOL),
                                 ])
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
        return [ParametersGroup('Labels',
                                [ParametricFunctionParameter(label, param_name, bodyClasses.set_show_label, bodyClasses.get_show_label, SettingParameter.TYPE_BOOL)
                                 for (label, param_name) in labels]),
                ParametersGroup('Fonts',
                                [SettingParameter("Label size", 'label_size', UserParameter.TYPE_INT, [4, 32]),
                                 SettingParameter("Constellation label size", 'constellations_label_size', UserParameter.TYPE_INT, [4, 32]),
                                 ]),
                ]

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

    def get_ui_scale(self):
        return settings.ui_scale[0]

    def set_ui_scale(self, scale):
        settings.ui_scale = (scale, scale)

    def make_advanced(self):
        return [ParametersGroup('UI',
                                [UserParameter("UI Scale", self.set_ui_scale, self.get_ui_scale, UserParameter.TYPE_FLOAT, [0.5, 2]),
                                 SettingParameter("Menu text size", 'menu_text_size', UserParameter.TYPE_INT, [4, 32]),
                                 SettingParameter("UI text size", 'ui_font_size', UserParameter.TYPE_INT, [4, 32]),
                                ]),
                ParametersGroup('HUD',
                                [SettingParameter("HUD text size", 'hud_text_size', UserParameter.TYPE_INT, [4, 32]),
                                 SettingParameter("HUD info size", 'hud_info_text_size', UserParameter.TYPE_INT, [4, 32]),
                                 SettingParameter("HUD color", 'hud_color', UserParameter.TYPE_VEC, [0, 1], nb_components=3),
                                ]),
                ParametersGroup('Query',
                                [SettingParameter("Query size", 'query_text_size', UserParameter.TYPE_INT, [4, 32]),
                                 SettingParameter("Suggestion size", 'query_suggestion_text_size', UserParameter.TYPE_INT, [4, 32]),
                                ]),
                ParametersGroup('Render',
                                [SettingParameter("Cull far patches", 'cull_far_patches', UserParameter.TYPE_BOOL),
                                 SettingParameter("Cull far patches threshold", 'cull_far_patches_threshold', UserParameter.TYPE_INT, [5, 25]),
                                 SettingParameter("Shadow slope bias", 'shadows_slope_scale_bias', UserParameter.TYPE_BOOL),
                                 SettingParameter("Shadow PCF", 'shadows_pcf_16', UserParameter.TYPE_BOOL),
                                 SettingParameter("Shadow slope bias", 'shadows_slope_scale_bias', UserParameter.TYPE_BOOL),
                                ]),
                ParametersGroup('OpenGL',
                                [SettingParameter("Multisampling", 'multisamples', UserParameter.TYPE_INT, [0, 16])
                                ]),
                ]
    def make_debug(self):
        return [ParametersGroup('Async',
                                [SettingParameter("Sync data loading", 'sync_data_load', UserParameter.TYPE_BOOL),
                                 SettingParameter("Sync texture loading", 'sync_texture_load', UserParameter.TYPE_BOOL),
                                ])
        ]
