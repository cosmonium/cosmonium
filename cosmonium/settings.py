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

from panda3d.core import LColor
from panda3d.core import LPoint3, LPoint3d

from .astro import units
from .bodyclass import BodyClass, bodyClasses
from appdirs.appdirs import AppDirs

import os

app_name = 'cosmonium'
version = '0.1.2-dev'

use_double = LPoint3 == LPoint3d
cache_yaml = True
prc_file = 'config.prc'

#OpenGL user configuration
use_core_profile_mac = True
use_gl_version = None
use_hardware_srgb = True
use_multisampling = True
multisamples = 2
use_hardware_sprites = True
use_floating_point_buffer = True
force_power_of_two_textures = False
use_hardware_tessellation = True
use_hardware_instancing = True
use_inverse_z = False
instancing_use_tex = True
use_texture_array = True

stereoscopic_framebuffer = False
red_blue_stereo = False
side_by_side_stereo = False
stereo_swap_eyes = False

#Settings
use_hdr = False
use_srgb = True
use_assimp = True
encode_float = False

deferred=False
deferred_split=False
deferred_load=True
patch_pool_size = 4

mouse_over = False
celestia_nav = True
invert_wheel = False
damped_nav = True

global_ambient = 0.0
corrected_global_ambient = global_ambient
allow_shadows = True
shadow_size = 1024
max_vertex_size_patch = 64
max_sprite_size = 400
use_patch_adaptation = True
use_patch_skirts = True

render_points = True
render_sprite_points = True
show_halo = True
disable_tint = False
software_instancing = False

hud_font = 'DejaVuSans'
markdown_font = 'DejaVuSans'
label_font = 'DejaVuSans'

label_size = 12
constellations_label_size = 16
convert_utf8 = True

use_inv_scaling=True
use_log_scaling=False
use_depth_scaling = use_inv_scaling or use_log_scaling
auto_scale=True
lens_far_limit = 1e-7
scale=1000.0
min_scale = 0.02
max_scale=1000.0
set_frustum=True
near_plane=1.0
far_plane=30000.0
infinite_far_plane = True
infinite_plane = 50000.0
auto_infinite_plane = False
mid_plane_ratio = 1.1
default_fov = 40.0
min_fov = 0.001
max_fov = 120.0

if use_double:
    offset_body_center = False
    shift_patch_origin = True
else:
    offset_body_center = True
    shift_patch_origin = True

min_altitude = 2 * units.m

shader_noise=True
c_noise=True

debug_vt = False
debug_lod_show_bb = False
debug_lod_freeze = False
debug_lod_split_merge = False
debug_lod_frustum = False
dump_shaders = True
dump_panda_shaders = False
debug_shadow_frustum = False
debug_sync_load = False

debug_jump = False

use_vertex_shader = False

min_mag_scale = 0.1
lowest_app_magnitude = 6.0
max_app_magnitude = 0.0
mag_pixel_scale = 2
min_body_size = 2

smallest_glare_mag = 1.0
largest_glare_mag = -2.0

label_lowest_app_magnitude = 4.0

axis_fade = 20
axis_thickness = 0.9

show_clouds = True
show_atmospheres = True
show_asterisms = False
show_boundaries = False
show_ecliptic_grid = False
show_equatorial_grid = False
show_rotation_axis = False
show_reference_axis = False

show_orbits = False
orbit_fade = 20
label_fade = 20
orbit_thickness = 0.6

grid_thickness = 0.5

asterism_thickness = 0.9
boundary_thickness = 0.9

wireframe_fill_color = LColor(0.5, 0.5, 0.5, 1.0)

fast_move = 2.0
slow_move = 5.0
default_distance = 5.0

show_hud = True
show_menubar = True
hud_color = LColor(0.7, 0.7, 1.0, 1.0)
help_color = LColor(1.0, 1.0, 1.0, 1.0)
help_background = LColor(0.5, 0.5, 0.5, 0.7)

menu_text_size = 12

query_delay = 0.333

#These are the fake depth value used for sorting background bin objects
skysphere_depth = 0
asterisms_depth = 10
constellations_depth = 15
boundaries_depth = 20
deep_space_depth = 50
halo_depth = 100

shader_version = None
core_profile = None
render_scene_to_buffer = False
render_scene_to_float = False
non_power_of_two_textures = False
disable_multisampling = False
floating_point_buffer = False
buffer_texture = False
hdr = False
srgb = False
srgb_buffer = False
srgb_texture = False
software_srgb = False
hardware_tessellation = False
hardware_instancing = False
texture_array = False

# Window configuration
win_fullscreen = False
win_width = 1024
win_height = 768
win_fs_width = 1024
win_fs_height = 768

# Application paths and files
appdirs = AppDirs(app_name)
cache_dir = appdirs.user_cache_dir
config_dir = appdirs.user_config_dir
data_dir = appdirs.user_data_dir
config_file = os.path.join(config_dir, 'config.yaml')

bodyClasses.register_class("galaxy", "galaxies",
                           BodyClass(label_color=LColor(0.0, 0.45, 0.5, 1),
                                     orbit_color=LColor(1, 1, 1, 1),
                                     show_label=False))
bodyClasses.register_class("globular", "globulars",
                           BodyClass(label_color=LColor(0.8, 0.45, 0.5, 1),
                                     orbit_color=LColor(1, 1, 1, 1),
                                     show_label=False))
bodyClasses.register_class("nebula", "nebulae",
                           BodyClass(label_color=LColor(0.541, 0.764, 0.278, 1),
                                     orbit_color=LColor(1, 1, 1, 1),
                                     show_label=False))
bodyClasses.register_class("star", "stars",
                           BodyClass(label_color=LColor(0.471, 0.356, 0.682, 1),
                                     orbit_color=LColor(0.5, 0.5, 0.8, 1),
                                     show_label=False))
bodyClasses.register_class("planet", "planets",
                           BodyClass(label_color=LColor(0.407, 0.333, 0.964, 1),
                                     orbit_color=LColor(0.3, 0.323, 0.833, 1),
                                     show_label=False))
bodyClasses.register_class("dwarfplanet", "dwarfplanets",
                           BodyClass(label_color=LColor(0.407, 0.333, 0.964, 1),
                                     orbit_color=LColor(0.3, 0.323, 0.833, 1),
                                     show_label=False))
bodyClasses.register_class("moon", "moons",
                           BodyClass(label_color=LColor(0.231, 0.733, 0.792, 1),
                                     orbit_color=LColor(0.08, 0.407, 0.392, 1),
                                     show_label=False))
bodyClasses.register_class("minormoon", "minormoons",
                           BodyClass(label_color=LColor(0.231, 0.733, 0.792, 1),
                                     orbit_color=LColor(0.08, 0.407, 0.392, 1),
                                     show_label=False))
bodyClasses.register_class("comet", "comets",
                           BodyClass(label_color=LColor(0.768, 0.607, 0.227, 1),
                                     orbit_color=LColor(0.639, 0.487, 0.168, 1),
                                     show_label=False))
bodyClasses.register_class("asteroid", "asteroids",
                           BodyClass(label_color=LColor(0.596, 0.305, 0.164, 1),
                                     orbit_color=LColor(0.58, 0.152, 0.08, 1),
                                     show_label=False))
bodyClasses.register_class("interstellar", "interstellars",
                           BodyClass(label_color=LColor(0.596, 0.305, 0.164, 1),
                                     orbit_color=LColor(0.58, 0.152, 0.08, 1),
                                     show_label=False))
bodyClasses.register_class("spacecraft", "spacecrafts",
                           BodyClass(label_color=LColor(0.93, 0.93, 0.93, 1),
                                     orbit_color=LColor(0.4, 0.4, 0.4, 1),
                                     show_label=False))
bodyClasses.register_class("constellation", "constellations",
                           BodyClass(label_color=LColor(0.225, 0.301, 0.36, 1),
                                     orbit_color=LColor(0.0,   0.24,  0.36, 1.0),
                                     show_label=False))
bodyClasses.register_class("boundary", "boundaries",
                           BodyClass(orbit_color=LColor(0.24,  0.10,  0.12, 1.0)))
