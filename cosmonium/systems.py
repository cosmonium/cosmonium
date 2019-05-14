from __future__ import print_function
from __future__ import absolute_import

from .bodies import StellarObject, StellarBodyLabel, Star
from .catalogs import ObjectsDB, objectsDB
from .astro.astro import lum_to_abs_mag, abs_mag_to_lum

class StellarSystem(StellarObject):
    virtual_object = True

    def __init__(self, names, orbit=None, rotation=None, body_class=None, point_color=None, description=''):
        StellarObject.__init__(self, names, orbit, rotation, body_class, point_color, description)
        self.children = []
        self.children_map = ObjectsDB()
        #Not used by StellarSystem, but used to detect SimpleSystem
        self.primary = None
        self.extend = 0.0
        self.has_halo = False

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

    def find_by_path(self, path, return_system=False, first=True):
        if not isinstance(path, list):
            path=path.split('/')
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
                if child.distance_to_obs is not None and (distance is None or child.distance_to_obs - child.get_apparent_radius() < distance):
                    distance = child.distance_to_obs - child.get_apparent_radius()
                    body = child
        return (distance, body)

    def find_nth_child(self, index):
        if index < len(self.children):
            return self.children[index]
        else:
            return None

    def add_child_fast(self, child):
        if child.parent is not None:
            child.parent.remove_child_fast(child)
        self.children_map.add(child)
        #print("Add child", child.get_name(), "to", self.get_name())
        self.children.append(child)
        child.set_parent(self)
        #TODO: Temporary workaround until multiple stars are supported
        if isinstance(child, Star):
            self.star = child
            self.has_halo = True
        elif self.star is not None:
            child.set_star(self.star)

    def add_child(self, child):
        old_parent = child.parent
        self.add_child_fast(child)
        if old_parent is not None:
            old_parent.recalc_extend()
        if child.orbit is not None:
            orbit_size = child.orbit.get_apparent_radius()
            if orbit_size > self.extend:
                self.extend = orbit_size
        #TODO: Calc consolidated abs magnitude here

    def remove_child_fast(self, child):
        #print("Remove child", child.get_name(), "from", self.get_name())
        self.children.remove(child)
        child.set_parent(None)
        child.set_star(None)
        self.children_map.remove(child)

    def remove_child(self, child):
        self.remove_child_fast(child)
        self.recalc_extend()

    def recalc_extend(self):
        extend = 0.0
        for child in self.children:
            size = child.get_extend()
            if child.orbit is not None:
                size += child.orbit.get_apparent_radius()
            if size > extend:
                extend = size
        self.extend = extend

    def recalc_recursive(self):
        for child in self.children:
            if isinstance(child, StellarSystem):
                child.recalc_recursive()
        self.recalc_extend()

    def set_star(self, star):
        StellarObject.set_star(self, star)
        for child in self.children:
            child.set_star(star)

    def update(self, time):
        StellarObject.update(self, time)
        for child in self.children:
            child.update(time)

    def update_obs(self, camera_pos):
        StellarObject.update_obs(self, camera_pos)
        #No need to check the children if not visible
        if not self.visible or not self.resolved: return
        for child in self.children:
            child.update_obs(camera_pos)

    def check_visibility(self, pixel_size):
        self.was_visible = self.visible and self.resolved
        StellarObject.check_visibility(self, pixel_size)
        #No need to check the children if not visible
        if (not self.visible or not self.resolved) and not self.was_visible: return
        for child in self.children:
            child.check_visibility(pixel_size)

    def check_settings(self):
        StellarObject.check_settings(self)
        #TODO: Propagate even if not visible ?
        for child in self.children:
            child.check_settings()

    def check_and_update_instance(self, camera_pos, orientation, pointset):
        StellarObject.check_and_update_instance(self, camera_pos, orientation, pointset)
        #No need to check the children if not visible
        if (not self.visible or not self.resolved) and not self.was_visible: return
        for child in self.children:
            child.check_and_update_instance(camera_pos, orientation, pointset)

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
        return self.extend

class SimpleSystem(StellarSystem):
    label_class = StellarBodyLabel
    def __init__(self, names, primary=None, orbit=None, rotation=None, body_class='system', point_color=None, description=''):
        StellarSystem.__init__(self, names, orbit, rotation, body_class, point_color, description)
        self.set_primary(primary)

    def set_primary(self, primary):
        if self.primary is not None:
            self.primary.set_system(None)
            self.primary = None
        if primary is not None:
            self.primary = primary
            primary.set_system(self)
            self.body_class = primary.body_class
            self.abs_magnitude = self.primary.get_abs_magnitude()
            self.point_color = primary.point_color

    def add_child(self, child):
        StellarSystem.add_child(self, child)
        if self.primary is None and len(self.children) == 1:
            self.set_primary(child)

    def add_child_fast(self, child):
        StellarSystem.add_child_fast(self, child)
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
        return self.primary.get_name()

    def get_abs_magnitude(self):
        return self.primary.get_abs_magnitude()

class Barycenter(StellarSystem):
    label_class = StellarBodyLabel
    has_halo = True
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('body_class', 'star')
        StellarSystem.__init__(self, *args, **kwargs)
        self.abs_magnitude = None

    def is_emissive(self):
        return True

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
