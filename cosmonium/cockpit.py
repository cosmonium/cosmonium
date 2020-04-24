from panda3d.core import LQuaternion, LVector3d

from .shapes import ShapeObject
from .parameters import ParametersGroup

class Cockpit(ShapeObject):
    def __init__(self, name, shape, appearance, shader):
        ShapeObject.__init__(self, name, shape, appearance, shader, clickable=False)
        self.camera = None

    def place_instance(self, instance, parent):
        instance.set_quat(LQuaternion(*self.camera.get_camera_rot()))

    def get_user_parameters(self):
        parameters = ShapeObject.get_user_parameters(self)
        group = ParametersGroup(self.get_name(), parameters)
        return group

    def apply_instance(self, instance):
        ShapeObject.apply_instance(self, instance)
        instance.hide(self.AllCamerasMask)
        instance.show(self.NearCameraMask)
