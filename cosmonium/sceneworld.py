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


from .foundation import CompositeObject
from .anchors import CartesianAnchor, FlatSurfaceAnchor, OriginAnchor, ObserverAnchor
from .sceneanchor import SceneAnchor, AbsoluteSceneAnchor, ObserverSceneAnchor
from cosmonium.astro.frame import AbsoluteReferenceFrame
from cosmonium.namedobject import NamedObject

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

    def check_settings(self):
        for world in self.worlds:
            world.check_settings()

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        for world in self.worlds:
            world.check_and_update_instance(scene_manager, camera_pos, camera_rot)


class SceneWorld(NamedObject):
    virtual_object = False
    background = False
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

    def on_visible(self, scene_manager):
        self.scene_anchor.create_instance(scene_manager)
        self.scene_anchor.update(scene_manager)

    def on_hidden(self, scene_manager):
        self.scene_anchor.remove_instance()

    def add_component(self, component):
        self.components.add_component(component)
        component.set_owner(self)

    def remove_component(self, component):
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
        self.components.visible = True

    def create_anchor(self):
        return CartesianAnchor(self.anchor_class, self, AbsoluteReferenceFrame())

    def create_scene_anchor(self):
        return SceneAnchor(self.anchor, False, True)

class OriginCenteredWorld(SimpleWorld):
    def __init__(self, name):
        SimpleWorld.__init__(self, name)
        self.components.visible = True

    def create_anchor(self):
        return OriginAnchor()

    def create_scene_anchor(self):
        return AbsoluteSceneAnchor(self.anchor)


class FlatTerrainWorld(OriginCenteredWorld):
    def __init__(self, name):
        self.terrain = None
        OriginCenteredWorld.__init__(self, name)

    def create_anchor(self):
        return FlatSurfaceAnchor(0, self, self.terrain)

    def set_terrain(self, terrain):
        self.terrain = terrain
        self.anchor.set_surface(terrain)
        self.add_component(terrain)

    def get_height_under(self, position):
        if self.terrain is not None:
            return self.terrain.get_height_at(position[0], position[1])
        else:
            return 0

class ObserverCenteredWorld(SimpleWorld):
    def __init__(self, name):
        SimpleWorld.__init__(self, name)
        self.components.visible = True

    def create_anchor(self):
        return ObserverAnchor(0, self)

    def create_scene_anchor(self):
        return ObserverSceneAnchor(self.anchor)
