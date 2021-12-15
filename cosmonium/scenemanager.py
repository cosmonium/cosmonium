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


from panda3d.core import Camera, NodePath, DepthOffsetAttrib, LPoint3

from .sprites import RoundDiskPointSprite, GaussianPointSprite, ExpPointSprite, MergeSprite
from .pointsset import PointsSet
from .foundation import BaseObject
from .utils import mag_to_scale
from .pstats import pstat
from . import settings

class SceneManagerBase:

    def __init__(self):
        self.midPlane = None
        self.scale = settings.scale
        self.point_sprite = GaussianPointSprite(size=16, fwhm=8)
        self.halos_sprite = ExpPointSprite(size=256, max_value=0.6)

    def attach_new_anchor(self, instance):
        raise NotImplementedError()

    def add_spread_object(self, instance):
        raise NotImplementedError()

    def add_background_object(self, instance):
        raise NotImplementedError()

    def init_camera(self, camera):
        raise NotImplementedError()

    def set_camera_mask(self, flags):
        raise NotImplementedError()

    def update_scene_and_camera(self, distance_to_nearest, camera):
        raise NotImplementedError()

    def build_scene(self, state, win, camera, visibles, resolved):
        raise NotImplementedError()

    def ls(self):
        raise NotImplementedError()

class StaticSceneManager(SceneManagerBase):
    def __init__(self):
        SceneManagerBase.__init__(self)
        self.near_plane = settings.near_plane
        self.far_plane = settings.far_plane
        self.infinite_far_plane = settings.infinite_far_plane
        self.auto_infinite_plane = settings.auto_infinite_plane
        self.lens_far_limit = settings.lens_far_limit
        self.root = render.attach_new_node('root')
        self.camera = None

    def attach_new_anchor(self, instance):
        instance.reparent_to(self.root)

    def add_spread_object(self, instance):
        pass

    def add_background_object(self, instance):
        instance.reparent_to(self.root)

    def init_camera(self, camera):
        if self.infinite_far_plane:
            far_plane = float('inf')
        else:
            far_plane = self.far_plane
        if self.auto_infinite_plane:
            self.infinity = self.near_plane / self.lens_far_limit / 1000
        else:
            self.infinity = self.infinite_plane
        print("Planes: ", self.near_plane, far_plane)
        camera.update_planes(self.near_plane, far_plane)
        self.camera = camera.cam

    def set_camera_mask(self, flags):
        self.camera.node().set_camera_mask(flags)

    def update_scene_and_camera(self, distance_to_nearest, camera):
        pass

    def build_scene(self, state, win, camera, visibles, resolved):
        self.root.set_state(state.get_state())

    def ls(self):
        self.root.ls()

class DynamicSceneManager(SceneManagerBase):
    def __init__(self):
        SceneManagerBase.__init__(self)
        self.near_plane = settings.near_plane
        self.far_plane = settings.far_plane
        self.infinite_plane = settings.infinite_plane
        self.infinite_far_plane = settings.infinite_far_plane
        self.auto_infinite_plane = settings.auto_infinite_plane
        self.lens_far_limit = settings.lens_far_limit
        self.auto_scale = settings.auto_scale
        self.min_scale= settings.min_scale
        self.max_scale = settings.max_scale
        self.set_frustum = settings.set_frustum
        self.mid_plane_ratio = settings.mid_plane_ratio
        self.infinity = self.infinite_plane
        self.root = render.attach_new_node('root')
        self.pointset = PointsSet(use_sprites=True, sprite=self.point_sprite)
        if settings.render_sprite_points:
            self.pointset.instance.reparent_to(self.root)
        self.haloset = PointsSet(use_sprites=True, sprite=self.halos_sprite, background=settings.halo_depth)
        if settings.render_sprite_points:
            self.haloset.instance.reparent_to(self.root)

    def attach_new_anchor(self, instance):
        instance.reparent_to(self.root)

    def add_spread_object(self, instance):
        pass

    def add_background_object(self, instance):
        instance.reparent_to(self.root)

    def init_camera(self, camera):
        if self.infinite_far_plane:
            far_plane = float('inf')
        else:
            far_plane = self.far_plane
        print("Planes: ", self.near_plane, far_plane)
        camera.update_planes(self.near_plane, far_plane)
        self.camera = camera.cam

    def set_camera_mask(self, flags):
        self.camera.node().set_camera_mask(flags)

    def update_scene_and_camera(self, distance_to_nearest, camera):
        if self.infinite_far_plane:
            far_plane = float('inf')
        else:
            far_plane = self.far_plane
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
                    near_plane = self.scale
                else:
                    near_plane = self.near_plane
                camera.update_planes(near_plane, far_plane)
        if self.auto_infinite_plane:
            self.infinity = near_plane / self.lens_far_limit / 1000
        else:
            self.infinity = self.infinite_plane
        self.midPlane = self.infinity / self.mid_plane_ratio

    @pstat
    def build_scene(self, state, win, camera, visibles, resolved):
        self.root.set_state(state.get_state())
        self.root.setShaderInput("midPlane", self.midPlane)
        self.pointset.reset()
        self.haloset.reset()
        for object_to_render in visibles:
            if object_to_render.visible:
                body = object_to_render.body
                if object_to_render.visible_size < settings.min_body_size * 2:
                    self.add_point(object_to_render.point_color, body.scene_anchor.scene_position, object_to_render.visible_size, object_to_render._app_magnitude, body.oid_color)
                    if settings.show_halo and object_to_render._app_magnitude < settings.smallest_glare_mag:
                        self.add_halo(object_to_render.point_color, body.scene_anchor.scene_position, object_to_render.visible_size, object_to_render._app_magnitude, body.oid_color)
        self.pointset.update()
        self.haloset.update()

    def add_point(self, point_color, scene_position, visible_size, app_magnitude, oid_color):
            scale = mag_to_scale(app_magnitude)
            if scale > 0:
                color = point_color * scale
                size = max(settings.min_point_size, settings.min_point_size + scale * settings.mag_pixel_scale)
                self.pointset.add_point(scene_position, color, size, oid_color)

    def add_halo(self, point_color, scene_position, visible_size, app_magnitude, oid_color):
            coef = settings.smallest_glare_mag - app_magnitude + 6.0
            radius = max(1.0, visible_size)
            size = radius * coef * 2.0
            self.haloset.add_point(LPoint3(*scene_position), point_color, size * 2, oid_color)

    def ls(self):
        self.root.ls()

class RegionSceneManager(SceneManagerBase):
    min_near = 1e-6
    def __init__(self):
        SceneManagerBase.__init__(self)
        self.regions = []
        self.spread_objects = []
        self.background_region = None
        self.camera_mask = None
        self.infinity = 1e9

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

    def init_camera(self, camera):
        pass

    def set_camera_mask(self, flags):
        self.camera_mask = flags
        for region in self.regions:
            region.set_camera_mask(flags)

    def update_scene_and_camera(self, distance_to_nearest, camera):
        pass

    def clear_scene(self):
        for region in self.regions:
            region.remove()
        self.regions = []

    @pstat
    def build_scene(self, world, win, camera, visibles, resolved):
        state = world.get_state()
        self.clear_scene()
        background_resolved = []
        for resolved in resolved:
            if not resolved.visible: continue
            if not resolved.body.virtual_object and resolved.body.scene_anchor.instance is not None:
                if not resolved.body.background:
                    coef = -resolved.vector_to_obs.dot(camera.anchor.camera_vector)
                    near = (resolved.distance_to_obs  - resolved._extend) * coef  * camera.cos_fov2 / self.scale
                    far = (resolved.distance_to_obs + resolved._extend) * coef / self.scale
                    near = max(near, self.min_near)
                    region = SceneRegion(self, near, far)
                    region.add_body(resolved.body)
                    while len(self.regions) > 0 and region.overlap(self.regions[-1]):
                        region.merge(self.regions[-1])
                        self.regions.pop()
                    self.regions.append(region)
                else:
                    background_resolved.append(resolved.body)
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
                nearest_region = SceneRegion(self, self.min_near, self.regions[0].near)
                self.regions.insert(0, nearest_region)
            self.background_region = farthest_region
            #print("R", list(map(lambda r: (r.bodies[0].get_name() if len(r.bodies) > 0 else "empty") + f" : {r.near}:{r.far}", self.regions)))
        else:
            region = SceneRegion(self, self.min_near, float('inf'))
            self.regions.append(region)
            self.background_region = region
        background_region = self.regions[-1]
        for body in background_resolved:
            background_region.add_body(body)
        current_region_index = 0
        current_region = self.regions[0]
        if settings.render_sprite_points:
            for visible in visibles:
                if visible.resolved: continue
                while visible.z_distance > current_region.far and current_region_index + 1 < len(self.regions):
                    current_region_index += 1
                    current_region = self.regions[current_region_index]
                #print("ADD", visible.body.get_name(), visible.z_distance, "TO", current_region_index)
                current_region.add_point(visible)
        if len(self.regions) > 0:
            region_size = 1.0 / len(self.regions)
            # Start with the nearest region, which will start a depth 0 (i.e. near plane)
            base = 0.0
            for i, region in enumerate(self.regions):
                sort_index = len(self.regions) - i
                region.create(win, state, camera, self.camera_mask, base, min(base + region_size, 1 - 1e-6), sort_index)
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
        self.win = None
        self.region = None
        self.root = NodePath('root')
        self.cam = None
        self.cam_np = None
        self.has_points = False
        self.pointset = None
        self.haloset = None

    def set_camera_mask(self, flags):
        self.cam.set_camera_mask(flags)

    def add_body(self, body):
        self.bodies.append(body)

    def add_point(self, anchor):
        if not self.has_points:
            self.pointset = PointsSet(use_sprites=True, sprite=self.scene_manager.point_sprite)
            self.pointset.instance.reparent_to(self.root)
            self.haloset = PointsSet(use_sprites=True, sprite=self.scene_manager.halos_sprite, background=settings.halo_depth)
            self.haloset.instance.reparent_to(self.root)
            self.has_points = True
        if anchor.visible_size < settings.min_body_size * 2 and anchor.body.scene_anchor.instance is not None:
            app_magnitude = anchor._app_magnitude
            point_color = anchor.point_color
            body = anchor.body
            body.scene_anchor.instance.reparent_to(self.root)
            scale = mag_to_scale(app_magnitude)
            if scale > 0:
                color = point_color * scale
                size = max(settings.min_point_size, settings.min_point_size + scale * settings.mag_pixel_scale)
                self.pointset.add_point(body.scene_anchor.scene_position, color, size, body.oid_color)
                if settings.show_halo and app_magnitude < settings.smallest_glare_mag:
                    coef = settings.smallest_glare_mag - app_magnitude + 6.0
                    radius = max(1.0, anchor.visible_size)
                    size = radius * coef * 2.0
                    self.haloset.add_point(LPoint3(*body.scene_anchor.scene_position), point_color, size * 2, body.oid_color)

    def overlap(self, other):
        return self.near <= other.near < self.far or other.near <= self.near < other.far or \
               self.far >= other.far > self.near or other.far >= self.far > other.near

    def merge(self, other):
        self.bodies += other.bodies
        self.near = min(self.near, other.near)
        self.far = max(self.far, other.far)

    def create(self, win, state, camera, camera_mask, section_near, section_far, sort_index):
        self.root.set_state(state)
        for body in self.bodies:
            body.scene_anchor.instance.reparent_to(self.root)
        self.cam = Camera("region-cam")
        self.cam.set_camera_mask(camera_mask)
        lens = camera.camLens.make_copy()
        lens.set_near_far(self.near * 0.99, self.far * 1.01)
        self.cam.set_lens(lens)
        self.cam_np = self.root.attach_new_node(self.cam)
        self.cam_np.set_quat(camera.camera_np.get_quat())
        self.win = win
        self.region = win.make_display_region((0, 1, 0, 1))
        self.region.disable_clears()
        #self.region.setClearColorActive(1)
        #self.region.setClearColor((1, 0, 0, 1))
        self.region.set_camera(self.cam_np)
        self.region.set_scissor_enabled(False)
        self.region.set_sort(sort_index)
        self.region.set_depth_range(section_near, section_far)
        if self.has_points:
            self.pointset.update()
            self.haloset.update()

    def remove(self):
        self.win.remove_display_region(self.region)
        self.win = None
        self.region = None
        self.root = None
        self.cam = None
        self.cam_np = None

    def ls(self):
        print("Near", self.near, "Far", self.far)
        print("Bodies:", list(map(lambda b: b.get_name(), self.bodies)))
        self.root.ls()
