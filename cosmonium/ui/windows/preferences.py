#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


from ...bodyclass import bodyClasses
from ...parameters import ParametersGroup, UserParameter, SettingParameter, ParametricFunctionParameter

from .editor import ParamEditor


class Preferences(ParamEditor):
    def __init__(self, cosmonium, owner=None):
        ParamEditor.__init__(self, owner)
        self.cosmonium = cosmonium

    def update_parameter(self, param):
        ParamEditor.update_parameter(self, param)
        self.cosmonium.update_settings()

    def make_entries(self):
        return ParametersGroup(_('Preferences'),
                               [ParametersGroup(_('General'), self.make_general()),
                                ParametersGroup(_('Orbits'), self.make_orbits()),
                                ParametersGroup(_('Labels'), self.make_labels()),
                                ParametersGroup(_('Render'), self.make_render()),
                                ParametersGroup(_('UI'), self.make_ui()),
                                ParametersGroup(_('Advanced'), self.make_advanced()),
                                ParametersGroup(_('Debug'), self.make_debug()),
                                ])

    def make_general(self):
        return [ParametersGroup(_('Mouse'),
                                [SettingParameter(_('Invert mouse wheel'), 'invert_wheel', SettingParameter.TYPE_BOOL),
                                 ]),
                ParametersGroup(_('Keyboard'),
                                [SettingParameter(_('Damped navigation keys'), 'damped_nav', SettingParameter.TYPE_BOOL),
                                 SettingParameter(_('Invert Up/Down and Left/Right'), 'celestia_nav', SettingParameter.TYPE_BOOL),
                                 ])
               ]

    def make_orbits(self):
        orbits = [
                (_('Stars'), 'star'),
                (_('Planets'), 'planet'),
                (_('Dwarf planets'),'dwarfplanet'),
                (_('Moons'), 'moon'),
                (_('Minor moons'), 'minormoon'),
                (_('Lost moons'), 'lostmoon'),
                (_('Comets'), 'comet'),
                (_('Asteroids'), 'asteroid'),
                (_('Interstellars'), 'interstellar'),
                (_('Spacecrafts'), 'spacecraft'),
               ]
        params = [ SettingParameter(_('All orbits'), 'show_orbits', SettingParameter.TYPE_BOOL) ]
        params += [ParametricFunctionParameter(label, param_name, bodyClasses.set_show_orbit, bodyClasses.get_show_orbit, SettingParameter.TYPE_BOOL)
                for (label, param_name) in orbits]
        return params

    def make_labels(self):
        labels = [
                  (_('Galaxies'), 'galaxy'),
                  #(_('Globular'), 'globular'),
                  (_('Stars'), 'star'),
                  (_('Planets'), 'planet'),
                  (_('Dwarf planets'), 'dwarfplanet'),
                  (_('Moons'), 'moon'),
                  (_('Minor moons'), 'minormoon'),
                  (_('Lost moons'), 'lostmoon'),
                  (_('Comets'), 'comet'),
                  (_('Asteroids'), 'asteroid'),
                  (_('Interstellars'), 'interstellar'),
                  (_('Spacecrafts'), 'spacecraft'),
                  (_('Constellations'), 'constellation'),
                  #(_('Locations'), 'location'),
                ]
        return [ParametersGroup(_('Labels'),
                                [ParametricFunctionParameter(label, param_name, bodyClasses.set_show_label, bodyClasses.get_show_label, SettingParameter.TYPE_BOOL)
                                 for (label, param_name) in labels]),
                ParametersGroup(_('Fonts'),
                                [SettingParameter(_("Label size"), 'label_size', UserParameter.TYPE_INT, [4, 32]),
                                 SettingParameter(_("Constellation label size"), 'constellations_label_size', UserParameter.TYPE_INT, [4, 32]),
                                 ]),
                ]

    def make_render(self):
        return [
                ParametersGroup(_('Objects'),
                                [ParametricFunctionParameter(_('Galaxies'), 'galaxy',bodyClasses.set_show, bodyClasses.get_show, SettingParameter.TYPE_BOOL),
                                ]),
                #('shift-u', self.cosmonium.toggle_globulars)
                #('^', self.cosmonium.toggle_nebulae)
                ParametersGroup(_('Components'),
                                [SettingParameter(_('Atmospheres'), 'show_atmospheres', SettingParameter.TYPE_BOOL),
                                 SettingParameter(_('Clouds'), 'show_clouds', SettingParameter.TYPE_BOOL),
                                 ]),
                #('control-e', self.toggle_shadows)
                #('control-l', self.cosmonium.toggle_nightsides)
                #('control-t', self.cosmonium.toggle_comet_tails)
                ParametersGroup(_('Constellations'),
                                [SettingParameter(_('Boundaries'), 'show_boundaries', SettingParameter.TYPE_BOOL),
                                 SettingParameter(_('Asterisms'), 'show_asterisms', SettingParameter.TYPE_BOOL),
                                 ]),
                ParametersGroup(_('Grids'),
                                [SettingParameter(_('Equatorial'), 'show_equatorial_grid', SettingParameter.TYPE_BOOL),
                                 SettingParameter(_('Ecliptic'), 'show_ecliptic_grid', SettingParameter.TYPE_BOOL),
                                 ]),
                ParametersGroup(_('Annotations'),
                                [SettingParameter(_('Rotation axis'), 'show_rotation_axis', SettingParameter.TYPE_BOOL),
                                 SettingParameter(_('Reference frame'), 'show_reference_axis', SettingParameter.TYPE_BOOL),
                                 ]),
                ParametersGroup(_('Point-like objects'),
                                [SettingParameter(_('scale with DPI'), 'point_scale_dpi_aware', SettingParameter.TYPE_BOOL),
                                 SettingParameter(_("Custom point scale"), 'custom_point_scale', UserParameter.TYPE_FLOAT, [0.5, 2]),
                                 ]),
                ]

    def make_ui(self):
        return [ParametersGroup(_('UI'),
                                [SettingParameter(_("UI scale with DPI"), 'ui_scale_dpi_aware', UserParameter.TYPE_BOOL),
                                 SettingParameter(_("Custom UI scale"), 'custom_ui_scale', UserParameter.TYPE_FLOAT, [0.5, 2]),
                                 SettingParameter(_("Menu text size"), 'menu_text_size', UserParameter.TYPE_INT, [4, 32]),
                                ]),
                ]

    def make_advanced(self):
        return [ParametersGroup(_('Render'),
                                [SettingParameter(_("Use horizon culling"), 'use_horizon_culling', UserParameter.TYPE_BOOL),
                                 SettingParameter(_("Cull far patches"), 'cull_far_patches', UserParameter.TYPE_BOOL),
                                 SettingParameter(_("Cull far patches threshold"), 'cull_far_patches_threshold', UserParameter.TYPE_INT, [5, 25]),
                                 SettingParameter(_("Shadow slope bias"), 'shadows_slope_scale_bias', UserParameter.TYPE_BOOL),
                                 SettingParameter(_("Shadow PCF"), 'shadows_pcf_16', UserParameter.TYPE_BOOL),
                                 SettingParameter(_("Shadow slope bias"), 'shadows_slope_scale_bias', UserParameter.TYPE_BOOL),
                                ]),
                ParametersGroup(_('OpenGL'),
                                [SettingParameter(_("Sync video"), 'sync_video', UserParameter.TYPE_BOOL),
                                SettingParameter(_("Multisampling"), 'multisamples', UserParameter.TYPE_INT, [0, 16])
                                ]),
                ]
    def make_debug(self):
        return [ParametersGroup(_('Async'),
                                [SettingParameter(_("Sync data loading"), 'sync_data_load', UserParameter.TYPE_BOOL),
                                 SettingParameter(_("Sync texture loading"), 'sync_texture_load', UserParameter.TYPE_BOOL),
                                ])
        ]
