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
from .sceneanchor import SceneAnchor, AbsoluteSceneAnchor, ObserverSceneAnchor
from ..astro.frame import AbsoluteReferenceFrame
from ..namedobject import NamedObject

class Worlds:
    def __init__(self):
        self.worlds = []

    def add_world(self, world):
        self.worlds.append(world)

    def remove_world(self, world):
        self.worlds.remove(world)

    def update_anchor(self, time, update_id):
        for world in self.worlds:
            world.anchor.update(time, update_id)

    def update_anchor_obs(self, observer, update_id):
        for world in self.worlds:
            world.anchor.update_observer(observer, update_id)
            world.anchor.update_state(observer, update_id)

    def update_scene_anchor(self, scene_manager):
        for world in self.worlds:
            #TODO: This is a hack
            world.scene_anchor.create_instance(scene_manager)
            world.scene_anchor.update(scene_manager)

    def update(self, time, dt):
        for world in self.worlds:
            world.update(time, dt)

    def update_obs(self, observer):
        for world in self.worlds:
            world.update_obs(observer)

    def check_visibility(self, frustum, pixel_size):
        for world in self.worlds:
            world.check_visibility(frustum, pixel_size)

    def update_lod(self, camera_pos, camera_rot):
        for world in self.worlds:
            world.update_lod(camera_pos, camera_rot)

    def check_settings(self):
        for world in self.worlds:
            world.check_settings()

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        for world in self.worlds:
            world.check_and_update_instance(scene_manager, camera_pos, camera_rot)


class SceneWorld(NamedObject):
    virtual_object = False
    background = False
    support_offset_body_center = False
    def __init__(self, name):
        NamedObject.__init__(self, [name], None, None)
        self.anchor = None
        self.scene_anchor = None

class SimpleWorld(SceneWorld):
    def __init__(self, name):
        SceneWorld.__init__(self, name)
        self.anchor = self.create_anchor()
        self.anchor.body = self
        self.scene_anchor = self.create_scene_anchor()
        self.lights = None

        self.components = CompositeObject('<root>')
        self.components.set_scene_anchor(self.scene_anchor)

        #TODO: To remove, needed by cam controller
        self.apparent_radius = 0.0

    def create_anchor(self):
        raise NotImplementedError()

    def create_scene_anchor(self):
        raise NotImplementedError()

    def set_lights(self, lights):
        if self.lights is not None:
            self.lights.remove_all()
        self.lights = lights
        self.components.set_lights(lights)

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
        self.scene_anchor.remove_instance()
        self.components.visible = False
        self.visible = False

    def add_component(self, component):
        self.components.add_component(component)
        component.set_owner(self)
        component.set_lights(self.lights)

    def remove_component(self, component):
        if component is not None:
            self.components.remove_component(component)
            component.set_owner(None)

    def check_settings(self):
        self.components.check_settings()

    def on_resolved(self, scene_manager):
        #TODO!
        self.on_visible(scene_manager)

    def on_point(self, scene_manager):
        pass

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
            component.start_shadows_update()

    def self_shadows_update(self, light_source):
        pass

    def add_shadow_target(self, light_source, target):
        pass

    def end_shadows_update(self):
        for component in self.components.components:
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

    def create_anchor(self):
        return CartesianAnchor(self.anchor_class, self, AbsoluteReferenceFrame())

    def create_scene_anchor(self):
        return SceneAnchor(self.anchor, False, LColor(), True)

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
