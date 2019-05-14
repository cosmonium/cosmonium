from __future__ import print_function

class TerrainObject(object):
    def __init__(self, shape=None, appearance=None, shader=None):
        self.parent = None
        self.shape = None
        self.set_shape(shape)
        self.appearance = appearance
        self.shader = shader

    def set_shape(self, shape):
        if self.shape is not None:
            self.shape.set_owner(None)
            self.shape = None
        self.shape = shape
        if shape is not None:
            self.shape.set_owner(self.parent)
            self.shape.parent = self

    def set_parent(self, parent):
        self.parent = parent
        if self.shape is not None:
            self.shape.set_owner(parent)

    def set_appearance(self, appearance):
        self.appearance = appearance

    def set_shader(self, shader):
        self.shader = shader

    def apply_instance(self, instance):
        if instance != self.instance:
            self.instance = instance
        if self.appearance is not None:
            self.appearance.bake()
            self.appearance.apply(self.shape, self.shader)
        if self.shader is not None:
            self.shader.apply(self.shape, self.appearance)
            self.shader.update(self.shape, self.appearance)
        self.shape.apply_owner()
        self.instance.reparentTo(render)

    def create_instance(self, callback=None, cb_args=()):
        self.instance = self.shape.create_instance(callback, cb_args)
        if self.instance is not None:
            self.apply_instance(self.instance)

    def create_instance_delayed(self):
        self.instance_ready = True

    def remove_instance(self):
        if self.instance:
            self.instance.removeNode()
            self.instance = None
            self.instance_ready = False

    def update_shader(self):
        if self.instance is not None and self.shader is not None:
            self.shader.apply(self.shape, self.appearance)

    def update_instance(self):
        if self.shader is not None:
            self.shader.update(self.shape, self.appearance)
