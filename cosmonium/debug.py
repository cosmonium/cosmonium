# -*- coding: utf-8 -*-
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


from math import pi

from .objects.stellarbody import StellarBody
from .objects.reflective import ReflectiveBody
from .astro import units
from . import settings
from . import utils


class Debug:
    def __init__(self, engine):
        self.engine = engine

    def toggle_buffer_viewer(self):
        self.engine.bufferViewer.toggleEnable()

    def list_scene(self):
        self.engine.scene_manager.ls()

    def open_scene_explorer(self):
        self.engine.render.explore()

    def analyse_scene(self):
        self.engine.render.analyze()

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

    def print_info(self):
        print("Global:")
        print("\tscale", self.scene_manager.scale)
        print("\tPlanes", self.observer.lens.get_near(), self.observer.lens.get_far())
        print("\tFoV", self.observer.lens.get_fov())
        print("Camera:")
        print("\tGlobal position", self.observer.get_absolute_reference_point())
        print("\tLocal position", self.observer.get_local_position())
        print("\tRotation", self.observer.get_absolute_orientation())
        print("\tCamera vector", self.observer.anchor.camera_vector)
        print("\tFrame position", self.observer.get_frame_position(), "rotation", self.observer.get_frame_orientation())
        if self.selected:
            print("Selected:", utils.join_names(self.selected.names))
            print("\tType:", self.selected.__class__.__name__)
            print("\tDistance:", self.selected.anchor.distance_to_obs / units.Km, 'Km')
            print("\tRadius", self.selected.get_apparent_radius(), "Km", "Extend:", self.selected.get_bounding_radius(), "Km", "Visible:", self.selected.anchor.visible, self.selected.anchor.visible_size, "px")
            print("\tApp magnitude:", self.selected.get_app_magnitude(), '(', self.selected.get_abs_magnitude(), ')')
            if isinstance(self.selected, StellarBody):
                print("\tPhase:", self.selected.get_phase())
            print("\tGlobal position", self.selected.anchor.get_absolute_reference_point())
            print("\tLocal position", self.selected.anchor.get_local_position(), '(Frame:', self.selected.anchor.orbit.get_frame_position_at(self.time.time_full), ')')
            print("\tOrientation", self.selected.anchor.get_absolute_orientation())
            print("\tVector to obs", self.selected.anchor.vector_to_obs)
            print("\tVisible:", self.selected.anchor.visible, "Resolved:", self.selected.anchor.resolved, '(', self.selected.anchor.visible_size, ') Override:', self.selected.anchor.visibility_override)
            print("\tUpdate frozen:", self.selected.anchor.update_frozen)
            print("\tOrbit:", self.selected.anchor.orbit.__class__.__name__, self.selected.anchor.orbit.frame)
            print("\tRotation:", self.selected.anchor.rotation.__class__.__name__, self.selected.anchor.rotation.frame)
            if self.selected.label is not None:
                print("\tLabel visible:", self.selected.label.visible)
            if isinstance(self.selected, ReflectiveBody) and self.selected.surface is not None:
                print("\tRing shadow:", self.selected.surface.shadows.ring_shadow is not None)
                #print("\tSphere shadow:", [x.body.get_friendly_name() for x in self.selected.surface.shadows.sphere_shadows.occluders])
            if isinstance(self.selected, StellarBody):
                if self.selected.scene_anchor.scene_scale_factor is not None:
                    print("Scene")
                    print("\tPosition", self.selected.scene_anchor.scene_position, '(Offset:', self.selected.scene_anchor.world_body_center_offset, ')')
                    print("\tScale", self.selected.scene_anchor.scene_scale_factor)
                    print("\tZ distance", self.selected.anchor.z_distance)
                if self.selected.surface is not None and self.selected.surface.instance is not None:
                    print("Instance")
                    print("\tPosition", self.selected.surface.instance.get_pos())
                    print("\tDistance", self.selected.surface.instance.get_pos().length())
                    print("\tScale", self.selected.surface.get_scale() * self.selected.scene_anchor.scene_scale_factor)
                    print("\tInstance Ready:", self.selected.surface.instance_ready)
                    if self.selected.atmosphere is not None:
                        pass#print("\tAtm size", self.selected.atmosphere.get_pixel_height())
                    if self.selected.surface.shape.patchable:
                        print("Patches:", len(self.selected.surface.shape.patches))
                else:
                    print("\tPoint")
                projection = self.selected.cartesian_to_spherical(self.observer.get_local_position())
                xy = self.selected.spherical_to_xy(projection)
                print("\tLongLat:", projection[0] * 180 / pi, projection[1] * 180 / pi, projection[2], "XY:", xy[0], xy[1])
                height = self.selected.anchor._height_under
                print("\tHeight:", height, "Delta:", height - self.selected.get_apparent_radius(), "Alt:", (self.selected.anchor.distance_to_obs - height))
                if self.selected.surface is not None and self.selected.surface.shape.patchable:
                    x = projection[0] / pi / 2 + 0.5
                    y = 1.0 - (projection[1] / pi + 0.5)
                    coord = self.selected.surface .global_to_shape_coord(x, y)
                    patch = self.selected.surface.shape.find_patch_at(coord)
                    if patch is not None:
                        print("\tID:", patch.str_id())
                        print("\tLOD:", patch.lod)
                        print("\tView:", patch.quadtree_node.patch_in_view)
                        print("\tLength:", patch.quadtree_node.length, "App:", patch.quadtree_node.apparent_size)
                        print("\tCoord:", coord, "Distance:", patch.quadtree_node.distance)
                        print("\tflat:", patch.flat_coord)
                        if patch.instance is not None:
                            print("\tPosition:", patch.instance.get_pos(), patch.instance.get_pos(self.engine.render))
                            print("\tDistance:", patch.instance.get_pos(self.engine.render).length())
                            print("\tScale:", patch.instance.get_scale())
                            if patch.quadtree_node.offset is not None:
                                print("\tOffset:", patch.quadtree_node.offset, patch.quadtree_node.offset * self.selected.get_apparent_radius())
            else:
                if self.selected.scene_anchor.scene_scale_factor is not None:
                    print("Scene:")
                    print("\tPosition:", self.selected.scene_anchor.scene_position)
                    print("\tOrientation:", self.selected.scene_anchor.scene_orientation)
                    print("\tScale:", self.selected.scene_anchor.scene_scale_factor)
