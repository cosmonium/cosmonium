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

from panda3d.core import LPoint3d, LColor

from .stellarobject import StellarObject
from .catalogs import ObjectsDB, objectsDB
from .astro.astro import lum_to_abs_mag, abs_mag_to_lum, app_to_abs_mag
from .foundation import CompositeObject
from .octree import OctreeNode, OctreeLeaf, VisibleObjectsTraverser, hasOctreeLeaf
from .anchors import SystemAnchor
from .pstats import pstat
from .astro import units

from . import settings

from math import sqrt
from time import time

class StellarSystem(StellarObject):
    anchor_class = SystemAnchor.System
    virtual_object = True
    support_offset_body_center = False

    def __init__(self, names, source_names, orbit=None, rotation=None, body_class=None, point_color=None, description=''):
        StellarObject.__init__(self, names, source_names, orbit, rotation, body_class, point_color, description)
        self.children = []
        self.children_map = ObjectsDB()
        #Not used by StellarSystem, but used to detect SimpleSystem
        self.primary = None
        self.has_halo = False
        self.was_visible = False
        self.abs_magnitude = None

    def create_anchor(self, anchor_class, orbit, rotation, point_color):
        return SystemAnchor(anchor_class, self, orbit, rotation, point_color)

    def is_system(self):
        return True

    def apply_func(self, func):
        StellarObject.apply_func(self, func)
        for child in self.children:
            child.apply_func(func)

    def find_by_name(self, name, name_up=None):
        if name_up is None:
            name_up=name.upper()
        if self.is_named(name, name_up):
            return self
        else:
            for child in self.children:
                found = child.find_by_name(name, name_up)
                if found is not None:
                    return found
            return None

    def find_child_by_name(self, name, return_system=False):
        child = self.children_map.get(name)
        if child is not None:
            return child
        for child in self.children:
            if child.is_named(name):
                return child
            elif isinstance(child, SimpleSystem) and child.primary != None and child.primary.is_named(name):
                if return_system:
                    return child
                else:
                    return child.primary
        return None

    def find_by_path(self, path, return_system=False, first=True, separator='/'):
        if not isinstance(path, list):
            path=path.split(separator)
        if len(path) > 0:
            #print("Looking for", path, "in '" + self.get_name() + "'", "RS:", return_system)
            name = path[0]
            sub_path = path[1:]
            child = None
            if first:
                #TODO: should be done in Universe class, not here...
                child = objectsDB.get(name)
                if child is not None and return_system and not isinstance(child, StellarSystem):
                    child = child.system
            if child is None:
                child = self.find_child_by_name(name, return_system)
            if child is not None:
                if len(sub_path) == 0:
                    if not return_system or isinstance(child, StellarSystem):
                        #print("Found child", child.get_name())
                        return child
                else:
                    if isinstance(child, StellarSystem):
                        #print("Found child, rec into", child.get_name())
                        return child.find_by_path(sub_path, return_system, first=False)
                    elif child.system is not None:
                        #print("Found child, rec into system", child.parent.get_name(), sub_path)
                        return child.system.find_by_path(sub_path, return_system, first=False)
                    else:
                        return None
        return None

    def find_closest(self, distance=None, body=None):
        for child in self.children:
            if isinstance(child, StellarSystem):
                (distance, body) = child.find_closest(distance, body)
            else:
                if child.anchor.distance_to_obs is not None and (distance is None or child.anchor.distance_to_obs - child.anchor._height_under < distance):
                    distance = child.anchor.distance_to_obs - child.anchor._height_under
                    body = child
        return (distance, body)

    def find_nth_child(self, index):
        if index < len(self.children):
            return self.children[index]
        else:
            return None

    def add_child_fast(self, child):
        if child.parent is not None:
            child.parent.anchor.remove_child(child.anchor)
            child.parent.remove_child_fast(child)
        #print("Add child", child.get_name(), "to", self.get_name())
        self.children_map.add(child)
        self.children.append(child)
        self.anchor.add_child(child.anchor)
        child.set_parent(self)
        #TODO: Temporary workaround until multiple stars are supported
        if self.star is not None:
            child.set_star(self.star)

    #TODO: This is a quick workaround until stars of a system are properly managed
    def add_child_star_fast(self, child):
        if child.parent is not None:
            child.parent.anchor.remove_child(child.anchor)
            child.parent.remove_child_fast(child)
        #print("Add child", child.get_name(), "to", self.get_name())
        self.children_map.add(child)
        self.children.append(child)
        self.anchor.add_child(child.anchor)
        child.set_parent(self)
        self.star = child
        self.has_halo = True

    def add_child(self, child):
        old_parent = child.parent
        self.add_child_fast(child)
        if old_parent is not None:
            old_parent.recalc_extend()
        if child.orbit is not None:
            orbit_size = child.orbit.get_apparent_radius()
            if orbit_size > self._extend:
                self._extend = orbit_size
                self.anchor._extend = self._extend
        #TODO: Calc consolidated abs magnitude here

    def remove_child_fast(self, child):
        #print("Remove child", child.get_name(), "from", self.get_name())
        self.children.remove(child)
        child.set_parent(None)
        child.set_star(None)
        self.children_map.remove(child)
        self.anchor.remove_child(child.anchor)

    def remove_child(self, child):
        self.remove_child_fast(child)
        self.recalc_extend()

    def recalc_extend(self):
        extend = 0.0
        for child in self.children:
            size = child.get_extend()
            if child.anchor.orbit is not None:
                size += child.anchor.orbit.get_apparent_radius()
            if size > extend:
                extend = size
        self._extend = extend
        self.anchor._extend = self._extend

    def recalc_recursive(self):
        for child in self.children:
            if isinstance(child, StellarSystem):
                child.recalc_recursive()
        self.recalc_extend()

    def set_star(self, star):
        StellarObject.set_star(self, star)
        for child in self.children:
            child.set_star(star)

    def check_settings(self):
        StellarObject.check_settings(self)
        #No need to check the children if not visible
        if not self.anchor.visible or not self.anchor.resolved: return
        for child in self.children:
            child.check_settings()

    @pstat
    def update_scene_and_render(self, observer, renderer):
        self.anchor.update_scene()
        if not self.anchor.visible or not self.anchor.resolved: return
        for child in self.children:
            child.update_scene_and_render(observer, renderer)

    def update_scene_and_render_children(self, observer, renderer):
        for child in self.children:
            child.update_scene_and_render(observer, renderer)

    def remove_components(self):
        StellarObject.remove_components(self)
        #Not really components, but that's the easiest way to remove the children's instances
        print("Remove children", self.get_name())
        for child in self.children:
            child.remove_instance()

    def remove_instance(self):
        StellarObject.remove_instance(self)
        for child in self.children:
            child.remove_instance()

    def get_extend(self):
        return self._extend

    def get_abs_magnitude(self):
        if self.abs_magnitude is None:
            luminosity = 0.0
            for child in self.children:
                luminosity += abs_mag_to_lum(child.get_abs_magnitude())
            if luminosity > 0.0:
                self.abs_magnitude = lum_to_abs_mag(luminosity)
            else:
                self.abs_magnitude = 99.0
        return self.abs_magnitude

class OctreeSystem(StellarSystem):
    def __init__(self, names, source_names, orbit=None, rotation=None, body_class=None, point_color=None, description=''):
        StellarSystem.__init__(self, names, source_names, orbit, rotation, body_class, point_color, description)
        #TODO: Size and magnitude should not be hardcoded
        self.octree_width = 100000.0 * units.Ly
        abs_mag = app_to_abs_mag(6.0, self.octree_width * sqrt(3))
        #TODO: position should be extracted from orbit
        self.octree = OctreeNode(0,
                             LPoint3d(10 * units.Ly, 10 * units.Ly, 10 * units.Ly),
                             self.octree_width,
                             abs_mag)
        self.update_id = 0
        self.previous_leaves = []
        self.to_update_leaves = []
        self.to_update = []
        self.to_remove = []
        self.nb_cells = 0
        self.nb_leaves = 0
        self.nb_leaves_in_cells = 0
        self.dump_octree = False
        self.dump_octree_stats = False

    def dumpOctree(self):
        self.octree.dump_octree()

    def log_octree(self):
        self.dump_octree = True

    def dumpOctreeStats(self):
        self.dump_octree_stats = not self.dump_octree_stats

    def create_octree(self):
        print("Creating octree...")
        start = time()
        for child in self.children:
            self.octree.add(OctreeLeaf(child, child.get_global_position(), child.get_abs_magnitude(), child.get_extend(), child.anchor.point_color))
        end = time()
        print("Creation time:", end - start)

    @pstat
    def build_octree_cells_list(self, observer, limit):
        self.update_id += 1
        self.previous_leaves = self.to_update
        self.traverser = VisibleObjectsTraverser(observer.frustum, limit, self.update_id)
        self.octree.traverse(self.traverser)
        self.to_update_leaves = self.traverser.get_leaves()
        self.to_remove = []
        if hasOctreeLeaf:
            self.to_update = []
            for leaf in self.to_update_leaves:
                obj = leaf.get_object()
                self.to_update.append(obj)
                obj.update_id = leaf.get_update_id()
        else:
            self.to_update = self.to_update_leaves
        for old in self.previous_leaves:
            if old.update_id != self.update_id:
                self.to_remove.append(old)

    def update_pos_and_visibility(self, observer):
        pixel_size = observer.pixel_size
        camera_global_pos = observer.camera_global_pos
        camera_position = observer._position
        self.traverser.update_pos_and_visibility(camera_global_pos, camera_position, pixel_size, settings.min_body_size)
        if hasOctreeLeaf:
            for leaf in self.to_update_leaves:
                obj = leaf.get_object().anchor
                obj.vector_to_obs = leaf.vector_to_obs
                obj.distance_to_obs = leaf.distance_to_obs
                obj.rel_position = leaf.rel_position
                obj._app_magnitude = leaf.app_magnitude
                obj.visible = leaf.visible
                obj.resolved = leaf.resolved
                obj.visible_size = leaf.visible_size

    def get_nearest_system(self):
        nearest_system = None
        nearest_system_distance = float('inf')
        for leaf in self.to_update:
            if leaf.anchor.distance_to_obs < nearest_system_distance:
                nearest_system = leaf
                nearest_system_distance = leaf.anchor.distance_to_obs
        return nearest_system

    def update_and_update_observer(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        self.build_octree_cells_list(observer, settings.lowest_app_magnitude)
        self.update_pos_and_visibility(observer)
        for leaf in self.to_update:
            if isinstance(leaf.anchor, SystemAnchor) and leaf.anchor.resolved:
                leaf.anchor.update_and_update_observer_children(time, observer, frustum, camera_global_position, camera_local_position, pixel_size)
            elif not leaf.anchor.update_frozen:
                leaf.anchor.update_and_update_observer(time, observer, frustum, camera_global_position, camera_local_position, pixel_size)

    def check_settings(self):
        CompositeObject.check_settings(self)
        for leaf in self.to_update:
            leaf.check_settings()
        for component in self.components:
            component.check_settings()

    def update_scene_and_render(self, observer, renderer):
        self.traverser.update_scene_info(observer.midPlane, settings.scale)
        if hasOctreeLeaf:
            for leaf in self.to_update_leaves:
                obj = leaf.get_object().anchor
                obj.scene_position = leaf.scene_position
                obj.scene_distance = leaf.scene_distance
                obj.scene_scale_factor = leaf.scene_scale_factor
                obj.scene_orientation = leaf.scene_orientation
        for leaf in self.to_update:
            renderer.add_object(leaf)
            if leaf.anchor.resolved:
                leaf.update_scene_and_render_children(observer, renderer)

class SimpleSystem(StellarSystem):
    def __init__(self, names, source_names, primary=None, star_system=False, orbit=None, rotation=None, body_class='system', point_color=None, description=''):
        StellarSystem.__init__(self, names, source_names, orbit, rotation, body_class, point_color, description)
        self.star_system = star_system
        self.set_primary(primary)

    def set_primary(self, primary):
        if self.primary is not None:
            self.primary.set_system(None)
            self.primary = None
        if primary is not None:
            self.primary = primary
            primary.set_system(self)
            self.body_class = primary.body_class
            if not self.star_system:
                self.abs_magnitude = self.primary.get_abs_magnitude()
            self.anchor.point_color = primary.anchor.point_color

    def add_child(self, child):
        StellarSystem.add_child(self, child)
        if self.primary is None and len(self.children) == 1:
            self.set_primary(child)

    def add_child_fast(self, child):
        StellarSystem.add_child_fast(self, child)
        if self.primary is None and len(self.children) == 1:
            self.set_primary(child)

    def add_child_star_fast(self, child):
        StellarSystem.add_child_star_fast(self, child)
        if self.primary is None and len(self.children) == 1:
            self.set_primary(child)

    def remove_child(self, child):
        StellarSystem.remove_child(self, child)
        if child is self.primary:
            self.primary = None

    def remove_child_fast(self, child):
        StellarSystem.remove_child_fast(self, child)
        if child is self.primary:
            self.primary = None

    def is_emissive(self):
        return self.primary.is_emissive()

    def get_equatorial_rotation(self):
        return self.primary.get_equatorial_rotation()

    def get_label_text(self):
        return self.primary.get_label_text()

    def get_abs_magnitude(self):
        if self.star_system:
            return StellarSystem.get_abs_magnitude(self)
        else:
            return self.primary.get_abs_magnitude()

    def get_components(self):
        return self.primary.get_components()

    def check_cast_shadow_on(self, body):
        return self.primary.check_cast_shadow_on(body)

    def start_shadows_update(self):
        self.primary.start_shadows_update()

    def end_shadows_update(self):
        self.primary.end_shadows_update()

    def add_shadow_target(self, target):
        self.primary.add_shadow_target(target)

    @pstat
    def update_and_update_observer(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        if not self.anchor.visible or not self.anchor.resolved:
            StellarSystem.update_and_update_observer(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size)
            self.primary.update_and_update_observer(time, observer, frustum, camera_global_position, camera_local_position, pixel_size)
            return
        primary = self.primary
        for child in self.children:
            child.start_shadows_update()
        StellarSystem.update_and_update_observer(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size)
        if primary is not None and not primary.is_emissive():
            check_primary = primary.anchor.visible and primary.anchor.resolved
            for child in self.children:
                if child == primary: continue
                if child.anchor.visible and child.anchor.resolved:
                    if primary.atmosphere is not None and primary.init_components and (child.anchor._local_position - self.primary.anchor._local_position).length() < primary.atmosphere.radius:
                        primary.atmosphere.add_shape_object(child.surface)
                    if primary.check_cast_shadow_on(child):
                        #print(primary.get_friendly_name(), "casts shadow on", child.get_friendly_name())
                        primary.add_shadow_target(child)
                if check_primary:
                    #TODO: The test should be done on the actual shadow size, not the resolved state of the child
                    if child.check_cast_shadow_on(primary):
                        #print(child.get_friendly_name(), "casts shadow on", primary.get_friendly_name())
                        child.add_shadow_target(primary)
        for child in self.children:
            child.end_shadows_update()

    def update_obs(self, observer):
        StellarSystem.update_obs(self, observer)
        if not self.visible or not self.resolved:
            self.primary.update_obs(observer)

class Barycenter(StellarSystem):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('body_class', 'star')
        StellarSystem.__init__(self, *args, **kwargs)
        self.abs_magnitude = None
        self.has_halo = True

    def is_emissive(self):
        return True
