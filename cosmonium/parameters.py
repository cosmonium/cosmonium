import sys
from math import log, exp

from panda3d.core import LVecBase2, LVecBase3, LVecBase4, LVecBase2f, LVecBase3f, LVecBase4f, LVecBase2d, LVecBase3d, LVecBase4d
if sys.version_info[0] >= 3:
    from collections.abc import Iterable
else:
    from collections import Iterable

from .utils import isclose

vector_types = (Iterable, LVecBase2, LVecBase3, LVecBase4, LVecBase2f, LVecBase3f, LVecBase4f, LVecBase2d, LVecBase3d, LVecBase4d)

class ParametersGroup(object):
    def __init__(self, name=None, *parameters):
        self.name = name
        if len(parameters) == 1 and isinstance(parameters[0], Iterable):
            self.parameters = parameters[0]
        else:
            self.parameters = list(parameters)

    def set_parameters(self, parameters):
        self.parameters = parameters

    def add_parameter(self, parameter):
        if parameter is not None:
            self.parameters.append(parameter)

    def add_parameters(self, *parameters):
        if len(parameters) == 1:
            if isinstance(parameters[0], Iterable):
                self.parameters += parameters[0]
            elif parameters[0] is not None:
                self.parameters.append(parameters[0])
        else:
            self.parameters += parameters

    def prepend_parameters(self, *parameters):
        if len(parameters) == 1 and isinstance(parameters[0], Iterable):
            self.parameters = parameters[0] + self.parameters
        else:
            self.parameters = list(parameters) + self.parameters

    def is_group(self):
        return True

class UserParameterBase(object):
    TYPE_STRING = 0
    TYPE_FLOAT = 1
    TYPE_INT = 2
    TYPE_BOOL = 3
    TYPE_VEC = 4

    SCALE_LINEAR = 0
    SCALE_LOG = 1
    SCALE_LOG_0 = 2

    def __init__(self, name, param_type, value_range, scale, units, nb_components):
        self.name = name
        self.param_type = param_type
        self.value_range = value_range
        self.scale = scale
        self.units = units
        self.nb_components = nb_components

    def is_group(self):
        return False

    def get_range(self, scale=False):
        if scale and self.scale in (self.SCALE_LOG, self.SCALE_LOG_0):
            return [log(self.value_range[0]), log(self.value_range[1])]
        else:
            return self.value_range

    def get_type(self):
        if self.param_type == self.TYPE_STRING:
            return str
        elif self.param_type == self.TYPE_INT:
            return int
        elif self.param_type == self.TYPE_FLOAT:
            return float
        elif self.param_type == self.TYPE_BOOL:
            return bool
        elif self.param_type == self.TYPE_VEC:
            return float
        else:
            return None

    def convert_to_type(self, value):
        if self.param_type == self.TYPE_STRING:
            return value
        elif self.param_type == self.TYPE_INT:
            return int(value)
        elif self.param_type == self.TYPE_FLOAT:
            return float(value)
        elif self.param_type == self.TYPE_BOOL:
            return bool(value)
        elif self.param_type == self.TYPE_VEC:
            if isinstance(value, str) or not isinstance(value, vector_types):
                return float(value)
            else:
                return list(map(lambda x: float(x), value))
        else:
            return value

    def do_get_param(self):
        return None

    def do_set_param(self, value):
        pass

    def scale_value(self, value, scale):
        if self.param_type in (self.TYPE_BOOL, self.TYPE_STRING): return value
        if not scale: return value / self.units
        if self.scale == self.SCALE_LOG:
            value = log(value)
        elif self.scale == self.SCALE_LOG_0:
            if value == 0:
                value = log(self.value_range[0])
            else:
                value = log(value)
        else:
            value = value / self.units
        return value

    def unscale_value(self, value, scale):
        if self.param_type in (self.TYPE_BOOL, self.TYPE_STRING): return value
        if not scale: return value * self.units
        if self.scale == self.SCALE_LOG:
            value = exp(value)
        elif self.scale == self.SCALE_LOG_0:
            if isclose(value, log(self.value_range[0]), rel_tol=1e-6):
                value = 0
            else:
                value = exp(value)
        else:
            value = value * self.units
        return value

    def get_param(self, scale=False):
        value = self.do_get_param()
        return self.scale_value(value, scale)

    def set_param(self, value, scale=False):
        value = self.unscale_value(value, scale)
        self.do_set_param(value)

    def get_param_component(self, component, scale=False):
        param = self.do_get_param()
        return self.scale_value(param[component], scale)

    def set_param_component(self, component, value, scale=False):
        param = self.do_get_param()
        param[component] = self.unscale_value(value, scale)
        self.do_set_param(param)

class UserParameter(UserParameterBase):
    def __init__(self, name, setter, getter, param_type=None, value_range=None, scale=UserParameterBase.SCALE_LINEAR, units=1.0, nb_components=1):
        UserParameterBase.__init__(self, name, param_type, value_range, scale, units, nb_components)
        self.setter = setter
        self.getter = getter

    def do_get_param(self):
        return self.getter()

    def do_set_param(self, value):
        self.setter(value)

class AutoUserParameter(UserParameterBase):
    def __init__(self, name, attribute, instance, param_type=None, value_range=None, scale=UserParameterBase.SCALE_LINEAR, units=1.0, nb_components=1):
        UserParameterBase.__init__(self, name, param_type, value_range, scale, units, nb_components)
        self.attribute = attribute
        self.instance = instance

    def do_get_param(self):
        return getattr(self.instance, self.attribute)

    def do_set_param(self, value):
        setattr(self.instance, self.attribute, value)
