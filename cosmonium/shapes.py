from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import GeomNode
from panda3d.core import LVecBase3, LPoint3d, LVector3, LVector3d
from panda3d.core import NodePath, BitMask32
from panda3d.core import CollisionSphere, CollisionNode, OmniBoundingVolume
from panda3d.core import Material

from .foundation import VisibleObject
from .shaders import AutoShader
from .dircontext import defaultDirContext
from .mesh import load_model, load_panda_model
from . import geometry
from . import settings
from cosmonium.shadows import MultiShadows

#TODO: Should inherit from VisibleObject !
class Shape:
    patchable = False
    offset = False
    use_collision_solid = False
    deferred_instance = False

    def __init__(self):
        self.instance = None
        self.collision_solid = None
        self.scale = LVector3(1.0, 1.0, 1.0)
        self.radius = 1.0
        self.owner = None
        self.inv_u = False
        self.inv_v = False
        self.swap_uv = False
        self.instance_ready = False
        self.jobs_pending = 0
        self.jobs = 0
        self.clickable = False
        self.attribution = None

    def check_settings(self):
        pass

    def is_spherical(self):
        return True

    def create_instance(self):
        return None
    
    def remove_instance(self):
        if self.instance is not None:
            self.instance.detach_node()
            self.instance = None
        self.instance_ready = False

    def create_collision_solid(self, radius=1.0):
        cs = CollisionSphere(0, 0, 0, radius)
        self.collision_solid = self.instance.attachNewNode(CollisionNode('cnode'))
        self.collision_solid.node().addSolid(cs)
        #self.collision_solid.show()

    def show(self):
        if self.instance:
            self.instance.show()

    def hide(self):
        if self.instance:
            self.instance.hide()

    def str_id(self):
        return 'shape'

    def set_owner(self, owner):
        self.owner = owner
        self.apply_owner()

    def apply_owner(self):
        if self.instance is not None:
            if self.use_collision_solid and self.collision_solid is not None:
                self.collision_solid.setPythonTag('owner', self.owner)
            self.instance.setPythonTag('owner', self.owner)

    def update_lod(self, camera_pos, distance_to_obs, pixel_size, appearance):
        return False

    def set_texture_to_lod(self, texture, texture_stage, texture_lod, patched):
        pass

    def set_scale(self, scale):
        self.radius = max(scale)
        self.scale = scale

    def set_radius(self, radius):
        self.radius = radius
        self.scale = LVector3(radius, radius, radius)

    def get_scale(self):
        return self.scale

    def global_to_shape_coord(self, x, y):
        return (x, y)

    def coord_to_uv(self, coord):
        return coord

    def get_height_at(self, coord):
        return self.radius

    def get_normals_at(self, coord):
        raise NotImplementedError

    def find_patch_at(self, coord):
        return self

    def set_clickable(self, clickable):
        self.clickable = clickable
        if self.use_collision_solid and self.collision_solid is not None:
            if clickable:
                self.collision_solid.node().setIntoCollideMask(CollisionNode.getDefaultCollideMask())
            else:
                self.collision_solid.node().setIntoCollideMask(BitMask32.all_off())
            #The instance itself is not clickable
            self.instance.setCollideMask(BitMask32.all_off())
        else:
            if clickable:
                self.instance.setCollideMask(GeomNode.getDefaultCollideMask())
            else:
                self.instance.setCollideMask(BitMask32.all_off())

class CompositeShapeObject(object):
    def __init__(self):
        self.components = []
        self.owner = None
        self.parent = None

    def add_component(self, component):
        self.components.append(component)
        component.set_parent(self.parent)
        component.set_owner(self.owner)

    def set_parent(self, parent):
        self.parent = parent
        for component in self.components:
            component.set_parent(self.parent)

    def set_owner(self, owner):
        self.owner = owner
        for component in self.components:
            component.set_owner(self.owner)

    def check_settings(self):
        for component in self.components:
            component.check_settings()

    def add_after_effect(self, after_effect):
        for component in self.components:
            component.add_after_effect(after_effect)

    def create_instance(self):
        for component in self.components:
            component.create_instance()

    def update_instance(self, camera_pos, orientation):
        for component in self.components:
            component.update_instance(camera_pos, orientation)

    def remove_instance(self):
        for component in self.components:
            component.remove_instance()

class ShapeObject(VisibleObject):
    def __init__(self, name, shape=None, appearance=None, shader=None, clickable=True):
        VisibleObject.__init__(self, name)
        self.shape = None
        self.set_shape(shape)
        self.appearance = appearance
        if shader is None:
            shader = AutoShader()
        self.shader = shader
        self.clickable = clickable
        self.instance_ready = False
        self.owner = None
        self.first_patch = True
        self.shadows = MultiShadows(self)
        self.shadow_caster = None

    def check_settings(self):
        self.shape.check_settings()

    def set_shape(self, shape):
        if self.shape is not None:
            self.shape.set_owner(None)
            self.shape.parent = None
        self.shape = shape
        if shape is not None:
            self.shape.set_owner(self.parent)
            self.shape.parent = self

    def set_owner(self, owner):
        self.owner = owner

    def set_parent(self, parent):
        VisibleObject.set_parent(self, parent)
        if self.shape is not None:
            self.shape.set_owner(parent)

    def set_appearance(self, appearance):
        self.appearance = appearance

    def set_shader(self, shader):
        self.shader = shader

    def add_after_effect(self, after_effect):
        if self.shader is not None:
            self.shader.add_after_effect(after_effect)

    def set_scale(self, scale):
        self.shape.set_scale(scale)

    def get_scale(self):
        return self.shape.get_scale()

    def create_instance(self, callback=None, cb_args=()):
        self.callback = callback
        self.cb_args = cb_args
        self.instance = self.shape.create_instance()
        if not self.shape.deferred_instance:
            self.apply_instance(self.instance)
        else:
            self.shape.apply_owner()
            self.instance.reparentTo(self.context.world)
        return self.instance

    def apply_instance(self, instance):
        #print("Apply", self.get_name())
        if instance != self.instance:
            if self.instance is not None:
                self.instance.remove_node()
            self.instance = instance
        self.shape.set_clickable(self.clickable)
        self.shape.apply_owner()
        self.instance.reparentTo(self.context.world)
        if self.parent.is_emissive():
            #TODO: Should be done by the owner of the shape
            myMaterial = Material()
            myMaterial.setEmission((1, 1, 1, 1))
            self.instance.setMaterial(myMaterial, 1)
        if self.appearance is not None:
            #TODO: should be done somewhere else
            self.appearance.bake()
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.schedule_jobs()

    def create_shadows(self):
        pass

    def start_shadows_update(self):
        self.shadows.start_update()

    def end_shadows_update(self):
        self.shadows.end_update()

    def add_shadow_target(self, target):
        if self.shadow_caster is None:
            self.create_shadows()
        if self.shadow_caster is not None:
            self.shadow_caster.add_target(target)

    def schedule_patch_jobs(self, patch):
        if self.appearance is not None:
            self.appearance.apply_patch(patch, self)

    def schedule_shape_jobs(self, shape):
        if self.appearance is not None:
            self.appearance.apply(shape, self)

    def schedule_jobs(self):
        if self.shape.patchable:
            for patch in self.shape.patches:
                if not patch.instance_ready:
                    self.schedule_patch_jobs(patch)
                    if patch.jobs_pending == 0:
                        self.jobs_done_cb(patch)
        if not self.shape.instance_ready:
            self.schedule_shape_jobs(self.shape)
            if self.shape.jobs_pending == 0:
                self.jobs_done_cb(None)

    def jobs_done_cb(self, patch):
        if patch is not None:
            patch.jobs_pending -= 1
            if patch.jobs_pending > 0: return
            patch.jobs_pending = 0
            patch.jobs = 0
            if patch.instance is not None:
                if self.first_patch:
                    if self.shader is not None:
                        self.shader.apply(self.shape, self.appearance)
                    self.first_patch = None
                if self.appearance is not None:
                    self.appearance.apply_textures(patch)
                if self.shader is not None:
                    self.shader.apply_patch(self.shape, patch, self.appearance)
                patch.instance_ready = True
                if self.callback is not None:
                    self.callback(self, patch, *self.cb_args)
        else:
            self.shape.jobs_pending -= 1
            if self.shape.jobs_pending > 0: return
            self.shape.jobs_pending = 0
            self.shape.jobs = 0
            if self.shape.instance is not None:
                if self.appearance is not None and not self.shape.patchable:
                    self.appearance.apply_textures(self.shape)
                if self.shader is not None:
                    self.shader.apply(self.shape, self.appearance)
                self.shape.instance_ready = True
                self.instance_ready = True
                if self.callback is not None:
                    self.callback(self, *self.cb_args)

    def check_visibility(self, pixel_size):
        self.visible = self.parent != None and self.parent.shown and self.parent.visible and self.parent.resolved

    def update_shader(self):
        if self.instance is not None and self.shader is not None and self.instance_ready:
            self.shader.apply(self.shape, self.appearance)

    def update_instance(self, camera_pos, orientation):
        if not self.instance_ready: return
        self.place_instance(self.instance, self.parent)
        if not self.shape.patchable and settings.offset_body_center and self.parent is not None:
            #TODO: Should be done in place_instance, but that would make several if...
            self.instance.setPos(*(self.parent.scene_position + self.parent.world_body_center_offset))
        if self.shape.patchable and settings.offset_body_center and self.parent is not None:
            #In case of oblate shape, the offset can not be used directly to retrieve the body center
            #The scale must be applied to the offset to retrieve the real center
            offset = self.shape.instance.getMat().xform(LVector3(*self.shape.owner.model_body_center_offset))
            self.parent.projected_world_body_center_offset = LVector3d(*offset.get_xyz())
        if self.shape.update_lod(self.context.observer.get_camera_pos(), self.parent.distance_to_obs, self.context.observer.pixel_size, self.appearance):
            self.schedule_jobs()
        if self.shape.patchable:
            self.shape.place_patches(self.parent)
        if self.appearance is not None:
            self.appearance.update_lod(self.shape, self.parent.get_apparent_radius(), self.parent.distance_to_obs, self.context.observer.pixel_size)
        if self.shadows.update_needed:
            self.update_shader()
            self.shadows.update_needed = False
        if self.shader is not None:
            self.shader.update(self.shape, self.appearance)

    def remove_instance(self):
        self.shadows.clear_shadows()
        self.shape.remove_instance()
        self.instance = None
        self.instance_ready = False

class MeshShape(Shape):
    deferred_instance = True
    def __init__(self, model, offset=None, scale_mesh=True, flatten=True, panda=False, attribution=None, context=defaultDirContext):
        Shape.__init__(self)
        self.model = model
        self.attribution = attribution
        self.context = context
        self.scale_factor = 1.0
        if offset is None:
            offset = LPoint3d()
        self.offset = offset
        self.scale_mesh = scale_mesh
        self.flatten = flatten
        self.panda = panda
        self.callback = None
        self.cb_args = None

    def is_spherical(self):
        return False

    def create_instance_cb(self, mesh):
        if mesh is None: return
        #The shape has been removed from the view while the mesh was loaded
        if self.instance is None: return
        if self.scale_mesh:
            (l, r) = mesh.getTightBounds()
            major = max(r - l) / 2
            self.scale_factor = 1.0 / major
        if self.flatten:
            mesh.flattenStrong()
        self.apply_owner()
        mesh.set_pos(*self.offset)
        mesh.set_scale(self.scale_factor, self.scale_factor, self.scale_factor)
        mesh.reparent_to(self.instance)
        self.parent.apply_instance(self.instance)
        if self.callback is not None:
            self.callback(self, *self.cb_args)

    def create_instance(self, callback=None, cb_args=()):
        self.callback = callback
        self.cb_args = cb_args
        self.instance = NodePath('holder')
        if self.panda:
            load_panda_model(self.model, self.create_instance_cb)
        else:
            load_model(self.model, self.create_instance_cb, self.context)
        return self.instance

class InstanceShape(Shape):
    deferred_instance = True
    def __init__(self, instance):
        Shape.__init__(self)
        self.instance = instance
        bounds = self.instance.getTightBounds()
        if bounds is not None:
            (l, r) = bounds
            self.radius = max(r - l) / 2
        else:
            self.radius = 0

    def create_instance(self, callback=None):
        self.apply_owner()
        self.parent.apply_instance(self.instance)
        if callback is not None:
            callback(self)
        return self.instance

    def get_apparent_radius(self):
        return self.radius

    def get_scale(self):
        return LVecBase3(1.0, 1.0, 1.0)

class SphereShape(Shape):
    template = None
    def create_instance(self):
        if self.template is None:
            self.template = geometry.UVSphere(radius=1, rings=45, sectors=90)
        self.instance = NodePath('shpere')
        self.template.instanceTo(self.instance)
        if self.use_collision_solid:
            self.create_collision_solid()
        self.apply_owner()
        return self.instance

class IcoSphereShape(Shape):
    template = None
    def __init__(self, subdivisions=3):
        Shape.__init__(self)
        self.subdivisions = subdivisions

    def create_instance(self):
        if self.template is None:
            self.template = geometry.IcoSphere(radius=1, subdivisions=self.subdivisions)
        self.instance = NodePath('icoshpere')
        self.template.instanceTo(self.instance)
        if self.use_collision_solid:
            self.create_collision_solid()
        self.apply_owner()
        return self.instance

class DisplacementSphereShape(Shape):
    def __init__(self, heightmap, max_height):
        Shape.__init__(self)
        self.heightmap = heightmap
        self.max_height = max_height

    def create_instance(self):
        print(self.radius, self.max_height)
        self.instance = geometry.DisplacementUVSphere(radius=1.0,
                                                      heightmap=self.heightmap,
                                                      scale=self.max_height/self.radius,
                                                      rings=45, sectors=90)
        if self.use_collision_solid:
            self.create_collision_solid()
        self.apply_owner()
        return self.instance

class ScaledSphereShape(Shape):
    def __init__(self, radius=1.0, inv_texture_u=False, inv_texture_v=False):
        Shape.__init__(self)
        self.radius = radius
        self.inv_u = inv_texture_u
        self.inv_v = inv_texture_v

    def create_instance(self):
        self.instance=geometry.UVSphere(radius=self.radius, rings=45, sectors=90)
        if self.use_collision_solid:
            self.create_collision_solid(self.radius)
        return self.instance

class RingShape(Shape):
    def __init__(self, inner_radius, outer_radius):
        Shape.__init__(self)
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.nbOfPoints = 360

    def is_spherical(self):
        return False

    def create_instance(self):
        self.instance = NodePath("ring")
        node = GeomNode('ring-up')
        node.addGeom(geometry.RingFaceGeometry(1.0, self.inner_radius, self.outer_radius, self.nbOfPoints))
        up = self.instance.attach_new_node(node)
        up.setDepthOffset(-1)
        node = GeomNode('ring-down')
        node.addGeom(geometry.RingFaceGeometry(-1.0, self.inner_radius, self.outer_radius, self.nbOfPoints))
        down = self.instance.attach_new_node(node)
        down.setDepthOffset(-1)
        self.apply_owner()
        self.instance.set_depth_write(False)
        return self.instance
