#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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

from panda3d.core import LVector3
from pandamenu.menu import DropDownMenu

from ..bodyclass import bodyClasses
from .. import settings

from .menucommon import create_orbiting_bodies_menu_items, create_orbits_menu_items

class Menubar:
    def __init__(self, messenger, shortcuts, engine):
        self.messenger = messenger
        self.shortcuts = shortcuts
        self.engine = engine
        self.menubar = None

    def menu_text(self, text, state, event, condition=None, args=[]):
        shortcut = self.shortcuts.get_shortcut_for(event)
        if shortcut is not None:
            full_text = text + '>' + shortcut.title()
        else:
            full_text = text
        if condition is not None:
            event = event if condition else 0
        return (full_text, state, self.messenger.send, event, args)

    def create_main_menu_items(self):
        return (
                self.menu_text(_('_Find object'), 0, 'gui-search-object'),
                0,
                self.menu_text(_('_Save URL'), 0, 'save-cel-url'),
                self.menu_text(_('_Load URL'), 0, 'load-cel-url'),
                0,
                self.menu_text(_('Load _CEL script'), 0, 'open-script'),
                0,
                self.menu_text(_('Go to _home'), 0, 'select-home'),
                0,
                self.menu_text(_('_Preferences'), 0, 'gui-show-preferences'),
                0,
                self.menu_text(_('_Quit'), 0, 'exit'),
                )

    def create_time_menu_items(self):
        return (
                self.menu_text(_('_Increase rate 10x'), 0, 'accelerate-time-10'),
                self.menu_text(_('I_ncrease rate 2x'), 0, 'accelerate-time-2'),
                self.menu_text(_('_Decrease rate 10x'), 0, 'slow-time-10'),
                self.menu_text(_('D_ecrease rate 2x'), 0, 'slow-time-2'),
                self.menu_text(_('_Reverse time'), 0, 'invert-time'),
                self.menu_text(_('_Freeze time'), 0, 'toggle-freeze-time'),
                self.menu_text(_('_Set real time'), 0, 'set-real-time'),
                0,
                self.menu_text(_('Set _time...'), 0, 'gui-show-time-editor'),
                self.menu_text(_('Set _current time'), 0, 'set-current-date'),
                self.menu_text(_('Set _J2000 epoch'), 0, 'set-j2000-date'),
                )

    def create_select_menu_items(self):
        has_selected = self.engine.selected is not None
        orbiting_bodies = create_orbiting_bodies_menu_items(self.engine, self.engine.selected)
        orbits = create_orbits_menu_items(self.engine, self.engine.selected)
        return (
            self.menu_text(_('_Info'), 0, 'gui-show-info', has_selected),
            self.menu_text(_('_Edit'), 0, 'gui-show-editor', has_selected),
            0,
            self.menu_text(_('_Go to'), 0, 'goto-selected', has_selected),
            self.menu_text(_('Go to f_ront'), 0, 'goto-front', has_selected),
            self.menu_text(_('Go to _surface'), 0, 'goto-surface', has_selected),
            0,
            self.menu_text(_('_Follow'), 0, 'follow-selected', has_selected),
            self.menu_text(_('S_ync'), 0, 'sync-selected', has_selected),
            0,
            self.menu_text(_('_Reset navigation'), 0, 'cancel', has_selected),
            0,
            (_("Orbiting bodies"), 0, orbiting_bodies),
            (_("Orbits"), 0, orbits),
        )

    def create_camera_menu_items(self):
        has_selected = self.engine.selected is not None
        controllers = []
        for controller in self.engine.camera_controllers:
            activable = self.engine.ship.supports_camera_mode(controller.camera_mode) and (not controller.require_target() or self.engine.selected is not None)
            controllers.append((controller.get_name(),
                                self.engine.camera_controller is controller,
                                self.engine.set_camera_controller if activable else 0,
                                controller))
        ships = []
        for ship in self.engine.ships:
            ships.append((ship.get_name(), self.engine.ship is ship, self.engine.set_ship, ship))

        return (
                (_('_Mode'), 0, controllers),
                0,
                self.menu_text(_('_Center on'), 0, 'center-selected', has_selected),
                #('Look _back'), '*'), 0, self.camera.camera_look_back),
                self.menu_text(_('_Track'), 0, 'track-selected', has_selected),
                0,
                self.menu_text(_('Zoom _in'), 0, 'zoom-in'),
                self.menu_text(_('Zoom _out'), 0, 'zoom-out'),
                self.menu_text(_('_Reset Zoom'), 0, 'reset-zoom'),
                0,
                (_('_Select ship'), 0, ships if len(self.engine.ships) > 1 else 0),
                self.menu_text(_('_Edit ship'), 0, 'gui-show-ship-editor', self.engine.ship.editable),
                )

    def create_render_menu_items(self):
        labels = (
                  self.menu_text(_('_Galaxies'), bodyClasses.get_show_label('galaxy'), 'toggle-label-galaxy'),
                  #self.menu_text(_('Globular'), bodyClasses.get_show_label('globular'), 'toggle-label-globular'),
                  self.menu_text(_('_Stars'), bodyClasses.get_show_label('star'), 'toggle-label-star'),
                  self.menu_text(_('_Planets'), bodyClasses.get_show_label('planet'), 'toggle-label-planet'),
                  self.menu_text(_('_Dwarf planets'), bodyClasses.get_show_label('dwarfplanet'), 'toggle-label-dwarfplanet'),
                  self.menu_text(_('_Moons'), bodyClasses.get_show_label('moon'), 'toggle-label-moon'),
                  self.menu_text(_('M_inor Moons'), bodyClasses.get_show_label('minormoon'), 'toggle-label-minormoon'),
                  self.menu_text(_('L_ost Moons'), bodyClasses.get_show_label('lostmoon'), 'toggle-label-lostmoon'),
                  self.menu_text(_('C_omets'), bodyClasses.get_show_label('comet'), 'toggle-label-comet'),
                  self.menu_text(_('_Asteroids'), bodyClasses.get_show_label('asteroid'), 'toggle-label-asteroid'),
                  self.menu_text(_('I_nterstellars'), bodyClasses.get_show_label('interstellar'), 'toggle-label-interstellar'),
                  self.menu_text(_('S_pacecrafts'), bodyClasses.get_show_label('spacecraft'), 'toggle-label-spacecraft'),
                  self.menu_text(_('_Constellations'), bodyClasses.get_show_label('constellation'), 'toggle-label-constellation'),
                  #self.menu_text(_('Locations'), self.toggle_label, 'location'),
                  )

        orbits = (
                  self.menu_text(_('All _orbits'), settings.show_orbits, 'toggle-orbits'),
                  0,
                  self.menu_text(_('_Stars'), bodyClasses.get_show_orbit('star'), 'toggle-orbit-star'),
                  self.menu_text(_('_Planets'), bodyClasses.get_show_orbit('planet'), 'toggle-orbit-planet'),
                  self.menu_text(_('_Dwarf planets'), bodyClasses.get_show_orbit('dwarfplanet'), 'toggle-orbit-dwarfplanet'),
                  self.menu_text(_('_Moons'), bodyClasses.get_show_orbit('moon'), 'toggle-orbit-moon'),
                  self.menu_text(_('M_inor moons'), bodyClasses.get_show_orbit('minormoon'), 'toggle-orbit-minormoon'),
                  self.menu_text(_('L_ost moons'), bodyClasses.get_show_orbit('lostmoon'), 'toggle-orbit-lostmoon'),
                  self.menu_text(_('_Comets'), bodyClasses.get_show_orbit('comet'), 'toggle-orbit-comet'),
                  self.menu_text(_('_Asteroids'), bodyClasses.get_show_orbit('asteroid'), 'toggle-orbit-asteroid'),
                  self.menu_text(_('I_nterstellars'), bodyClasses.get_show_orbit('interstellar'), 'toggle-orbit-interstellar'),
                  self.menu_text(_('S_pacecrafts'), bodyClasses.get_show_orbit('spacecraft'), 'toggle-orbit-spacecraft'),
                  )

        bodies = (
                  self.menu_text(_('_Galaxies'), bodyClasses.get_show('galaxy'), 'toggle-body-class-galaxy'),
                  #self.menu_text(_('shift-u', self.engine.toggle_globulars)
                  #(elf.menu_text(_('^', self.engine.toggle_nebulae)
                  )

        options = (
                   self.menu_text(_('_Atmospheres'), settings.show_atmospheres, 'toggle-atmosphere'),
                   self.menu_text(_('_Clouds'), settings.show_clouds, 'toggle-clouds'),
                   #self.menu_text(_('control-e'), self.toggle_shadows)
                   #self.menu_text(_('control-l)', self.engine.toggle_nightsides)
                   #self.menu_text(_('control-t'), self.engine.toggle_comet_tails)
                   )

        guides = (
                   self.menu_text(_('_Boundaries'), settings.show_boundaries, 'toggle-constellations-boundaries'),
                   self.menu_text(_('_Asterisms'), settings.show_asterisms, 'toggle-asterisms'),
                   )

        grids = (
                 self.menu_text(_('_Equatorial'), settings.show_equatorial_grid, 'toggle-equatorial-grid'),
                 self.menu_text(_('E_cliptic'), settings.show_ecliptic_grid, 'toggle-ecliptic-grid'),
                 )

        stereo = (
                    self.menu_text(_('Hardware support'), settings.stereoscopic_framebuffer, 'toggle-stereoscopic-framebuffer'),
                    self.menu_text(_('Red-Blue'), settings.red_blue_stereo, 'toggle-red_blue-stereo'),
                    self.menu_text(_('Side by side'), settings.side_by_side_stereo, 'toggle-side-by_side-stereo'),
                    self.menu_text(_('Swap eyes'), settings.stereo_swap_eyes, 'toggle-swap-eyes'),
                    )

        advanced = (
                    self.menu_text(_('_Decrease ambient'), 0, 'decrease-ambient'),
                    self.menu_text(_('_Increase ambient'), 0, 'increase-ambient'),
                    0,
                    self.menu_text(_('Fewer _Stars Visible'), 0, 'decrease-limit-magnitude'),
                    self.menu_text(_('_More Stars Visible'), 0, 'increase-limit-magnitude'),
                    0,
                    self.menu_text(_('_Rotation axis'), settings.show_rotation_axis, 'toggle-rotation-axis'),
                    self.menu_text(_('Reference _frame'), settings.show_reference_axis, 'toggle-reference-axis'),
                    )

        return (
            (_('_Labels'), 0, labels),
            (_('_Orbits'), 0, orbits),
            (_('_Bodies'), 0, bodies),
            (_('O_ptions'), 0, options),
            (_('_Grids'), 0, grids),
            (_('G_uides'), 0, guides),
            (_('_3D'), 0, stereo),
            (_('_Advanced'), 0, advanced),
        )

    def create_window_menu_items(self):
        return (
                self.menu_text(_('Toggle _fullscreen'), 0, 'toggle-fullscreen'),
                self.menu_text(_('Toggle _menubar'), 0, 'gui-toggle-menubar'),
                self.menu_text(_('Toggle _HUD'), 0, 'toggle-hud'),
                0,
                self.menu_text(_('Save _screenshot'), 0, 'save-screenshot'),
                self.menu_text(_('Save screenshot _without UI'), 0, 'save-screenshot-no-gui'),
                self.menu_text(_('Set screenshots directory...'), 0, 'gui-show-select-screenshots'),
                )

    def create_debug_menu_items(self):
        fps = (
                self.menu_text(_('Frame per second'), settings.display_fps, 'set-render-fps'),
                self.menu_text(_('Render time'), settings.display_ms, 'set-render-ms'),
                self.menu_text(_("None"), not (settings.display_fps or settings.display_ms), 'set-render-none'),
                )
        shaders = (
                self.menu_text(_('Default'), settings.shader_debug_fragment_shader == 'default', 'debug-shader-fragment-mode', args=['default']),
                self.menu_text(_('Diffuse'), settings.shader_debug_fragment_shader == 'diffuse', 'debug-shader-fragment-mode', args=['diffuse']),
                self.menu_text(_('Normals'), settings.shader_debug_fragment_shader == 'normal', 'debug-shader-fragment-mode', args=['normal']),
                self.menu_text(_('Normal map'), settings.shader_debug_fragment_shader == 'normalmap', 'debug-shader-fragment-mode', args=['normalmap']),
                self.menu_text(_('Shadows'), settings.shader_debug_fragment_shader == 'shadows', 'debug-shader-fragment-mode', args=['shadows']),
                self.menu_text(_('Heightmap'), settings.shader_debug_fragment_shader == 'heightmap', 'debug-shader-fragment-mode', args=['heightmap']),
                self.menu_text(_('Color picking'), settings.shader_debug_fragment_shader == 'picking', 'debug-shader-fragment-mode', args=['picking']),
                self.menu_text(_('Ray hit'), settings.shader_debug_raymarching_canvas, 'debug-toggle-shader-raymarching-canvas'),
                self.menu_text(_('Show slice'), settings.shader_debug_raymarching_slice, 'debug-toggle-shader-debug-raymarching_slice'),
                )
        return (
                self.menu_text(_('Toggle filled wireframe'), 0, 'debug-toggle-filled-wireframe'),
                self.menu_text(_('Toggle wireframe'), 0, 'debug-toggle-wireframe'),
                self.menu_text(_("Show render buffers"), 0, 'debug-toggle-buffer-viewer'),
                self.menu_text(_('Show shadow frustum'), settings.debug_shadow_frustum, 'debug-toggle-shadows-frustum'),
                0,
                (_('Shaders'), 0, shaders),
                self.menu_text(_('Instant movement'), settings.debug_jump, 'debug-toggle-jump'),
                self.menu_text(_('Connect pstats'), 0, 'debug-connect-pstats'),
                (_('Render info'), 0, fps),
                0,
                self.menu_text(_('Freeze LOD'), settings.debug_lod_freeze, 'debug-freeze-lod'),
                self.menu_text(_('Dump LOD stats'), 0, 'debug-dump-objects-stats'),
                self.menu_text(_('Dump LOD tree'), 0, 'debug-dump-objects-info'),
                self.menu_text(_('Log LOD events'), settings.debug_lod_split_merge, 'debug-toggle-split-merge-log'),
                self.menu_text(_('Show boundaries'), settings.shader_debug_coord, 'debug-toggle-shader-debug-coord'),
                self.menu_text(_('Show LOD bounding boxes'), settings.debug_lod_show_bb, 'debug-toggle-bounding-boxes'),
                self.menu_text(_('Show LOD culling frustum'), settings.debug_lod_frustum, 'debug-toggle-lod-frustum'),
                0,
                self.menu_text(_('Show octree stats'), 0, 'debug-dump-octree-stats'),
                self.menu_text(_('Dump octree'), 0, 'debug-dump-octree'),
                )

    def create_help_menu_items(self):
        return (
       self.menu_text(_('User _guide'), 0, 'gui-show-help'),
       0, # separator
       self.menu_text(_('_Credits'), 0, 0),
       self.menu_text(_('_License'), 0, 'gui-show-license'),
       0, # separator
       self.menu_text(_('_About'), 0, 'gui-show-about'),
       )

    def create(self, font, scale):
        scale = LVector3(scale[0], 1.0, scale[1])
        scale[0] *= settings.menu_text_size
        scale[2] *= settings.menu_text_size
        self.menubar = DropDownMenu(
            items=((_('_Cosmonium'), self.create_main_menu_items),
                   (_('_Select'), self.create_select_menu_items),
                   (_('_Time'), self.create_time_menu_items),
                   (_('Camera'), self.create_camera_menu_items),
                   (_('_Render'), self.create_render_menu_items),
                   (_('_Window'), self.create_window_menu_items),
                   (_('_Debug'), self.create_debug_menu_items),
                   (_('_Help'), self.create_help_menu_items),),
            font=font,
            sidePad=.75,
            align=DropDownMenu.ALeft,
            baselineOffset=-.35,
            scale=scale, itemHeight=1.2, leftPad=.2,
            separatorHeight=.3,
            underscoreThickness=1,
            BGColor=(.9,.9,.9,.9),
            BGBorderColor=(.3,.3,.3,1),
            separatorColor=(0,0,0,1),
            frameColorHover=(.3,.3,.3,1),
            frameColorPress=(.3,.3,.3,.1),
            textColorReady=(0,0,0,1),
            textColorHover=(.7,.7,.7,1),
            textColorPress=(0,0,0,1),
            textColorDisabled=(.3,.3,.3,1))

    def show(self):
        self.menubar.menu.unstash()

    def hide(self):
        self.menubar.menu.stash()

    def get_height(self):
        return self.menubar.height
