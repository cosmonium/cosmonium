from .foundation import CompositeObject
from .sceneanchor import ObserverSceneAnchor
from panda3d.core import OmniBoundingVolume

class SceneWorld:
    def __init__(self):
        self.scene_anchor = self.create_scene_anchor()

    def create_scene_anchor(self):
        raise NotImplementedError()

class ObserverCenteredWorld(SceneWorld):
    def __init__(self):
        SceneWorld.__init__(self)
        self.components = CompositeObject('<root>')
        self.components.set_scene_anchor(self.scene_anchor)
        self.components.visible = True

    def create_scene_anchor(self):
        return ObserverSceneAnchor()

    def on_visible(self, scene_manager):
        self.scene_anchor.create_instance(scene_manager)

    def on_hidden(self, scene_manager):
        self.scene_anchor.remove_instance()

    def add_component(self, component):
        self.components.add_component(component)

    def remove_component(self, component):
        self.components.remove_component(component)

    def update(self, time, dt):
        self.components.update(time, dt)

    def update_obs(self, observer):
        self.components.update_obs(observer)

    def check_visibility(self, frustum, pixel_size):
        self.components.check_visibility(frustum, pixel_size)

    def check_settings(self):
        self.components.check_settings()

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        self.components.check_and_update_instance(scene_manager, camera_pos, camera_rot)
