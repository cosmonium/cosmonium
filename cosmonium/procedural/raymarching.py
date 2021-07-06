#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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


from panda3d.core import LVecBase3
from panda3d.core import CardMaker, NodePath, OmniBoundingVolume

from ..shapes import Shape
from ..shaders import ShaderAppearance
from ..utils import TransparencyBlend, srgb_to_linear_channel
from ..appearances import AppearanceBase
from ..parameters import AutoUserParameter, ParametersGroup
from .. import settings

from .shadernoise import NoiseSource

from math import asin, cos

class RayMarchingShape(Shape):
    templates = {}
    def __init__(self, radius=1.0, scale=None):
        Shape.__init__(self)
        self.radius = radius
        if scale is None:
            self.radius = radius
            self.scale = LVecBase3(self.radius, self.radius, self.radius)
        else:
            self.scale = LVecBase3(*scale) * radius
            self.radius = max(scale) * radius
        self.blend = TransparencyBlend.TB_PremultipliedAlpha
        self.scale_factor = 1.0

    def shape_id(self):
        return ''

    def get_apparent_radius(self):
        return self.radius

    async def create_instance(self):
        self.instance = NodePath("card")
        card_maker = CardMaker("card")
        card_maker.set_frame(-1, 1, -1, 1)
        node = card_maker.generate()
        self.card_instance = self.instance.attach_new_node(node)
        self.card_instance.setBillboardPointWorld()
        TransparencyBlend.apply(self.blend, self.instance)
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        return self.instance

    def get_scale(self):
        return Shape.get_scale(self) * self.scale_factor

    def update_instance(self, camera_pos, orientation):
        alpha = asin(self.radius / self.owner.anchor.distance_to_obs)
        self.scale_factor = 1.0 / cos(alpha)

class RayMarchingAppearance(AppearanceBase):
    def __init__(self, density_coef, density_power,
                 absorption_factor, absorption_coef,
                 mie_coef, phase_coef,
                 source_power, emission_power, max_steps):
        AppearanceBase.__init__(self)
        self.density_coef = density_coef
        self.density_power = density_power
        self.absorption_factor = absorption_factor
        self.absorption_coef = absorption_coef
        self.mie_coef = mie_coef
        self.phase_coef = phase_coef
        self.source_color = [1.0, 1.0, 1.0]
        self.source_power = source_power
        self.max_steps = max_steps
        self.emission_color = [1.0, 1.0, 1.0]
        self.emission_power = emission_power
        self.emissionColor = None
        self.hdr = False
        self.exposure = 4.0

class RayMarchingShader(ShaderAppearance):
    use_vertex = True
    world_vertex = True

    def __init__(self, shader=None):
        ShaderAppearance.__init__(self, shader)
        self.hdr = False
        self.exposure = 4.0
        self.max_steps = 64
        self.has_surface = True

    def get_id(self):
        name = 'ray'
        if settings.shader_debug_raymarching_canvas:
            name += '-hit'
        if settings.shader_debug_raymarching_slice:
            name += "-slice"
        if self.hdr:
            name += '-hdr'
        return name

    def ray_sphere_intersection(self, code):
        code.append('''
bool raySphereIntersection(float radius, vec3 origin, vec3 direction, out float t0, out float t1)
{
    float A = 1.0;
    float B = 2.0 * dot(origin, direction);
    float C = dot(origin, origin) - (radius * radius);

    float D = B * B - 4.0 * A * C;
    if (D < 0.0) {
        return false;
    }  else {
        float sqrtD = sqrt(D);
        t0 = (-B - sqrtD) / (2.0 * A);
        t1 = (-B + sqrtD) / (2.0 * A);
        return true;
    }
}
''')
    def fragment_extra(self, code):
        self.shader.fragment_shader.add_function(code, 'raySphereIntersection', self.ray_sphere_intersection)

    def fragment_uniforms(self, code):
        ShaderAppearance.fragment_uniforms(self, code)
        code.append("uniform vec3 center;")
        code.append("uniform vec3 origin;")
        code.append("uniform float radius;")
        code.append("uniform float scene_scale;")
        code.append("uniform int max_steps;")
        code.append("uniform float exposure;")

    def extra_condition(self):
        return ''

    def loop_init(self, code):
        pass

    def loop_done(self, code):
        pass

    def fragment_shader(self, code):
        if settings.shader_debug_raymarching_canvas:
            code.append("surface_color = vec4(0, 0, 1, 1);")
        else:
            code.append("surface_color = vec4(0, 0, 0, 0);")
        code.append("vec3 ray_dir = normalize((world_vertex * scene_scale - center) - origin);")
        code.append("float t0 = 0.0;")
        code.append("float t1 = 0.0;")
        code.append("if (raySphereIntersection(radius, origin, ray_dir, t0, t1)) {")
        code.append("  float t = max(0.0, t0);")
        self.loop_init(code)
        code.append("  for (int i = 0; i < max_steps && t < t1 %s; ++i) {" % self.extra_condition())
        code.append("    vec3 pos = origin + t * ray_dir;")
        self.perform_step(code)
        code.append("    t += step;")
        code.append("  }")
        self.loop_done(code)
        if self.hdr:
            code.append("  surface_color.rgb = 1.0 - exp(surface_color.rgb * -exposure);")
        code.append("} else {")
        if settings.shader_debug_raymarching_canvas:
            code.append("  surface_color = vec4(1, 0, 0, 1);")
        else:
            code.append("  discard;")
        code.append("}")

    def update_shader_shape_static(self, shape, appearance):
        shape.instance.setShaderInput("max_steps", int(self.max_steps))
        shape.instance.setShaderInput("exposure", self.exposure)

    def update_shader_shape(self, shape, appearance):
        pos = shape.owner.anchor.rel_position
        shape.instance.setShaderInput("radius", shape.owner.get_apparent_radius())
        shape.instance.setShaderInput("center", pos)
        shape.instance.setShaderInput("origin", -pos)
        shape.instance.setShaderInput("scene_scale", settings.scale)

    def get_user_parameters(self):
        group = ParametersGroup('Raymarching',
                AutoUserParameter('Steps', 'max_steps', self, AutoUserParameter.TYPE_INT, [1, 256]),
                AutoUserParameter('HDR', 'hdr', self, AutoUserParameter.TYPE_BOOL),
                AutoUserParameter('Exposure', 'exposure', self, AutoUserParameter.TYPE_FLOAT, [0, 10]),
                )
        return group

class SDFRayMarchingShader(RayMarchingShader):
    def __init__(self, shape, shader=None):
        RayMarchingShader.__init__(self, shader)
        self.shape = shape

    def get_id(self):
        name = RayMarchingShader.get_id(self)
        name += "-sdf-" + self.shape.get_id()
        return name

    def fragment_extra(self, code):
        RayMarchingShader.fragment_extra(self, code)
        self.shape.noise_extra(self, code)
        self.shape.noise_func(code)

    def perform_step(self, code):
        code.append("    float d;")
        self.shape.noise_value(code, 'd', 'pos / radius')
        code.append("    if (abs(d) < 0.0001 * t) {")
        code.append("      surface_color = vec4(0, 1, 0, 1);")
        code.append("      break;")
        code.append("    }")
        code.append("    float step = d;")

class BulgeRayMarchingShader(RayMarchingShader):
    def __init__(self, shader=None):
        RayMarchingShader.__init__(self, shader)
        self.effective_intensity = 0.001
        self.effective_radius = 0.5
        self.emissive_color = [1, 1, 1]
        self.emissive_scale = 1.0

    def get_id(self):
        name = RayMarchingShader.get_id(self)
        name += "-bulge"
        return name

    def fragment_uniforms(self, code):
        RayMarchingShader.fragment_uniforms(self, code)
        code.append("uniform float effective_intensity;")
        code.append("uniform float effective_radius;")
        code.append("uniform vec3 emissive_color;")
        code.append("uniform float emissive_scale;")

    def perform_step(self, code):
        code.append("    float d = length(pos) / radius / effective_radius;")
        code.append("    float v = effective_intensity * (pow(d, -0.855) * exp(-pow(d, 0.25)));// * step;")
        code.append("    surface_color.rgb += emissive_color * v;")

    def loop_done(self, code):
        RayMarchingShader.loop_done(self, code)
        code.append("    surface_color.rgb *= emissive_scale;")

    def update_shader_shape_static(self, shape, appearance):
        RayMarchingShader.update_shader_shape_static(self, shape, appearance)
        shape.instance.setShaderInput("effective_intensity", self.effective_intensity)
        shape.instance.setShaderInput("effective_radius", self.effective_radius)
        shape.instance.setShaderInput("emissive_color", self.emissive_color)
        shape.instance.setShaderInput("emissive_scale", self.emissive_scale)

    def get_user_parameters(self):
        group = RayMarchingShader.get_user_parameters(self)
        group.add_parameters(
                AutoUserParameter('Effective intensity', 'effective_intensity', self, AutoUserParameter.TYPE_FLOAT, [1e-10, 1e10], AutoUserParameter.SCALE_LOG),
                AutoUserParameter('Effective radius', 'effective_radius', self, AutoUserParameter.TYPE_FLOAT, [0, 1]),
                AutoUserParameter('Emissive color', 'emissive_color', self, AutoUserParameter.TYPE_VEC, [0, 1], nb_components=3),
                AutoUserParameter('Emissive scale', 'emissive_scale', self, AutoUserParameter.TYPE_FLOAT, [0, 1]),
                )
        return group

class SDFShapeBase(NoiseSource):
    pass

class SDFPointShape(SDFShapeBase):
    def __init__(self, position, dynamic=True, name=None, ranges={}):
        SDFShapeBase.__init__(self, name, 'point', ranges)
        self.position = position
        self.dynamic = dynamic

    def noise_uniforms(self, code):
        if self.dynamic:
            code.append("uniform vec3 %s;" % self.str_id)

    def noise_value(self, code, value, point):
        if self.dynamic:
            code.append('        %s  = length(%s - %s);' % (value, point, self.str_id))
        else:
            code.append('        %s  = length(%s - vec3(%s));' % (value, point, ', '.join(map(str, self.position))))

    def update(self, instance):
        if self.dynamic:
            instance.set_shader_input('%s' % self.str_id, self.position)

class SDFSphereShape(SDFShapeBase):
    def __init__(self, position, radius, dynamic=True, name=None, ranges={}):
        SDFShapeBase.__init__(self, name, 'sphere', ranges)
        self.position = position
        self.radius = radius
        self.dynamic = dynamic

    def noise_uniforms(self, code):
        if self.dynamic:
            code.append("uniform vec3 %s_position;" % self.str_id)
            code.append("uniform float %s_radius;" % self.str_id)

    def noise_value(self, code, value, point):
        if self.dynamic:
            code.append('        %s  = length(%s - %s_position) - %s_radius;' % (value, point, self.str_id, self.str_id))
        else:
            code.append('        %s  = length(%s - vec3(%s)) - %g;' % (value, point, ', '.join(map(str, self.position)), self.radius))

    def update(self, instance):
        if self.dynamic:
            instance.set_shader_input('%s_position' % self.str_id, self.position)
            instance.set_shader_input('%s_radius' % self.str_id, self.radius)

    def get_user_parameters(self):
        if not self.dynamic: return []
        group = ParametersGroup(self.name)
        group.add_parameters(AutoUserParameter('radius', 'radius', self, param_type=AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('radius')))
        return [group]

class VolumetricDensityRayMarchingShaderBase(RayMarchingShader):
    def __init__(self, density, shader=None):
        RayMarchingShader.__init__(self, shader)
        self.density = density

    def get_id(self):
        name = RayMarchingShader.get_id(self)
        name += "-vol-" + self.density.get_id()
        return name

    def fragment_uniforms(self, code):
        RayMarchingShader.fragment_uniforms(self, code)
        self.density.noise_uniforms(code)

    def fragment_extra(self, code):
        RayMarchingShader.fragment_extra(self, code)
        self.density.noise_extra(self.shader.fragment_shader, code)
        self.density.noise_func(code)

    def perform_scattering(self, code):
        pass

    def loop_init(self, code):
        RayMarchingShader.loop_init(self, code)
        code.append("  float min_step_size = 2 * radius / max_steps;")
        code.append("  float step = max((t1 - t0) / max_steps, min_step_size);")

    def perform_step(self, code):
        code.append('    float density;')
        code.append('    bool skip = false;')
        self.density.noise_value(code, 'density', 'pos / radius')
        if settings.shader_debug_raymarching_slice:
            code.append("    if (pos.z < 0 || pos.y < 0) skip = true;")
        code.append("        float light_source_squared_distance = dot(pos, pos);")
        code.append("        float light_source_distance = sqrt(light_source_squared_distance) / radius;")
        code.append("    if (!skip && density > 0.0) {")
        self.perform_scattering(code)
        code.append("    }")

    def update_shader_shape_static(self, shape, appearance):
        RayMarchingShader.update_shader_shape_static(self, shape, appearance)
        self.density.update(shape.instance)

    def get_user_parameters(self):
        group = RayMarchingShader.get_user_parameters(self)
        group.add_parameters(self.density.get_user_parameters())
        return group

class VolumetricDensityRayMarchingShader(VolumetricDensityRayMarchingShaderBase):
    def __init__(self, density, shader=None):
        VolumetricDensityRayMarchingShaderBase.__init__(self, density, shader)
        self.absorption_factor = [0, 0, 0]
        self.absorption_coef = 0
        self.mie_coef = 0
        self.phase_coef = 0
        self.source_color = [1.0, 1.0, 1.0]
        self.source_power = 0
        self.emission_color = [1.0, 1.0, 1.0]
        self.emission_power = 0
        self.emissionColor = None

    def fragment_uniforms(self, code):
        VolumetricDensityRayMarchingShaderBase.fragment_uniforms(self, code)
        code.append("uniform vec3 absorption_coef;")
        code.append("uniform float mie_coef;")
        code.append("uniform vec3 source_color;")
        code.append("uniform float source_power;")
        code.append("uniform vec3 emission_color;")
        code.append("uniform float emission_power;")
        code.append("uniform float phase_asymmetry_factor;")

    def fragment_extra(self, code):
        VolumetricDensityRayMarchingShaderBase.fragment_extra(self, code)
        code .append('''
//Henyey-Greenstein phase function
float hg_phase_func(float mu, float g)
{
    float g2 = g * g;
    return (1.0 - g2) / (4.0 * pi *pow(1.0 + g2 - 2.0 * g * mu, 1.5));
}

//Cornette-Shanks phase function
float cs_phase_func(float mu, float g)
{
    float g2 = g * g;
    return (3.0 * (1.0 - g2) * (1.0 + mu * mu)) / (2.0 * (2.0 + g2) * pow(1.0 + g2 - 2.0 * g * mu, 1.5));
}
''')

    def loop_init(self, code):
        VolumetricDensityRayMarchingShaderBase.loop_init(self, code)
        code.append("  vec3 total_luminance = vec3(0.0);")
        code.append("  vec3 total_transmittance = vec3(1.0);")
        code.append("  float acc_transmittance = 1.0;")

    def extra_condition(self):
        return VolumetricDensityRayMarchingShaderBase.extra_condition(self) + "&& acc_transmittance > 1.0/255"

    def perform_scattering(self, code):
        code.append("        float attenuation = radius * radius / light_source_squared_distance;")
        code.append("        vec3 light_source_dir = -pos /radius / light_source_distance;")
        code.append("        //vec3 sigma_a = clamp(density * absorption_coef, 0, 1);")
        code.append("        //float sigma_s = clamp(density * mie_coef, 0, 1);")
        code.append("        vec3 sigma_a = density * absorption_coef;")
        code.append("        float sigma_s = density * mie_coef;")
        code.append("        vec3 sigma_e = max(vec3(1e-12), sigma_a + vec3(sigma_s));")
        code.append("        vec3 optical_depth = sigma_e * step / radius;")
        code.append("        //vec3 transmittance = clamp(exp(-optical_depth), 0, 1);")
        code.append("        vec3 transmittance = exp(-optical_depth);")
        #TODO: Add phase function selection
        code.append("        float phase = hg_phase_func(dot(light_source_dir, -ray_dir), phase_asymmetry_factor);")
        code.append("        vec3 light_emission_radiance = emission_color * emission_power;// * density;")
        code.append("        vec3 light_source_radiance = source_color * source_power * attenuation;")
        #TODO: Actual source shading should be also raymarched
        code.append("        vec3 shading = 1.0 - absorption_coef;")
        code.append("        vec3 illumination = light_emission_radiance + light_source_radiance * sigma_s * phase * shading;")
        code.append("        vec3 integrated_luminance = illumination * ( 1.0 - transmittance) / sigma_e;")
        code.append("        total_luminance += integrated_luminance * acc_transmittance;")
        code.append("        total_transmittance *= transmittance;")
        code.append("        acc_transmittance *= dot(transmittance, vec3(1.0/3));")

    def loop_done(self, code):
        VolumetricDensityRayMarchingShaderBase.loop_done(self, code)
        code.append("  surface_color = vec4(total_luminance * (1 - acc_transmittance), acc_transmittance);")

    def update_shader_shape_static(self, shape, appearance):
        VolumetricDensityRayMarchingShaderBase.update_shader_shape_static(self, shape, appearance)
        shape.instance.setShaderInput("source_color", self.source_color)
        shape.instance.setShaderInput("source_power", self.source_power)
        shape.instance.setShaderInput("emission_color", srgb_to_linear_channel(self.emission_color[0]),
                                                        srgb_to_linear_channel(self.emission_color[1]),
                                                        srgb_to_linear_channel(self.emission_color[2]))
        shape.instance.setShaderInput("emission_power", self.emission_power )
        shape.instance.setShaderInput("absorption_coef", LVecBase3(*self.absorption_coef) * self.absorption_factor)
        shape.instance.setShaderInput("mie_coef", self.mie_coef)
        shape.instance.setShaderInput("phase_asymmetry_factor", self.phase_coef)

    def get_user_parameters(self):
        group = VolumetricDensityRayMarchingShaderBase.get_user_parameters(self)
        group.add_parameters(
                AutoUserParameter('Absorption factor', 'absorption_factor', self, AutoUserParameter.TYPE_FLOAT, [0, 100], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-10),
                AutoUserParameter('Absorption coef', 'absorption_coef', self, AutoUserParameter.TYPE_VEC, [0, 1], nb_components=3),
                AutoUserParameter('Mie coef', 'mie_coef', self, AutoUserParameter.TYPE_FLOAT, [0, 100], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-10),
                AutoUserParameter('Phase', 'phase_coef', self, AutoUserParameter.TYPE_FLOAT, [0, 1]),
                AutoUserParameter('Source power', 'source_power', self, AutoUserParameter.TYPE_FLOAT, [0, 1e15], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-15),
                AutoUserParameter('Source color', 'source_color', self, AutoUserParameter.TYPE_VEC, [0, 1], nb_components=3),
                AutoUserParameter('Emission power', 'emission_power', self, AutoUserParameter.TYPE_FLOAT, [0, 1e10], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-15),
                AutoUserParameter('Emission color', 'emission_color', self, AutoUserParameter.TYPE_VEC, [0, 1], nb_components=3),
                )
        return group

class VolumetricDensityEmissiveRayMarchingShader(VolumetricDensityRayMarchingShaderBase):
    def __init__(self, density, shader=None):
        VolumetricDensityRayMarchingShaderBase.__init__(self, density, shader)
        self.emission_color = [1.0, 1.0, 1.0]
        self.emission_power = 0
        self.emissionColor = None

    def get_id(self):
        name = RayMarchingShader.get_id(self)
        name += "-emissive"
        return name

    def fragment_uniforms(self, code):
        VolumetricDensityRayMarchingShaderBase.fragment_uniforms(self, code)
        code.append("uniform vec3 emission_color;")
        code.append("uniform float emission_power;")
        code.append("uniform float phase_asymmetry_factor;")

    def perform_scattering(self, code):
        code.append("        vec3 light_emission_radiance = emission_color * emission_power * density * step / radius;")
        code.append("        surface_color.rgb += light_emission_radiance;")

    def update_shader_shape_static(self, shape, appearance):
        VolumetricDensityRayMarchingShaderBase.update_shader_shape_static(self, shape, appearance)
        shape.instance.setShaderInput("emission_color", srgb_to_linear_channel(self.emission_color[0]),
                                                        srgb_to_linear_channel(self.emission_color[1]),
                                                        srgb_to_linear_channel(self.emission_color[2]))
        shape.instance.setShaderInput("emission_power", self.emission_power )

    def get_user_parameters(self):
        group = VolumetricDensityRayMarchingShaderBase.get_user_parameters(self)
        group.add_parameters(
                AutoUserParameter('Emission power', 'emission_power', self, AutoUserParameter.TYPE_FLOAT, [0, 1e10], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-15),
                AutoUserParameter('Emission color', 'emission_color', self, AutoUserParameter.TYPE_VEC, [0, 1], nb_components=3),
                )
        return group
