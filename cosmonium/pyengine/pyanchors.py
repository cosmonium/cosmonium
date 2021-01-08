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

from panda3d.core import LPoint3d, LQuaterniond, LColor

from ..foundation import BaseObject
from ..octree import OctreeNode
from ..astro import units
from ..astro.astro import abs_to_app_mag, app_to_abs_mag, abs_mag_to_lum, lum_to_abs_mag

from .. import settings

from math import sqrt, asin, pi
from time import time

class AnchorBase():
    Emissive   = 1
    Reflective = 2
    System     = 4
    def __init__(self, anchor_class, body, point_color):
        self.content = anchor_class
        self.body = body
        #TODO: To remove
        if point_color is None:
            point_color = LColor(1.0, 1.0, 1.0, 1.0)
        self.point_color = point_color
        self.parent = None
        self.rebuild_needed = False
        #Flags
        self.visible = False
        self.visibility_override = False
        self.resolved = False
        self.update_id = 0
        self.update_frozen = False
        self.force_update = False
        #Cached values
        self._position = LPoint3d()
        self._global_position = LPoint3d()
        self._local_position = LPoint3d()
        self._orientation = LQuaterniond()
        self._equatorial = LQuaterniond()
        self._abs_magnitude = None
        self._app_magnitude = None
        self._extend = 0.0
        self._albedo = 0.5
        #Scene parameters
        self.rel_position = None
        self.distance_to_obs = None
        self.vector_to_obs = None
        self.distance_to_star = None
        self.vector_to_star = None
        self.visible_size = 0.0
        self.scene_position = None
        self.scene_orientation = None
        self.scene_scale_factor = None

    def set_rebuild_needed(self):
        self.rebuild_needed = True
        if self.parent is not None:
            self.parent.set_rebuild_needed()

    def rebuild(self):
        pass

    def traverse(self, visitor):
        visitor.traverse_anchor(self)

    def get_global_position(self):
        return self._global_position

    def get_abs_magnitude(self):
        return self._abs_magnitude

    def calc_global_distance_to(self, position):
        direction = self.get_position() - position
        length = direction.length()
        return (direction / length, length)

    def calc_local_distance_to(self, position):
        direction = position - self._local_position
        length = direction.length()
        return (direction / length, length)

    def update(self, time):
        pass

    def update_observer(self, observer):
        pass

    def update_and_update_observer(self, time, observer):
        self.update(time)
        self.update_observer(observer)

    def update_app_magnitude(self):
        pass

    def update_scene(self):
        pass

class CartesianAnchor(AnchorBase):
    pass

class StellarAnchor(AnchorBase):
    def __init__(self, anchor_class, body, orbit, rotation, point_color):
        AnchorBase.__init__(self, anchor_class, body, point_color)
        self.orbit = orbit
        self.rotation = rotation
        #TODO: Should be done properly
        orbit.body = body
        rotation.body = body
        self.star = None

    def update(self, time):
        self._orientation = self.rotation.get_rotation_at(time)
        self._equatorial = self.rotation.get_equatorial_orientation_at(time)
        self._local_position = self.orbit.get_position_at(time)
        self._global_position = self.orbit.get_global_position_at(time)
        self._position = self._global_position + self._local_position
        if self.star is not None:
            (self.vector_to_star, self.distance_to_star) = self.calc_local_distance_to(self.star.get_local_position())

    def update_observer(self, observer):
        global_delta = self._global_position - observer._global_position
        local_delta = self._local_position - observer._local_position
        rel_position = global_delta + local_delta
        distance_to_obs = rel_position.length()
        vector_to_obs = -rel_position / distance_to_obs
        if distance_to_obs > 0.0:
            visible_size = self._extend / (distance_to_obs * observer.pixel_size)
        else:
            visible_size = 0.0
        radius = self._extend
        if self.visibility_override:
            resolved = visible_size > settings.min_body_size
            visible = True
        elif distance_to_obs > radius:
            in_view = observer.rel_frustum.is_sphere_in(rel_position, radius)
            resolved = visible_size > settings.min_body_size
            visible = in_view# and (visible_size > 1.0 or self._app_magnitude < settings.lowest_app_magnitude)
        else:
            #We are in the object
            resolved = True
            visible = True
        if resolved:
            self._height_under = self.body.get_height_under(observer._local_position)
        else:
            self._height_under = self.body.get_apparent_radius()
        self.rel_position = rel_position
        self.vector_to_obs = vector_to_obs
        self.distance_to_obs = distance_to_obs
        self.visible = visible
        self.resolved = resolved
        self.visible_size = visible_size

    def get_luminosity(self, star):
        vector_to_star = (star._local_position - self._local_position)
        distance_to_star = vector_to_star.length()
        vector_to_star /= distance_to_star
        star_power = abs_mag_to_lum(star._abs_magnitude)
        area = 4 * pi * distance_to_star * distance_to_star * 1000 * 1000 # Units are in km
        if area > 0.0:
            irradiance = star_power / area
            surface = pi * self._extend * self._extend * 1000 * 1000 # Units are in km
            received_energy = irradiance * surface
            reflected_energy = received_energy * self._albedo
            phase_angle = self.vector_to_obs.dot(self.vector_to_star)
            fraction = (1.0 + phase_angle) / 2.0
            return reflected_energy * fraction
        else:
            print("No area", self.body.get_name())
            return 0.0

    def update_app_magnitude(self, star):
        #TODO: Should be done by inheritance ?
        if self.distance_to_obs == 0:
            self._app_magnitude = 99.0
            return
        if self.content & self.Emissive != 0:
            self._app_magnitude = abs_to_app_mag(self._abs_magnitude, self.distance_to_obs)
        elif self.content & self.Reflective != 0:
            if star is not None:
                reflected = self.get_luminosity(star)
                self._app_magnitude = abs_to_app_mag(lum_to_abs_mag(reflected), self.distance_to_obs)
            else:
                self._app_magnitude = 99.0
        else:
            self._app_magnitude = abs_to_app_mag(self._abs_magnitude, self.distance_to_obs)
        if not self.visibility_override:
            self.visible = self.visible_size > 1.0 or self._app_magnitude < settings.lowest_app_magnitude

    def update_scene(self):
        if self.body.support_offset_body_center and self.visible and self.resolved and settings.offset_body_center:
            self.scene_rel_position = self.rel_position + self.vector_to_obs * self._height_under
            distance_to_obs = self.distance_to_obs - self._height_under
        else:
            self.scene_rel_position = self.rel_position
            distance_to_obs = self.distance_to_obs
        self.scene_position, self.scene_distance, self.scene_scale_factor = BaseObject.calc_scene_params(self.scene_rel_position, self._position, distance_to_obs, self.vector_to_obs)
        self.scene_orientation = self._orientation

class FixedStellarAnchor(StellarAnchor):
    def __init__(self, body, orbit, rotation, point_color):
        StellarAnchor.__init__(self, body, orbit, rotation, point_color)
        #self.update_frozen = True
        #self.update(0)

class DynamicStellarAnchor(StellarAnchor):
    pass

class SystemAnchor(DynamicStellarAnchor):
    def __init__(self, body, orbit, rotation, point_color):
        DynamicStellarAnchor.__init__(self, self.System, body, orbit, rotation, point_color)
        self.children = []

    def add_child(self, child):
        self.children.append(child)
        child.parent = self
        if not self.rebuild_needed:
            self.set_rebuild_needed()

    def remove_child(self, child):
        try:
            self.children.remove(child)
            child.parent = None
        except ValueError:
            pass
        self.set_rebuild_needed()

    def rebuild(self):
        self.content = self.System
        for child in self.children:
            if child.rebuild_needed:
                child.rebuild()
            self.content |= child.content
        self.rebuild_needed = False

    def traverse(self, visitor):
        if visitor.enter_system(self):
            visitor.traverse_system(self)

class OctreeAnchor(SystemAnchor):
    def __init__(self, body, orbit, rotation, point_color):
        SystemAnchor.__init__(self, body, orbit, rotation, point_color)
        #TODO: Turn this into a parameter or infer it from the children
        self.octree_width = 100000.0 * units.Ly
        #TODO: Should be configurable
        abs_mag = app_to_abs_mag(6.0, self.octree_width * sqrt(3))
        #TODO: position should be extracted from orbit
        self.octree = OctreeNode(0,
                             LPoint3d(10 * units.Ly, 10 * units.Ly, 10 * units.Ly),
                             self.octree_width,
                             abs_mag)
        #TODO: Right now an octree contains anything
        self.content = ~1

    def rebuild(self):
        #TODO: We should not iter over all the children
        SystemAnchor.rebuild(self)
        #TODO: This is a crude way to detect octree
        self.content = ~1
        #TODO: Must add condition to rebuild the octree
        self.create_octree()

    def traverse(self, visitor):
        if visitor.enter_octree_node(self.octree):
            self.octree.traverse_new(visitor)

    def create_octree(self):
        print("Creating octree...")
        start = time()
        for child in self.children:
            #TODO: this should be done properly at anchor creation
            child.update(0)
            self.octree.add(child)
        end = time()
        print("Creation time:", end - start)
        self.rebuild_needed = False

class UniverseAnchor(OctreeAnchor):
    def __init__(self, body, orbit, rotation, point_color):
        OctreeAnchor.__init__(self, body, orbit, rotation, point_color)
        self.visible = True
        self.resolved = True

    def traverse(self, visitor):
        self.octree.traverse_new(visitor)

class AnchorTraverser:
    def traverse_anchor(self, anchor):
        pass

    def enter_system(self, anchor):
        pass

    def traverse_system(self, anchor):
        pass

    def enter_octree_node(self, anchor):
        pass

    def traverse_octree_node(self, anchor):
        pass

class UpdateTraverser(AnchorTraverser):
    def __init__(self, time, observer, limit):
        self.time = time
        self.observer = observer
        self.limit = limit
        self.visibles = []

    def traverse_anchor(self, anchor):
        anchor.update_and_update_observer(self.time, self.observer)
        if anchor.visible:
            self.visibles.append(anchor)

    def enter_system(self, anchor):
        anchor.update_and_update_observer(self.time, self.observer)
        if anchor.visible:
            self.visibles.append(anchor)
        return (anchor.visible and anchor.resolved) or anchor.force_update

    def traverse_system(self, anchor):
        for child in anchor.children:
            child.traverse(self)

    def enter_octree_node(self, octree_node):
        #TODO: Octree root must be separate from octree node. Use enter_system ?
        frustum = self.observer.frustum
        distance = (octree_node.center - frustum.get_position()).length() - octree_node.radius
        if distance <= 0.0:
            return True
        if abs_to_app_mag(octree_node.max_magnitude, distance) > self.limit:
            return False
        return frustum.is_sphere_in(octree_node.center, octree_node.radius)

    def traverse_octree_node(self, octree_node):
        frustum = self.observer.frustum
        frustum_position = frustum.get_position()
        distance = (octree_node.center - frustum_position).length() - octree_node.radius
        if distance > 0.0:
            faintest = app_to_abs_mag(self.limit, distance)
        else:
            faintest = 99.0
        for leaf in octree_node.leaves:
            abs_magnitude = leaf._abs_magnitude
            traverse = False
            if abs_magnitude < faintest:
                direction = leaf._global_position - frustum_position
                distance = direction.length()
                if distance > 0.0:
                    app_magnitude = abs_to_app_mag(abs_magnitude, distance)
                    if app_magnitude < self.limit:
                        traverse = frustum.is_sphere_in(leaf._global_position, leaf._extend)
                else:
                    traverse = True
            if traverse:
                leaf.traverse(self)

class FindClosestSystemTraverser(AnchorTraverser):
    def __init__(self, observer, system, distance):
        self.observer = observer
        self._global_position = observer._global_position
        self.closest_system = system
        self.distance = distance

    def enter_octree_node(self, octree_node):
        #TODO: Check node content ?
        distance = (octree_node.center - self._global_position).length() - octree_node.radius
        return distance <= self.distance

    def traverse_octree_node(self, octree_node):
        global_position = self.observer._global_position
        local_position = self.observer._local_position
        for leaf in octree_node.leaves:
            global_delta = leaf._global_position - global_position
            local_delta = leaf._local_position - local_position
            distance = (global_delta + local_delta).length()
            if distance <self.distance:
                self.distance = distance
                self.closest_system = leaf.body

class FindLightSourceTraverser(AnchorTraverser):
    def __init__(self, limit, position):
        self.limit = limit
        self.position = position
        self.anchors = []

    def traverse_anchor(self, anchor):
        self.anchors.append(anchor)

    def enter_system(self, anchor):
        #TODO: Is global position accurate enough ?
        global_delta = anchor._global_position - self.position
        distance = (global_delta).length()
        return anchor.content & AnchorBase.Emissive != 0 and (distance == 0 or abs_to_app_mag(anchor._abs_magnitude, distance) < self.limit)

    def traverse_system(self, anchor):
        for child in anchor.children:
            if child.content & AnchorBase.Emissive == 0: continue
            #TODO: Is global position accurate enough ?
            global_delta = child._global_position - self.position
            distance = (global_delta).length()
            if distance == 0 or abs_to_app_mag(child._abs_magnitude, distance) < self.limit:
                child.traverse(self)

    def enter_octree_node(self, octree_node):
        #TODO: Check node content ?
        distance = (octree_node.center - self.position).length() - octree_node.radius
        if distance <= 0.0:
            return True
        if abs_to_app_mag(octree_node.max_magnitude, distance) > self.limit:
            return False
        return True

    def traverse_octree_node(self, octree_node):
        distance = (octree_node.center - self.position).length() - octree_node.radius
        if distance > 0.0:
            faintest = app_to_abs_mag(self.limit, distance)
        else:
            faintest = 99.0
        for leaf in octree_node.leaves:
            abs_magnitude = leaf._abs_magnitude
            if abs_magnitude < faintest:
                distance = (leaf._global_position - self.position).length()
                if distance > 0.0:
                    app_magnitude = abs_to_app_mag(abs_magnitude, distance)
                    if app_magnitude < self.limit:
                        leaf.traverse(self)
                else:
                    leaf.traverse(self)

class FindObjectsInVisibleResolvedSystemsTraverser(AnchorTraverser):
    def __init__(self):
        self.anchors = []

    def traverse_anchor(self, anchor):
        self.anchors.append(anchor)

    def enter_system(self, anchor):
        self.anchors.append(anchor)
        return anchor.visible and anchor.resolved

    def traverse_system(self, anchor):
        for child in anchor.children:
            child.traverse(self)

class FindShadowCastersTraverser(AnchorTraverser):
    def __init__(self, target, vector_to_light_source, distance_to_light_source, light_source_radius):
        self.target = target
        self.body_position = target._local_position
        self.body_bounding_radius = target._extend
        self.vector_to_light_source = vector_to_light_source
        self.distance_to_light_source = distance_to_light_source
        self.light_source_angular_radius = asin(light_source_radius / (distance_to_light_source - self.body_bounding_radius))
        self.anchors = []
        self.parent_systems = []
        parent = target.parent
        while parent.content != ~1:
            self.parent_systems.append(parent)
            parent = parent.parent

    def check_cast_shadow(self, occluder):
        cast_shadow = False
        occluder_position = occluder._local_position
        occluder_bounding_radius = occluder._extend
        relative_position = occluder_position - self.body_position
        t = self.vector_to_light_source.dot(relative_position)
        #print(occluder.body.get_name(), t)
        if t >= 0 and t <= self.distance_to_light_source:
            distance = relative_position.length() - self.body_bounding_radius
            occluder_angular_radius = asin(occluder_bounding_radius / distance) if occluder_bounding_radius < distance else pi / 2
            ar_ratio = occluder_angular_radius / self.light_source_angular_radius
            #print(occluder.body.get_name(), "D", distance, "AR", occluder_angular_radius, "R", ar_ratio)
            #TODO: No longer valid if we are using HDR
            #If the shadow coef is smaller than the min change in pixel color
            #the umbra will have no visible impact
            if ar_ratio * ar_ratio > 1.0 / 255:
                distance_to_projection = (relative_position - self.vector_to_light_source * t).length()
                penumbra_radius = (1 + ar_ratio) * occluder_bounding_radius
                #TODO: Should check also the visible size of the penumbra
                if distance_to_projection < penumbra_radius + self.body_bounding_radius:
                    #print(occluder.body.get_name(), "casts shadows on", self.target.body.get_name())
                    cast_shadow = True
        return cast_shadow

    def traverse_anchor(self, anchor):
        if anchor != self.target and anchor.content & AnchorBase.Reflective != 0 and self.check_cast_shadow(anchor):
            self.anchors.append(anchor)

    def enter_system(self, anchor):
        enter = anchor in self.parent_systems or (anchor.content & AnchorBase.Reflective != 0 and self.check_cast_shadow(anchor))
        #TODO: We should trigger update here if needed (using update_id) instead of deferring update to next frame
        anchor.force_update = enter
        return enter

    def traverse_system(self, anchor):
        for child in anchor.children:
            child.traverse(self)
