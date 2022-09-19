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


from __future__ import annotations

from panda3d.core import Camera, NodePath, DisplayRegion, GraphicsOutput
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import GeomNode, DrawMask

from ...pstats import pstat
from ... import settings


class SceneManagerBase:

    def __init__(self):
        self.midPlane = None
        self.scale = 1.0

    def has_regions(self):
        return False

    def get_regions(self):
        raise NotImplementedError()

    def add_pass(self, name: str, target: GraphicsOutput, camera_mask: DrawMask):
        raise NotImplementedError()

    def attach_new_anchor(self, instance):
        raise NotImplementedError()

    def add_spread_object(self, instance):
        raise NotImplementedError()

    def add_background_object(self, instance):
        raise NotImplementedError()

    def init_camera(self, camera_holder, default_camera):
        raise NotImplementedError()

    def set_camera_mask(self, flags):
        raise NotImplementedError()

    def update_scene_and_camera(self, distance_to_nearest, camera_holder):
        raise NotImplementedError()

    def build_scene(self, state, camera_holder, visibles, resolved):
        raise NotImplementedError()

    def pick_scene(self, mpos):
        raise NotImplementedError()

    def ls(self):
        raise NotImplementedError()


class RenderingPass:
    def __init__(self, name: str, target: GraphicsOutput, camera_mask: DrawMask):
        self.name = name
        self.target = target
        self.camera_mask = camera_mask
        self.display_region: DisplayRegion = None
        node = Camera("camera-" + self.name)
        node.set_camera_mask(camera_mask)
        self.camera = NodePath(node)

    def copy(self):
        return RenderingPass(self.name, self.target, self.camera_mask)

    def create(self):
        self.display_region = self.target.make_display_region(0, 1, 0, 1)
        self.display_region.disable_clears()
        self.display_region.set_scissor_enabled(False)
        self.display_region.set_camera(self.camera)
        self.display_region.set_active(True)

    def remove(self):
        self.target.remove_display_region(self.display_region)


class StaticSceneManager(SceneManagerBase):
    def __init__(self, render):
        SceneManagerBase.__init__(self)
        self.camera = None
        self.lens = None
        self.dr = None
        self.inverse_z = settings.use_inverse_z
        self.near_plane = settings.near_plane
        self.infinite_far_plane = settings.infinite_far_plane
        if self.infinite_far_plane and not self.inverse_z:
            self.far_plane = float('inf')
        else:
            self.far_plane = settings.far_plane
        self.infinite_plane = settings.infinite_plane
        self.auto_infinite_plane = settings.auto_infinite_plane
        self.infinity = None
        self.lens_far_limit = settings.lens_far_limit
        self.root = render.attach_new_node('root')

    def set_target(self, target):
        print("Set Scene Manager target", target)
        self.dr = target.make_display_region(0, 1, 0, 1)
        self.dr.disable_clears()
        self.dr.set_scissor_enabled(False)
        self.dr.set_camera(self.camera)
        self.dr.set_active(True)

    def attach_new_anchor(self, instance):
        instance.reparent_to(self.root)

    def add_spread_object(self, instance):
        pass

    def add_background_object(self, instance):
        instance.reparent_to(self.root)

    def init_camera(self, camera_holder, default_camera):
        self.camera = default_camera
        self.lens = camera_holder.lens.make_copy()
        self.camera.node().set_lens(self.lens)
        if self.auto_infinite_plane:
            self.infinity = self.near_plane / self.lens_far_limit / 1000
        else:
            self.infinity = self.infinite_plane
        print("Planes: ", self.near_plane, self.far_plane)
        self.camera.reparent_to(self.root)

    def set_camera_mask(self, flags):
        self.camera.node().set_camera_mask(flags)

    def update_scene_and_camera(self, distance_to_nearest, camera_holder):
        self.lens = camera_holder.lens.make_copy()
        self.camera.node().set_lens(self.lens)
        if self.inverse_z:
            self.lens.set_near_far(self.far_plane, self.near_plane)
        else:
            self.lens.set_near_far(self.near_plane, self.far_plane)
        self.camera.set_pos(camera_holder.camera_np.get_pos())
        self.camera.set_quat(camera_holder.camera_np.get_quat())

    def build_scene(self, state, camera_holder, visibles, resolved):
        self.root.set_state(state.get_state())

    def ls(self):
        self.root.ls()


class DynamicSceneManager(SceneManagerBase):
    def __init__(self, render):
        SceneManagerBase.__init__(self)
        self.rendering_passes: list[RenderingPass] = []
        self.lens = None
        self.near_plane = settings.near_plane
        self.infinite_far_plane = settings.infinite_far_plane
        if self.infinite_far_plane:
            self.far_plane = float('inf')
        else:
            self.far_plane = settings.far_plane
        self.inverse_z = settings.use_inverse_z
        self.infinite_plane = settings.infinite_plane
        self.auto_infinite_plane = settings.auto_infinite_plane
        self.lens_far_limit = settings.lens_far_limit
        self.auto_scale = settings.auto_scale
        self.min_scale= settings.min_scale
        self.max_scale = settings.max_scale
        self.set_frustum = settings.set_frustum
        self.mid_plane_ratio = settings.mid_plane_ratio
        self.infinity = self.infinite_plane
        self.root = render.attach_new_node('root')


    def add_pass(self, name: str, target: GraphicsOutput, camera_mask: DrawMask):
        print("Add pass", name)
        rendering_pass = RenderingPass(name, target, camera_mask)
        rendering_pass.camera.node().set_lens(self.lens)
        rendering_pass.camera.reparent_to(self.root)
        rendering_pass.create()
        self.rendering_passes.append(rendering_pass)

    def pick_scene(self, mpos):
        camera = self.rendering_passes[0].camera
        picker = CollisionTraverser()
        pq = CollisionHandlerQueue()
        picker_node = CollisionNode('mouseRay')
        picker_np = camera.attach_new_node(picker_node)
        picker_node.set_from_collide_mask(CollisionNode.get_default_collide_mask() | GeomNode.get_default_collide_mask())
        picker_ray = CollisionRay()
        picker_node.add_solid(picker_ray)
        picker.add_collider(picker_np, pq)
        #picker.show_collisions(self.root)
        picker_ray.set_from_lens(camera.node(), mpos.get_x(), mpos.get_y())
        picker.traverse(self.root)
        pq.sort_entries()
        picker_np.remove_node()
        return pq

    def attach_new_anchor(self, instance):
        instance.reparent_to(self.root)

    def add_spread_object(self, instance):
        pass

    def add_background_object(self, instance):
        instance.reparent_to(self.root)

    def update_planes(self):
        if self.inverse_z:
            self.lens.set_near_far(self.far_plane, self.near_plane)
        else:
            self.lens.set_near_far(self.near_plane, self.far_plane)

    def init_camera(self, camera_holder, default_camera):
        self.lens = camera_holder.lens.make_copy()
        print("Planes: ", self.near_plane, self.far_plane)
        self.update_planes()

    def update_scene_and_camera(self, distance_to_nearest, camera_holder):
        self.lens = camera_holder.lens.make_copy()
        if self.auto_scale:
            if distance_to_nearest is None:
                self.scale = self.max_scale
            elif distance_to_nearest <= 0:
                self.scale = self.min_scale
            elif distance_to_nearest < self.max_scale * 10:
                self.scale = max(distance_to_nearest / 10, self.min_scale)
            else:
                self.scale = self.max_scale
            if self.set_frustum:
                #near_plane = min(distance_to_nearest / settings.scale / 2.0, settings.near_plane)
                if self.scale < 1.0:
                    self.near_plane = self.scale
                else:
                    self.near_plane = settings.near_plane
        self.update_planes()
        if self.auto_infinite_plane:
            self.infinity = self.near_plane / self.lens_far_limit / 1000
        else:
            self.infinity = self.infinite_plane
        self.midPlane = self.infinity / self.mid_plane_ratio
        for rendering_pass in self.rendering_passes:
            rendering_pass.camera.node().set_lens(self.lens)
            rendering_pass.camera.set_pos(camera_holder.camera_np.get_pos())
            rendering_pass.camera.set_quat(camera_holder.camera_np.get_quat())

    @pstat
    def build_scene(self, state, camera_holder, visibles, resolved):
        self.root.set_state(state.get_state())
        self.root.setShaderInput("midPlane", self.midPlane)

    def ls(self):
        self.root.ls()

class CollisionEntriesCollection:
    def __init__(self):
        self.entries = []

    def add_queue(self, queue):
        self.entries += queue.entries

    def get_num_entries(self):
        return len(self.entries)

    def get_entry(self, i):
        return self.entries[i]

class RegionSceneManager(SceneManagerBase):
    min_near = 1e-6
    max_near_reagion = 1e5
    def __init__(self):
        SceneManagerBase.__init__(self)
        self.rendering_passes = []
        self.regions = []
        self.spread_objects = []
        self.background_region = None
        self.camera_mask = None
        self.infinity = 1e9
        self.inverse_z = settings.use_inverse_z

    def has_regions(self):
        return True

    def get_regions(self):
        return self.regions

    def add_pass(self, name: str, target: GraphicsOutput, camera_mask: DrawMask):
        print("Add pass", name)
        rendering_pass = RenderingPass(name, target, camera_mask)
        self.rendering_passes.append(rendering_pass)

    def attach_new_anchor(self, instance):
        pass

    def add_spread_object(self, instance):
        self.spread_objects.append(instance)

    def attach_spread_objects(self):
        for spread_object in self.spread_objects:
            for region in self.regions:
                clone = region.root.attach_new_node("clone")
                clone.set_transform(spread_object.parent.get_net_transform())
                spread_object.instance_to(clone)

    def add_background_object(self, instance):
        instance.reparent_to(self.background_region.root)

    def init_camera(self, camera_holder, default_camera):
        pass

    def update_scene_and_camera(self, distance_to_nearest, camera_holder):
        pass

    def pick_scene(self, mpos):
        result = CollisionEntriesCollection()
        for region in self.regions:
            pq = region.pick_scene(mpos)
            result.add_queue(pq)
        return result

    def clear_scene(self):
        for region in self.regions:
            region.remove()
        self.regions = []

    @pstat
    def build_scene(self, world, camera_holder, visibles, resolveds):
        state = world.get_state()
        self.clear_scene()
        background_resolved = []
        spread_bodies = []
        for scene_anchor in resolveds:
            anchor = scene_anchor.anchor
            if not anchor.visible: continue
            if not scene_anchor.virtual_object and scene_anchor.instance is not None:
                if scene_anchor.background:
                    background_resolved.append(scene_anchor)
                elif scene_anchor.spread_object:
                    spread_bodies.append(scene_anchor)
                else:
                    if anchor.distance_to_obs > anchor.get_bounding_radius():
                        coef = -anchor.vector_to_obs.dot(camera_holder.anchor.camera_vector)
                        near = (anchor.distance_to_obs  - anchor.get_bounding_radius()) * coef  * camera_holder.cos_fov2 / self.scale
                        far = (anchor.distance_to_obs + anchor.get_bounding_radius()) * coef / self.scale
                        near = max(near, self.min_near)
                    else:
                        near = self.min_near
                        far = self.min_near + anchor.get_bounding_radius() * 2 / self.scale
                    region = SceneRegion(self, near, far)
                    region.add_body(scene_anchor)
                    while len(self.regions) > 0 and region.overlap(self.regions[-1]):
                        region.merge(self.regions[-1])
                        self.regions.pop()
                    self.regions.append(region)
        if len(self.regions) > 0:
            # Sort the region from nearest to farthest
            self.regions.sort(key=lambda r: r.near)
            for prev_i, next_region in enumerate(self.regions[1:]):
                prev_region = self.regions[prev_i]
                if prev_region.far != next_region.near:
                    embedded_region = SceneRegion(self, prev_region.far, next_region.near)
                    self.regions.append(embedded_region)
            self.regions.sort(key=lambda r: r.near)
            farthest_region = SceneRegion(self, self.regions[-1].far, float('inf'))
            self.regions.append(farthest_region)
            if self.regions[0].near > self.min_near:
                if self.regions[0].near / self.min_near > self.max_near_reagion:
                    nearest_region = SceneRegion(self, self.min_near * self.max_near_reagion, self.regions[0].near)
                    self.regions.insert(0, nearest_region)
                    nearest_region = SceneRegion(self, self.min_near, self.min_near * self.max_near_reagion)
                    self.regions.insert(0, nearest_region)
                else:
                    nearest_region = SceneRegion(self, self.min_near, self.regions[0].near)
                    self.regions.insert(0, nearest_region)
            self.background_region = farthest_region
            #print("R", list(map(lambda r: (r.bodies[0].get_name() if len(r.bodies) > 0 else "empty") + f" : {r.near}:{r.far}", self.regions)))
        else:
            region = SceneRegion(self, self.min_near, float('inf'))
            self.regions.append(region)
            self.background_region = region
        for scene_anchor in spread_bodies:
            anchor = scene_anchor.anchor
            coef = 1 # -anchor.vector_to_obs.dot(camera_holder.anchor.camera_vector)
            near_distance = (anchor.distance_to_obs  - anchor.get_bounding_radius()) * coef / self.scale
            far_distance = (anchor.distance_to_obs + anchor.get_bounding_radius()) * coef / self.scale
            for region in self.regions:
                if region.overlap_range(near_distance, far_distance):
                    region.add_body(scene_anchor)
        background_region = self.regions[-1]
        for scene_anchor in background_resolved:
            background_region.add_body(scene_anchor)
        current_region_index = 0
        current_region = self.regions[0]
        for visible in visibles:
            anchor = visible.anchor
            if anchor.resolved: continue
            while anchor.z_distance  / self.scale > current_region.far and current_region_index + 1 < len(self.regions):
                current_region_index += 1
                current_region = self.regions[current_region_index]
            #print("ADD", visible.body.get_name(), visible.z_distance, "TO", current_region_index, current_region.near, current_region.far)
            current_region.add_point(visible)
        if len(self.regions) > 0:
            region_size = 1.0 / len(self.regions)
            if not self.inverse_z:
                # Start with the nearest region, which will start a depth 0 (i.e. near plane)
                base = 0.0
            else:
                base = 1.0
                region_size = -region_size
            for i, region in enumerate(self.regions):
                sort_index = len(self.regions) - i
                region.create(self.rendering_passes, state, camera_holder, self.inverse_z, base, min(base + region_size, 1 - 1e-6), sort_index)
                base += region_size
        self.attach_spread_objects()
        self.spread_objects = []

    def ls(self):
        for i, region in enumerate(self.regions):
            print("REGION", i)
            region.ls()

class SceneRegion:
    def __init__(self, scene_manager, near, far):
        self.scene_manager = scene_manager
        self.bodies = []
        self.near = near
        self.far = far
        self.rendering_passes: list[RenderingPass] = []
        self.root = NodePath('root')
        self.points = []

    def add_body(self, body):
        self.bodies.append(body)

    def add_point(self, scene_anchor):
        if scene_anchor.instance is not None:
            self.points.append(scene_anchor)
            scene_anchor.instance.reparent_to(self.root)

    def get_points(self):
        return self.points

    def get_points_collection(self):
        return self.points

    def overlap(self, other):
        return self.near <= other.near < self.far or other.near <= self.near < other.far or \
               self.far >= other.far > self.near or other.far >= self.far > other.near

    def overlap_range(self, near_distance, far_distance):
        return self.near <= near_distance < self.far or near_distance <= self.near < far_distance or \
               self.far >= far_distance > self.near or far_distance >= self.far > near_distance

    def merge(self, other):
        self.bodies += other.bodies
        self.near = min(self.near, other.near)
        self.far = max(self.far, other.far)

    def create(self, rendering_passes, state, camera_holder, inverse_z, section_near, section_far, sort_index):
        self.rendering_passes = [rendering_pass.copy() for rendering_pass in rendering_passes]
        self.root.set_state(state)
        for scene_anchor in self.bodies:
            if scene_anchor.instance.has_parent():
                clone = self.root.attach_new_node("region-anchor")
                scene_anchor.instance.instance_to(clone)
            else:
                scene_anchor.instance.reparent_to(self.root)
        lens = camera_holder.lens.make_copy()
        if inverse_z:
            lens.set_near_far(self.far * 1.01, self.near * 0.99)
        else:
            lens.set_near_far(self.near * 0.99, self.far * 1.01)
        for rendering_pass in self.rendering_passes:
            rendering_pass.camera.node().set_lens(lens)
            rendering_pass.camera.reparent_to(self.root)
            rendering_pass.camera.set_quat(camera_holder.camera_np.get_quat())
            rendering_pass.create()
            rendering_pass.display_region.set_sort(sort_index)
            if inverse_z:
                rendering_pass.display_region.set_depth_range(section_far, section_near)
            else:
                rendering_pass.display_region.set_depth_range(section_near, section_far)

    def remove(self):
        for rendering_pass in self.rendering_passes:
            rendering_pass.remove()
        self.rendering_passes = []
        # Note: This assume that all the instances attached to the root will be detached
        # If it's no longer the case, we have to manually detach them before destroying the root
        self.root = None

    def pick_scene(self, mpos):
        picker = CollisionTraverser()
        pq = CollisionHandlerQueue()
        picker_ray = CollisionRay()
        picker_node = CollisionNode('mouseRay')
        picker_np = self.rendering_passes[0].camera.attach_new_node(picker_node)
        picker_node.set_from_collide_mask(CollisionNode.get_default_collide_mask() | GeomNode.get_default_collide_mask())
        picker_node.add_solid(picker_ray)
        picker.add_collider(picker_np, pq)
        picker_ray.set_from_lens(self.rendering_passes[0].camera.node(), mpos.get_x(), mpos.get_y())
        #picker.show_collisions(region.root)
        picker.traverse(self.root)
        picker_np.remove_node()
        pq.sort_entries()
        return pq

    def ls(self):
        print("Near", self.near, "Far", self.far)
        print("Bodies:", list(map(lambda b: b.anchor.body.get_name(), self.bodies)))
        self.root.ls()
