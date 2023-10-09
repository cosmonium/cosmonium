#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from panda3d.core import LColor, LVector3d

from ..foundation import CompositeObject
from ..engine.anchors import CartesianAnchor, FlatSurfaceAnchor, OriginAnchor, ObserverAnchor
from .sceneanchor import SceneAnchorCollection
from .sceneanchor import SceneAnchor, AbsoluteSceneAnchor, ObserverSceneAnchor
from ..astro.frame import AbsoluteReferenceFrame
from ..namedobject import NamedObject

class Worlds:
    stellar_object = False

    def __init__(self):
        self.worlds = []
        self.specials = []
        self.global_shadows = None
        self.old_visibles = []
        self.visibles = []
        self.becoming_visibles = []
        self.no_longer_visibles = []
        self.old_resolved = []
        self.resolved = []
        self.becoming_resolved = []
        self.no_longer_resolved = []

    def init(self):
        for world in self.worlds:
            world.init()

    def set_global_shadows(self, global_shadows):
        if self.global_shadows is not None:
            self.global_shadows.remove()
        self.global_shadows = global_shadows
        if self.global_shadows is not None:
            self.global_shadows.create()

    def add_world(self, world):
        self.worlds.append(world)
        world.set_parent(self)

    def remove_world(self, world):
        world.set_parent(None)
        self.worlds.remove(world)

    def add_special(self, world):
        self.specials.append(world)

    def update_specials(self, time, update_id):
        for world in self.specials:
            world.anchor.update(time, update_id)

    def update_anchor(self, time, update_id):
        for world in self.worlds:
            if world.controller is not None:
                world.controller.update(time, 0)
            world.anchor.update(time, update_id)

    def update_specials_observer(self, observer, update_id):
        for world in self.specials:
            world.anchor.update_observer(observer.anchor, update_id)
            world.anchor.update_id = update_id

    def update_anchor_obs(self, observer, update_id):
        for world in self.worlds:
            world.anchor.update_observer(observer, update_id)
            world.anchor.update_state(observer, update_id)

    def update_scene_anchor(self, scene_manager):
        for world in self.worlds:
            #TODO: This is a hack
            world.scene_anchor.create_instance(scene_manager)
            world.scene_anchor.update(scene_manager)

    def start_update(self):
        self.old_visibles = self.visibles
        self.visibles = []
        self.becoming_visibles = []
        self.no_longer_visibles = []
        self.old_resolved = self.resolved
        self.resolved = []
        self.becoming_resolved = []
        self.no_longer_resolved = []

    def update(self, time, dt, update_id, observer):
        self.update_anchor(time, update_id)
        self.update_anchor_obs(observer.anchor, update_id)
        for world in self.worlds:
            if world.anchor.visible:
                self.visibles.append(world.anchor)
            if world.anchor.resolved:
                self.resolved.append(world.anchor)

    def update_states(self):
        visibles = []
        resolved = []
        self.visible_scene_anchors = SceneAnchorCollection()
        self.resolved_scene_anchors = SceneAnchorCollection()
        for anchor in self.visibles:
            visible = anchor.resolved
            if visible:
                visibles.append(anchor)
                self.visible_scene_anchors.add_scene_anchor(anchor.body.scene_anchor)
                if not anchor.was_visible:
                    self.becoming_visibles.append(anchor)
                if anchor.resolved:
                    resolved.append(anchor)
                    self.resolved_scene_anchors.add_scene_anchor(anchor.body.scene_anchor)
            else:
                if anchor.was_visible:
                    self.no_longer_visibles.append(anchor)
            anchor.visible = visible
        for anchor in self.old_visibles:
            if not anchor in self.visibles:
                self.no_longer_visibles.append(anchor)
                anchor.was_visible = anchor.visible
                anchor.visible = False
        self.visibles = visibles
        self.resolved = resolved
        for anchor in resolved:
            if not anchor.was_resolved:
                self.becoming_resolved.append(anchor)
        for anchor in self.old_resolved:
            if not anchor in self.resolved:
                self.no_longer_resolved.append(anchor)

    def find_shadows(self):
        for world in self.worlds:
            world.start_shadows_update()

        if self.global_shadows:
            for world in self.worlds:
                for component in world.get_components():
                    if component.concrete_object:
                        self.global_shadows.add_target(component)

        for world in self.worlds:
            world.end_shadows_update()

    def update_height_under(self, observer):
        for anchor in self.resolved:
            anchor._height_under = anchor.body.get_height_under(observer.get_local_position())

    def update_scene_anchors(self, scene_manager):
        for newly_visible in self.becoming_visibles:
            newly_visible.body.scene_anchor.create_instance(scene_manager)
        for visible in self.visibles:
            visible.body.scene_anchor.update(scene_manager)
        for old_visible in self.no_longer_visibles:
            old_visible.body.scene_anchor.remove_instance()

    def update_instances_state(self, scene_manager):
        #for occluder in self.shadow_casters:
        #    occluder.update_scene(self.c_observer)
        #    occluder.body.scene_anchor.update(scene_manager)
        for newly_visible in self.becoming_visibles:
            # print("NEW VISIBLE", newly_visible.body.get_name())
            if newly_visible.resolved:
                newly_visible.body.on_resolved(scene_manager)
        for newly_resolved in self.becoming_resolved:
            # print("NEW RESOLVED", newly_resolved.body.get_name())
            newly_resolved.body.on_resolved(scene_manager)
        for old_resolved in self.no_longer_resolved:
            # print("OLD RESOLVED", old_resolved.body.get_name())
            old_resolved.body.on_point(scene_manager)
        for old_visible in self.no_longer_visibles:
            # print("OLD VISIBLE", old_visible.body.get_name())
            #self.labels.remove_label(old_visible.body)
            if old_visible.resolved:
                old_visible.body.on_point(scene_manager)

    def update_lod(self, observer):
        camera_pos = observer.get_local_position()
        camera_rot = observer.get_absolute_orientation()
        frustum = observer.anchor.rel_frustum
        pixel_size = observer.anchor.pixel_size
        for resolved in self.resolved:
            world = resolved.body
            #TODO: this will update the body's components
            world.update_obs(observer)
            world.check_visibility(frustum, pixel_size)
            world.update_lod(camera_pos, camera_rot)

    def update_instances(self, scene_manager, observer):
        camera_pos = observer.get_local_position()
        camera_rot = observer.get_absolute_orientation()

        if self.global_shadows is not None:
            self.global_shadows.update(scene_manager)

        for resolved in self.resolved:
            world = resolved.body
            world.check_and_update_instance(scene_manager, camera_pos, camera_rot)
        self.update_scene_anchor(scene_manager)

    def check_settings(self):
        for world in self.worlds:
            world.check_settings()


class SceneWorld(NamedObject):

    virtual_object = False
    background = False
    support_offset_body_center = False
    stellar_object = False

    def __init__(self, name):
        NamedObject.__init__(self, [name], None, None)
        self.anchor = None
        self.scene_anchor = None
        self.parent = None

    def init(self):
        pass

    def set_parent(self, parent):
        self.parent = parent

class SimpleWorld(SceneWorld):
    def __init__(self, name):
        SceneWorld.__init__(self, name)
        self.anchor = self.create_anchor()
        self.anchor.body = self
        self.scene_anchor = self.create_scene_anchor()
        self.controller = None
        self.lights = None

        self.components = CompositeObject('<root>')
        self.components.set_scene_anchor(self.scene_anchor)

        #TODO: To remove, needed by cam controller
        self.apparent_radius = 0.0

    def init(self):
        if self.controller is not None:
            self.controller.init()

    def create_anchor(self):
        raise NotImplementedError()

    def create_scene_anchor(self):
        raise NotImplementedError()

    def set_controller(self, controller):
        self.controller = controller

    def set_lights(self, lights):
        if self.lights is not None:
            self.lights.remove_all()
        self.lights = lights
        self.components.set_lights(lights)

    def set_scattering(self, scattering):
        for component in self.components.components:
            if component.concrete_object:
                scattering.add_shape_object(component)

    def get_height_under(self, position):
        return 0.0

    def set_visibility_override(self, override):
        if override == self.anchor.visibility_override: return
        if override:
            self.anchor.visibility_override = True
        else:
            self.anchor.visibility_override = False
            #Force recheck of visibility or the object will be instanciated in create_or_update_instance()
            self.check_visibility(self.context.observer.anchor.frustum, self.context.observer.anchor.pixel_size)

    def on_visible(self, scene_manager):
        self.visible = True
        self.components.visible = True
        self.scene_anchor.create_instance(scene_manager)
        self.scene_anchor.update(scene_manager)

    def on_hidden(self, scene_manager):
        self.components.remove_instance()
        self.scene_anchor.remove_instance()
        self.components.visible = False
        self.visible = False

    def add_component(self, component):
        self.components.add_component(component)
        component.set_owner(self)
        component.set_body(self)
        component.set_lights(self.lights)

    def remove_component(self, component):
        if component is not None:
            self.components.remove_component(component)
            component.set_owner(None)
            component.set_body(None)

    def check_settings(self):
        self.components.check_settings()

    def on_resolved(self, scene_manager):
        #TODO!
        self.on_visible(scene_manager)

    def on_point(self, scene_manager):
        #TODO!
        self.on_hidden(scene_manager)

    def update(self, time, dt):
        self.components.update(time, dt)

    def update_obs(self, observer):
        self.components.update_obs(observer)

    def check_visibility(self, frustum, pixel_size):
        self.components.check_visibility(frustum, pixel_size)

    def get_components(self):
        return self.components.components

    def start_shadows_update(self):
        #TODO: Add method in CompositeObject
        for component in self.components.components:
            if component.concrete_object:
                component.start_shadows_update()

    def self_shadows_update(self, light_source):
        pass

    def add_shadow_target(self, light_source, target):
        pass

    def end_shadows_update(self):
        for component in self.components.components:
            if component.concrete_object:
                component.end_shadows_update()

    def update_lod(self, camera_pos, camera_rot):
        self.components.update_lod(camera_pos, camera_rot)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        if self.lights is not None:
            self.lights.update_instances(camera_pos)
        self.components.check_and_update_instance(scene_manager, camera_pos, camera_rot)

    #TODO: To remove
    def get_apparent_radius(self):
        return self.apparent_radius


class CartesianWorld(SimpleWorld):

    anchor_class = 0

    def __init__(self, name):
        SimpleWorld.__init__(self, name)
        self.anchor.set_bounding_radius(self.get_bounding_radius())

    def create_anchor(self):
        return CartesianAnchor(self.anchor_class, self, AbsoluteReferenceFrame())

    def create_scene_anchor(self):
        return SceneAnchor(self.anchor, False, LColor(), True)

    def get_terrain(self):
        return self.parent.get_terrain()

    def get_bounding_radius(self):
        return 100

class OriginCenteredWorld(SimpleWorld):
    def __init__(self, name):
        SimpleWorld.__init__(self, name)

    def create_anchor(self):
        return OriginAnchor()

    def create_scene_anchor(self):
        return AbsoluteSceneAnchor(self.anchor)


class FlatTerrainWorld(OriginCenteredWorld):
    def __init__(self, name):
        self.surface = None
        OriginCenteredWorld.__init__(self, name)
        self.model_body_center_offset = 0.0

    def create_anchor(self):
        return FlatSurfaceAnchor(0, self, self.surface)

    def set_terrain(self, surface):
        self.remove_component(self.surface)
        self.surface = surface
        self.anchor.set_surface(surface)
        if surface is not None:
            self.add_component(surface)
            surface.set_body(self)

    def get_height_under(self, position):
        if self.surface is not None:
            return self.surface.get_height_under(position)
        else:
            return 0

    def get_point_under(self, position):
        if self.surface is not None:
            return self.surface.get_point_under(position)
        else:
            return position

    def get_tangent_plane_under(self, position):
        return (LVector3d.right(), LVector3d.forward(), LVector3d.up())


class ObserverCenteredWorld(SimpleWorld):
    def __init__(self, name, background=False):
        self.background = background
        SimpleWorld.__init__(self, name)
        self.components.visible = True

    def create_anchor(self):
        return ObserverAnchor(0, self)

    def create_scene_anchor(self):
        return ObserverSceneAnchor(self.anchor, background=self.background)
