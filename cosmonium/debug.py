# -*- coding: utf-8 -*-
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

from .bodies import StellarBody
from . import settings

class Debug:
    def __init__(self, engine):
        self.engine = engine

    def toggle_buffer_viewer(self):
        base.bufferViewer.toggleEnable()

    def list_scene(self):
        self.engine.scene_manager.ls()

    def open_scene_explorer(self):
        render.explore()

    def analyse_scene(self):
        render.analyze()

    def print_tasks(self):
        print(taskMgr)

    def toggle_jump(self):
        settings.debug_jump = not settings.debug_jump
        if settings.debug_jump:
            self.engine.gui.update_info(_("Instant move"))
        else:
            self.engine.gui.update_info(_("Normal move"))

    def toggle_lod_freeze(self):
        settings.debug_lod_freeze = not settings.debug_lod_freeze
        if settings.debug_lod_freeze:
            self.engine.gui.update_info(_("Freeze LOD"))
        else:
            self.engine.gui.update_info(_("Unfreeze LOD"))

    def toggle_bb(self):
        settings.debug_lod_show_bb = not settings.debug_lod_show_bb
        self.engine.trigger_check_settings = True

    def toggle_frustum(self):
        settings.debug_lod_frustum = not settings.debug_lod_frustum
        self.engine.trigger_check_settings = True

    def toggle_shadow_frustum(self):
        settings.debug_shadow_frustum = not settings.debug_shadow_frustum
        self.engine.trigger_check_settings = True

    def dump_object_stats(self):
        selected = self.engine.selected
        if selected is None: return
        if not isinstance(selected, StellarBody): return
        if selected.surface is not None:
            shape = selected.surface.shape
            if shape.patchable:
                print("Surface")
                shape.dump_stats()
        if selected.clouds is not None:
            shape = selected.clouds.shape
            if shape.patchable:
                print("Clouds")
                shape.dump_stats()

    def dump_object_info(self):
        selected = self.engine.selected
        if selected is None: return
        if not isinstance(selected, StellarBody): return
        if selected.surface is not None:
            shape = selected.surface.shape
            if shape.patchable:
                print("Surface")
                shape.dump_tree()
        if selected.clouds is not None:
            shape = selected.clouds.shape
            if shape.patchable:
                print("Clouds")
                shape.dump_tree()

    def dump_object_info_2(self):
        selected = self.engine.selected
        if selected is None: return
        if not isinstance(selected, StellarBody): return
        if selected.surface is not None:
            shape = selected.surface.shape
            if shape.patchable:
                print("Surface")
                shape.dump_patches()
        if selected.clouds is not None:
            shape = selected.clouds.shape
            if shape.patchable:
                print("Clouds")
                shape.dump_patches()

    def toggle_split_merge_debug(self):
        settings.debug_lod_split_merge = not settings.debug_lod_split_merge

    def set_shader_fragment_debug(self, mode):
        settings.shader_debug_fragment_shader = mode
        self.engine.trigger_check_settings = True

    def toggle_shader_debug_coord(self):
        settings.shader_debug_coord = not settings.shader_debug_coord
        self.engine.trigger_check_settings = True

    def toggle_shader_debug_raymarching_canvas(self):
        settings.shader_debug_raymarching_canvas = not settings.shader_debug_raymarching_canvas
        self.engine.trigger_check_settings = True

    def toggle_shader_debug_raymarching_slice(self):
        settings.shader_debug_raymarching_slice = not settings.shader_debug_raymarching_slice
        self.engine.trigger_check_settings = True
