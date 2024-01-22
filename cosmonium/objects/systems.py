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


from .stellarobject import StellarObject

from ..catalogs import ObjectsDB, objectsDB
from ..engine.anchors import SystemAnchor, OctreeAnchor


class ReferencePoint(StellarObject):
    virtual_object = True


class StellarSystem(StellarObject):
    anchor_class = SystemAnchor.System
    virtual_object = True
    support_offset_body_center = False

    def __init__(self, names, source_names, orbit=None, rotation=None, frame=None, body_class=None, point_color=None, description=''):
        StellarObject.__init__(self, names, source_names, orbit, rotation, frame, body_class, point_color, description)
        self.children = []
        self.children_map = ObjectsDB()
        #Not used by StellarSystem, but used to detect SimpleSystem
        self.primary = None
        self.has_halo = False

    def create_anchor(self, anchor_class, orbit, rotation, frame, point_color):
        return SystemAnchor(self, orbit, rotation, point_color)

    def is_system(self):
        return True

    def get_or_create_system(self):
        return self

    def check_settings(self):
        StellarObject.check_settings(self)
        for child in self.children:
            if child.orbit_object is not None:
                child.orbit_object.check_settings()

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
        #TODO: This is a quick workaround until stars of a system are properly managed
        if child.is_emissive():
            self.has_halo = True

    add_child_star_fast = add_child_fast

    def add_child(self, child):
        self.add_child_fast(child)

    def remove_child_fast(self, child):
        #print("Remove child", child.get_name(), "from", self.get_name())
        self.children.remove(child)
        child.set_parent(None)
        self.children_map.remove(child)
        self.anchor.remove_child(child.anchor)

    def remove_child(self, child):
        self.remove_child_fast(child)

    def on_resolved(self, scene_manager):
        StellarObject.on_resolved(self, scene_manager)
        for child in self.children:
            child.create_orbit_object()

    def on_point(self, scene_manager):
        StellarObject.on_point(self, scene_manager)
        for child in self.children:
            child.remove_orbit_object()

    def get_bounding_radius(self):
        return self.anchor.get_bounding_radius()

    def check_visibility(self, frustum, pixel_size):
        StellarObject.check_visibility(self, frustum, pixel_size)
        if not self.anchor.resolved: return
        for child in self.children:
            if child.orbit_object is not None:
                child.orbit_object.check_visibility(frustum, pixel_size)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        StellarObject.check_and_update_instance(self, scene_manager, camera_pos, camera_rot)
        for child in self.children:
            if child.orbit_object is not None:
                child.orbit_object.check_and_update_instance(scene_manager, camera_pos, camera_rot)
                if child.orbit_object.instance is not None:
                    scene_manager.add_spread_object(child.orbit_object.instance)

class OctreeSystem(StellarSystem):
    def __init__(self, names, source_names, orbit=None, rotation=None, frame=None, body_class=None, radius=None, point_color=None, description=''):
        self.radius = radius
        StellarSystem.__init__(self, names, source_names, orbit, rotation, frame, body_class, point_color, description)

    def create_anchor(self, anchor_class, orbit, rotation, frame, point_color):
        return OctreeAnchor(self, orbit, rotation, self.radius, point_color)

    def dumpOctree(self):
        self.anchor.dump_octree()

    def log_octree(self):
        self.dump_octree = True

    def dumpOctreeStats(self):
        self.dump_octree_stats = not self.dump_octree_stats

    def rebuild(self):
        self.anchor.rebuild()

class SimpleSystem(StellarSystem):
    def __init__(self, names, source_names, primary=None, star_system=False, orbit=None, rotation=None, frame=None, body_class='system', point_color=None, description=''):
        StellarSystem.__init__(self, names, source_names, orbit, rotation, frame, body_class, point_color, description)
        self.star_system = star_system
        self.set_primary(primary)

    def set_primary(self, primary):
        if self.primary is not None:
            self.primary.set_system(None)
            self.primary = None
        if primary is not None:
            self.primary = primary
            self.anchor.set_primary(primary.anchor)
            primary.set_system(self)
            self.body_class = primary.body_class
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

    def get_label_text(self):
        return self.primary.get_label_text()

    def get_components(self):
        return self.primary.get_components()

    def start_shadows_update(self):
        self.primary.start_shadows_update()

    def end_shadows_update(self):
        self.primary.end_shadows_update()

    def add_shadow_target(self, target):
        self.primary.add_shadow_target(target)

class Barycenter(StellarSystem):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('body_class', 'star')
        StellarSystem.__init__(self, *args, **kwargs)
        self.has_halo = True

    def is_emissive(self):
        return True
