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


from math import asin, pi

from ..anchors import StellarAnchor


class AnchorTraverser:
    def traverse_anchor(self, anchor):
        pass

    def enter_system(self, anchor):
        return False

    def traverse_system(self, anchor):
        pass

    def enter_octree_node(self, anchor):
        return False

    def traverse_octree_node(self, anchor):
        pass


class UpdateTraverser(AnchorTraverser):
    def __init__(self, time, observer, lowest_radiance, update_id):
        self.time = time
        self.observer = observer
        self.lowest_radiance = lowest_radiance
        self.update_id = update_id
        self.visibles = []

    def get_collected(self):
        return self.visibles

    def traverse_anchor(self, anchor):
        #if anchor.update_id == self.update_id: return
        anchor.update_all(self.time, self.observer, self.update_id)
        anchor.update_id = self.update_id
        if anchor.visible or anchor.visibility_override:
            self.visibles.append(anchor)

    def enter_system(self, anchor):
        self.traverse_anchor(anchor)
        return ((anchor.visible or anchor.visibility_override) and anchor.resolved) or anchor.force_update

    def traverse_system(self, anchor):
        for child in anchor.children:
            child.traverse(self)

    def enter_octree_node(self, octree_node):
        #TODO: Octree root must be separate from octree node. Use enter_system ?
        frustum = self.observer.frustum
        distance = (octree_node.center - frustum.get_position()).length() - octree_node.radius
        if distance <= 0.0:
            return True
        point_radiance = octree_node.max_luminosity / (4 * pi * distance * distance * 1000 * 1000)
        if point_radiance < self.lowest_radiance:
            return False
        return frustum.is_sphere_in(octree_node.center, octree_node.radius)

    def traverse_octree_node(self, octree_node):
        frustum = self.observer.frustum
        frustum_position = frustum.get_position()
        distance = (octree_node.center - frustum_position).length() - octree_node.radius
        if distance > 0.0:
            lowest_luminosity = 4 * pi * distance * 1000 * 1000 * self.lowest_radiance
        else:
            lowest_luminosity = 0.0
        for leaf in octree_node.leaves:
            traverse = False
            if leaf._intrinsic_luminosity > lowest_luminosity:
                distance = (leaf._global_position - frustum_position).length()
                if distance > 0.0:
                    point_radiance = leaf._intrinsic_luminosity / (4 * pi * distance * distance * 1000 * 1000)
                    if point_radiance > self.lowest_radiance:
                        traverse = frustum.is_sphere_in(leaf._global_position, leaf.bounding_radius)
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
            if distance < self.distance:
                self.distance = distance
                self.closest_system = leaf


class FindLightSourceTraverser(AnchorTraverser):
    def __init__(self, lowest_radiance, position):
        self.lowest_radiance = lowest_radiance
        self.position = position
        self.anchors = []

    def get_collected(self):
        return self.anchors

    def traverse_anchor(self, anchor):
        self.anchors.append(anchor)

    def enter_system(self, anchor):
        #TODO: Is global position accurate enough ?
        global_delta = anchor._global_position - self.position
        if anchor.content & StellarAnchor.Emissive != 0:
            distance = (global_delta).length()
            if distance > 0:
                point_radiance = anchor._intrinsic_luminosity / (4 * pi * distance * distance * 1000 * 1000)
                return point_radiance > self.lowest_radiance
            else:
                return True
        else:
            return False


    def traverse_system(self, anchor):
        for child in anchor.children:
            if child.content & StellarAnchor.Emissive == 0: continue
            #TODO: Is global position accurate enough ?
            global_delta = child._global_position - self.position
            distance = (global_delta).length()
            if distance > 0:
                point_radiance = child._intrinsic_luminosity / (4 * pi * distance * distance * 1000 * 1000)
                if point_radiance > self.lowest_radiance:
                    child.traverse(self)
            else:
                child.traverse(self)


    def enter_octree_node(self, octree_node):
        #TODO: Check node content ?
        distance = (octree_node.center - self.position).length() - octree_node.radius
        if distance <= 0.0:
            return True
        point_radiance = octree_node.max_luminosity / (4 * pi * distance * distance * 1000 * 1000)
        if point_radiance < self.lowest_radiance:
            return False
        return True


    def traverse_octree_node(self, octree_node):
        distance = (octree_node.center - self.position).length() - octree_node.radius
        if distance > 0.0:
            lowest_luminosity = 4 * pi * distance * 1000 * 1000 * self.lowest_radiance
        else:
            lowest_luminosity = 0.0
        for leaf in octree_node.leaves:
            if leaf._intrinsic_luminosity > lowest_luminosity:
                distance = (leaf._global_position - self.position).length()
                if distance > 0.0:
                    point_radiance = leaf._intrinsic_luminosity / (4 * pi * distance * distance * 1000 * 1000)
                    if point_radiance > self.lowest_radiance:
                        leaf.traverse(self)
                else:
                    leaf.traverse(self)


class FindShadowCastersTraverser(AnchorTraverser):
    def __init__(self, target, vector_to_light_source, distance_to_light_source, light_source_radius):
        self.target = target
        self.body_position = target._local_position
        self.body_bounding_radius = target.bounding_radius
        self.vector_to_light_source = vector_to_light_source
        self.distance_to_light_source = distance_to_light_source
        self.light_source_angular_radius = asin(light_source_radius / (distance_to_light_source - self.body_bounding_radius))
        self.anchors = []
        self.parent_systems = []
        parent = target.parent
        while parent is not None and parent.content != ~0:
            self.parent_systems.append(parent)
            parent = parent.parent

    def get_collected(self):
        return self.anchors


    def check_cast_shadow(self, occluder):
        cast_shadow = False
        occluder_position = occluder._local_position
        occluder_bounding_radius = occluder.bounding_radius
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
        if anchor != self.target and anchor.content & StellarAnchor.Reflective != 0 and self.check_cast_shadow(anchor):
            self.anchors.append(anchor)

    def enter_system(self, anchor):
        enter = anchor in self.parent_systems or (anchor.content & StellarAnchor.Reflective != 0 and self.check_cast_shadow(anchor))
        #TODO: We should trigger update here if needed (using update_id) instead of deferring update to next frame
        anchor.force_update = enter
        return enter

    def traverse_system(self, anchor):
        for child in anchor.children:
            child.traverse(self)
