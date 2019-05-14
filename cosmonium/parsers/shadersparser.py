from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LColor

from ..shaders import FlatLightingModel, LunarLambertLightingModel, LambertPhongLightingModel

from .yamlparser import YamlModuleParser

class LightingModelYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, appearance):
        (object_type, parameters) = cls.get_type_and_data(data, 'lambert-phong')
        if object_type == 'lambert-phong':
            model = LambertPhongLightingModel()
        elif object_type == 'lunar-lambert':
            model = LunarLambertLightingModel()
        elif object_type == 'flat':
            model = FlatLightingModel()
            #TODO: This should be done a better way...
            if appearance.emissionColor is None:
                appearance.emissionColor = LColor(1, 1, 1, 1)
        else:
            print("Lighting model type", object_type, "unknown")
            model = None
        return model

