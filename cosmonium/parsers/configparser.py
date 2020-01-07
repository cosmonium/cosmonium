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

from .yamlparser import YamlParser
from .. import settings

import os

class ConfigParser(YamlParser):
    data_version = 1
    def __init__(self, config_file):
        YamlParser.__init__(self)
        self.config_file = config_file

    def load(self):
        if os.path.exists(self.config_file):
            print("Loading config file", self.config_file)
            self.load_and_parse(self.config_file)

    def save(self):
        config_dir = os.path.dirname(self.config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        self.encode_and_store(self.config_file)

    def decode_body_class(self, data):
        for (name, body_class) in bodyClasses.classes.items():
            entry = data.get(name, {})
            body_class.show = entry.get('show', True)
            body_class.show_orbit = entry.get('orbit', True)
            body_class.show_label = entry.get('label', False)

    def encode_body_class(self):
        data = {}
        for (name, body_class) in bodyClasses.classes.items():
            entry = {}
            entry['show'] = body_class.show
            entry['orbit'] = body_class.show_orbit
            entry['label'] = body_class.show_label
            data[name] = entry
        return data

    def decode_render(self, data):
        settings.show_orbits = data.get('orbits', settings.show_orbits)
        settings.show_clouds = data.get('clouds', settings.show_clouds)
        settings.show_atmospheres = data.get('atmospheres', settings.show_atmospheres)
        settings.show_asterisms = data.get('asterisms', settings.show_asterisms)
        settings.show_boundaries = data.get('boundaries', settings.show_boundaries)
        settings.show_rotation_axis = data.get('rotation-axis', settings.show_rotation_axis)
        settings.show_reference_axis = data.get('reference-axis', settings.show_reference_axis)
        settings.show_ecliptic_grid = data.get('ecliptic-grid', settings.show_ecliptic_grid)
        settings.show_equatorial_grid = data.get('equatorial-grid', settings.show_equatorial_grid)
        settings.global_ambient = data.get('global-ambient', settings.global_ambient)

    def encode_render(self):
        data = {}
        data['orbits'] = settings.show_orbits
        data['clouds'] = settings.show_clouds
        data['atmospheres'] = settings.show_atmospheres
        data['asterisms'] = settings.show_asterisms
        data['boundaries'] = settings.show_boundaries
        data['ecliptic-grid'] = settings.show_ecliptic_grid
        data['equatorial-grid'] = settings.show_equatorial_grid
        data['rotation-axis'] = settings.show_rotation_axis
        data['reference-axis'] = settings.show_reference_axis
        data['global-ambient'] = settings.global_ambient
        return data

    def decode_ui_hud(self, data):
        settings.show_hud = data.get('visible', settings.show_hud)
        settings.hud_font = data.get('font', settings.hud_font)
        settings.hud_color = data.get('color', settings.hud_color)

    def encode_ui_hud(self):
        data = {}
        data['visible'] = settings.show_hud
        data['font'] = settings.hud_font
        data['color'] = list(settings.hud_color)
        return data

    def decode_ui_menu(self, data):
        settings.show_menubar = data.get('visible', settings.show_menubar)

    def encode_ui_menu(self):
        data = {}
        data['visible'] = settings.show_menubar
        return data

    def decode_ui_nav(self, data):
        settings.invert_wheel = data.get('invert-wheel', settings.invert_wheel)
        settings.celestia_nav = data.get('celestia-nav', settings.celestia_nav)
        settings.damped_nav = data.get('damped-nav', settings.damped_nav)

    def encode_ui_nav(self):
        data = {}
        data['invert-wheel'] = settings.invert_wheel
        data['celestia-nav'] = settings.celestia_nav
        data['damped-nav'] = settings.damped_nav
        return data

    def decode_ui_labels(self, data):
        settings.label_font = data.get('font', settings.label_font)
        settings.label_size = data.get('size', settings.label_size)

    def encode_ui_labels(self):
        data = {}
        data['font'] = settings.label_font
        data['size'] = settings.label_size
        return data

    def decode_ui_constellations(self, data):
        settings.constellations_label_size = data.get('size', settings.constellations_label_size)

    def encode_ui_constellations(self):
        data = {}
        data['size'] = settings.constellations_label_size
        return data

    def decode_ui(self, data):
        self.decode_ui_hud(data.get('hud', {}))
        self.decode_ui_menu(data.get('menu', {}))
        self.decode_ui_nav(data.get('nav', {}))
        self.decode_ui_labels(data.get('labels', {}))
        self.decode_ui_constellations(data.get('constellations', {}))

    def encode_ui(self):
        data = {}
        data['hud'] = self.encode_ui_hud()
        data['menu'] = self.encode_ui_menu()
        data['nav'] = self.encode_ui_nav()
        data['labels'] = self.encode_ui_labels()
        data['constellations'] = self.encode_ui_constellations()
        return data

    def decode_win(self, data):
        settings.win_fullscreen = data.get('fullscreen', settings.win_fullscreen)
        settings.win_width = data.get('width', settings.win_width)
        settings.win_height = data.get('height', settings.win_height)
        settings.win_fs_width = data.get('fs-width', settings.win_fs_width)
        settings.win_fs_height = data.get('fs-height', settings.win_fs_height)

    def encode_win(self):
        data = {}
        data['fullscreen'] = settings.win_fullscreen
        data['width'] = settings.win_width
        data['height'] = settings.win_height
        data['fs-width'] = settings.win_fs_width
        data['fs-height'] = settings.win_fs_height
        return data

    def decode_opengl(self, data):
        settings.multisamples = data.get('multisamples', settings.multisamples)
        settings.use_srgb = data.get('srgb', settings.use_srgb)
        settings.use_hardware_srgb = data.get('hw-srgb', settings.use_hardware_srgb)
        settings.use_hardware_tessellation = data.get('hw-tessellation', settings.use_hardware_tessellation)
        settings.use_hardware_instancing = data.get('hw-instancing', settings.use_hardware_instancing)
        settings.use_floating_point_buffer = data.get('hw-fp-buffer', settings.use_floating_point_buffer)
        settings.use_texture_array = data.get('texture-array', settings.use_texture_array)
        settings.use_core_profile_mac = data.get('core-profile-mac', settings.use_core_profile_mac)
        settings.use_gl_version = data.get('gl-version', settings.use_gl_version)
        settings.stereoscopic_framebuffer = data.get('framebuffer-stereo', settings.stereoscopic_framebuffer)
        settings.red_blue_stereo = data.get('red-blue-stereo', settings.red_blue_stereo)
        settings.side_by_side_stereo = data.get('side-by-side-stereo', settings.side_by_side_stereo)
        settings.stereo_swap_eyes = data.get('swap-eyes', settings.stereo_swap_eyes)

    def encode_opengl(self):
        data = {}
        data['multisamples'] = settings.multisamples
        data['srgb'] = settings.use_srgb
        data['hw-srgb'] = settings.use_hardware_srgb
        data['hw-tessellation'] = settings.use_hardware_tessellation
        data['hw-instancing'] = settings.use_hardware_instancing
        data['hw-fp-buffer'] = settings.use_floating_point_buffer
        data['texture-array'] = settings.use_texture_array
        data['core-profile-mac'] = settings.use_core_profile_mac
        data['gl-version'] = settings.use_gl_version
        data['framebuffer-stereo'] = settings.stereoscopic_framebuffer
        data['red-blue-stereo'] = settings.red_blue_stereo
        data['side-by-side-stereo'] = settings.side_by_side_stereo
        data['swap-eyes'] = settings.stereo_swap_eyes
        return data

    def decode_debug(self, data):
        settings.debug_jump = data.get('instant-jump', settings.debug_jump)
        settings.debug_sync_load = data.get('sync-load', settings.debug_sync_load)

    def encode_debug(self):
        data = {}
        data['instant-jump'] = settings.debug_jump
        data['sync-load'] = settings.debug_sync_load
        return data

    def decode_screenshots(self, data):
        settings.screenshot_path = data.get('path', settings.screenshot_path)
        #TODO: improve data validation...
        if settings.screenshot_path == '': settings.screenshot_path = '.'
        settings.screenshot_filename = data.get('filename', settings.screenshot_filename)
        settings.screenshot_format = data.get('format', settings.screenshot_format)

    def encode_screenshots(self):
        data = {}
        data['path'] = settings.screenshot_path
        data['filename'] = settings.screenshot_filename
        data['format'] = settings.screenshot_format
        return data

    def decode(self, data):
        if data is None: return
        if data.get('version', 0) != self.data_version:
            print("Incompatible configuration file", data.get('version', 0))
            return
        self.decode_render(data.get('render', {}))
        self.decode_body_class(data.get('body-class', {}))
        self.decode_ui(data.get('ui', {}))
        self.decode_win(data.get('win', {}))
        self.decode_opengl(data.get('opengl', {}))
        self.decode_debug(data.get('debug', {}))
        self.decode_screenshots(data.get('screenshots', {}))

    def encode(self):
        data = {}
        data['version'] = self.data_version
        data['render'] =  self.encode_render()
        data['body-class'] = self.encode_body_class()
        data['ui'] = self.encode_ui()
        data['win'] = self.encode_win()
        data['opengl'] = self.encode_opengl()
        data['screenshots'] = self.encode_screenshots()
        return data

configParser = ConfigParser(settings.config_file)
