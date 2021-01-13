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

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import Texture, LVector3d, LPoint3, LMatrix4, LQuaternion

from .bodyelements import Atmosphere
from .shaders import StructuredShader, ShaderProgram, BasicShader, LightingModel, AtmosphericScattering
from .utils import TransparencyBlend
from .parameters import AutoUserParameter, UserParameter
from .procedural.generator import GeneratorVertexShader, RenderTarget, RenderStage

from math import pow, pi

class ONeilAtmosphereBase(Atmosphere):
    def __init__(self, shape, appearance, shader):
        Atmosphere.__init__(self, shape, appearance, shader)
        self.blend = TransparencyBlend.TB_Alpha

    def update_shader_params(self):
        self.shader.scattering.set_inside(self.inside)

    def do_update_scattering(self, shape_object, atmosphere, extinction):
        shape_object.shader.scattering.set_inside(self.inside)
        if atmosphere:
            shape_object.shader.scattering.set_hdr(self.atm_hdr)
        else:
            shape_object.shader.scattering.set_hdr(self.hdr)
        shape_object.shader.scattering.set_extinction_only(extinction)

class ONeilSimpleAtmosphere(ONeilAtmosphereBase):
    AtmosphereRatio = 1.025
    ScaleDepth = 0.25
    def __init__(self,
                 shape,
                 wavelength,
                 mie_phase_asymmetry,
                 rayleigh_coef,
                 mie_coef,
                 sun_power,
                 samples,
                 exposure,
                 calc_in_fragment,
                 atm_calc_in_fragment,
                 normalize,
                 atm_normalize,
                 hdr,
                 atm_hdr,
                 appearance):
        ONeilAtmosphereBase.__init__(self, shape, appearance, None)
        self.wavelength = wavelength
        self.G = mie_phase_asymmetry
        self.Kr = rayleigh_coef
        self.Km = mie_coef
        self.ESun = sun_power
        self.samples = samples
        self.exposure = exposure
        self.calc_in_fragment = calc_in_fragment
        self.atm_calc_in_fragment = atm_calc_in_fragment
        self.normalize = normalize
        self.atm_normalize = atm_normalize
        self.hdr = hdr
        self.atm_hdr = atm_hdr
        shader = BasicShader(lighting_model=LightingModel(), scattering=self.create_scattering_shader(atmosphere=True, displacement=False, extinction=False))
        self.set_shader(shader)

    def set_parent(self, parent):
        Atmosphere.set_parent(self, parent)
        if parent is not None:
            self.planet = parent
            self.planet_radius = parent.get_min_radius()
            self.radius = self.planet_radius * self.AtmosphereRatio
            self.ratio = self.AtmosphereRatio

    def create_scattering_shader(self, atmosphere, displacement, extinction):
        if atmosphere:
            scattering = ONeilSimpleScattering(self, atmosphere=True, extinction_only=False, calc_in_fragment=self.atm_calc_in_fragment, normalize=self.atm_normalize, displacement=False, hdr=self.atm_hdr)
        else:
            scattering = ONeilSimpleScattering(self, atmosphere=False, extinction_only=extinction, calc_in_fragment=self.calc_in_fragment, normalize=self.normalize, displacement=displacement, hdr=self.hdr)
        scattering.inside = self.inside
        return scattering

    def get_user_parameters(self):
        group = Atmosphere.get_user_parameters(self)
        group.add_parameters(
                             AutoUserParameter('Rayleigh coef', 'Kr', self, AutoUserParameter.TYPE_FLOAT, [0, 1.0], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-6),
                             AutoUserParameter('Mie coef', 'Km', self, AutoUserParameter.TYPE_FLOAT, [0, 1.0], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-6),
                             AutoUserParameter('Phase asymmetry', 'G', self, AutoUserParameter.TYPE_FLOAT, [-1.0, 1.0]),
                             AutoUserParameter('Source power', 'ESun', self, AutoUserParameter.TYPE_FLOAT, [0, 100]),
                             AutoUserParameter('Exposure', 'exposure', self, AutoUserParameter.TYPE_FLOAT, [0, 10]),
                             AutoUserParameter('HDR', 'hdr', self, AutoUserParameter.TYPE_BOOL),
                             AutoUserParameter('Atmosphere HDR', 'atm_hdr', self, AutoUserParameter.TYPE_BOOL),
                            )
        return group

class ONeilAtmosphere(ONeilAtmosphereBase):
    lookuptable_generators = {}

    def __init__(self,
                 shape,
                 height,
                 wavelength,
                 mie_phase_asymmetry,
                 rayleigh_scale_depth,
                 rayleigh_coef,
                 rayleigh_absorption,
                 mie_scale_depth,
                 mie_alpha_coef,
                 mie_beta_coef,
                 sun_power,
                 samples,
                 exposure,
                 calc_in_fragment,
                 atm_calc_in_fragment,
                 normalize,
                 atm_normalize,
                 hdr,
                 atm_hdr,
                 lookup_size,
                 lookup_samples,
                 appearance):
        ONeilAtmosphereBase.__init__(self, shape, appearance, None)
        self.wavelength = wavelength
        self.G = mie_phase_asymmetry
        self.rayleigh_scale_depth = rayleigh_scale_depth
        self.Kr = rayleigh_coef
        self.rayleigh_absorption = rayleigh_absorption
        self.mie_scale_depth = mie_scale_depth
        self.Km_alpha = mie_alpha_coef
        self.Km_beta = mie_beta_coef
        self.ESun = sun_power
        self.samples = samples
        self.exposure = exposure
        self.calc_in_fragment = calc_in_fragment
        self.atm_calc_in_fragment = atm_calc_in_fragment
        self.normalize = normalize
        self.atm_normalize = atm_normalize
        self.hdr = hdr
        self.atm_hdr = atm_hdr
        self.height = height
        self.lookup_size = lookup_size
        self.lookup_samples = lookup_samples
        self.pbOpticalDepth = None
        shader = BasicShader(lighting_model=LightingModel(), scattering=self.create_scattering_shader(atmosphere=True, displacement=False, extinction=False))
        self.set_shader(shader)

    @classmethod
    def get_generator(cls, size):
        if not size in cls.lookuptable_generators:
            stage = ONeilLookupTableRenderStage(size)
            stage.create()
            cls.lookuptable_generators[size] = stage
        tex_generator = cls.lookuptable_generators[size]
        return tex_generator

    def set_parent(self, parent):
        Atmosphere.set_parent(self, parent)
        if parent is not None:
            self.planet = parent
            self.planet_radius = parent.get_average_radius()
            self.radius = self.planet_radius + self.height
            self.ratio = self.radius / self.planet_radius

    def create_scattering_shader(self, atmosphere, displacement, extinction):
        if atmosphere:
            scattering = ONeilScattering(self, atmosphere=True, extinction_only=False, calc_in_fragment=self.atm_calc_in_fragment, normalize=self.atm_normalize, displacement=False, hdr=self.atm_hdr)
        else:
            scattering = ONeilScattering(self, atmosphere=False, extinction_only=extinction, calc_in_fragment=self.calc_in_fragment, normalize=self.normalize, displacement=displacement, hdr=self.hdr)
        scattering.inside = self.inside
        return scattering

    def generate_lookup_table(self):
        lookuptable_generator = self.get_generator(self.lookup_size)
        self.pbOpticalDepth = Texture()
        self.pbOpticalDepth.setWrapU(Texture.WM_clamp)
        self.pbOpticalDepth.setWrapV(Texture.WM_clamp)
        self.pbOpticalDepth.setMinfilter(Texture.FT_linear)
        self.pbOpticalDepth.setMagfilter(Texture.FT_linear)

        lookuptable_generator.prepare({'parameters': self}, self.pbOpticalDepth)

    def get_lookup_table(self):
        if self.pbOpticalDepth is None:
            self.generate_lookup_table()
        return self.pbOpticalDepth

    def set_rayleigh_scale_depth(self, rayleigh_scale_depth):
        self.rayleigh_scale_depth = rayleigh_scale_depth / self.height
        self.generate_lookup_table()

    def get_rayleigh_scale_depth(self):
        return self.rayleigh_scale_depth * self.height

    def set_mie_scale_depth(self, mie_scale_depth):
        self.mie_scale_depth = mie_scale_depth / self.height
        self.generate_lookup_table()

    def get_mie_scale_depth(self):
        return self.mie_scale_depth * self.height

    def get_user_parameters(self):
        group = Atmosphere.get_user_parameters(self)
        group.add_parameters(
                             UserParameter('Rayleigh scale depth', self.set_rayleigh_scale_depth, self.get_rayleigh_scale_depth, UserParameter.TYPE_FLOAT, [0, self.height]),
                             AutoUserParameter('Rayleigh coef', 'Kr', self, AutoUserParameter.TYPE_FLOAT, [0, 1.0], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-6),
                             AutoUserParameter('Rayleigh absorption', 'rayleigh_absorption', self, AutoUserParameter.TYPE_VEC, [0, 100.0], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-6, nb_components=3),
                             UserParameter('Mie scale depth', self.set_mie_scale_depth, self.get_mie_scale_depth, UserParameter.TYPE_FLOAT, [0, self.height]),
                             AutoUserParameter('Mie alpha coef', 'Km_alpha', self, AutoUserParameter.TYPE_FLOAT, [-4.0, 4.0]),
                             AutoUserParameter('Mie beta coef', 'Km_beta', self, AutoUserParameter.TYPE_FLOAT, [0, 1.0], AutoUserParameter.SCALE_LOG_0, value_range_0=1e-6),
                             AutoUserParameter('Phase asymmetry', 'G', self, AutoUserParameter.TYPE_FLOAT, [-1.0, 1.0]),
                             AutoUserParameter('Source power', 'ESun', self, AutoUserParameter.TYPE_FLOAT, [0, 100]),
                             AutoUserParameter('Samples', 'samples', self, AutoUserParameter.TYPE_INT, [0, 64]),
                             AutoUserParameter('Exposure', 'exposure', self, AutoUserParameter.TYPE_FLOAT, [0, 10]),
                             AutoUserParameter('HDR', 'hdr', self, AutoUserParameter.TYPE_BOOL),
                             AutoUserParameter('Atmosphere HDR', 'atm_hdr', self, AutoUserParameter.TYPE_BOOL),
                            )
        return group

class ONeilScatteringBase(AtmosphericScattering):
    use_vertex = True
    world_vertex = True
    str_id = None

    def __init__(self, parameters, atmosphere=False, extinction_only=False, calc_in_fragment=False, normalize=False, displacement=False, hdr=False):
        AtmosphericScattering.__init__(self)
        self.parameters = parameters
        self.atmosphere = atmosphere
        self.extinction_only = extinction_only
        self.calc_in_fragment = calc_in_fragment
        self.use_vertex_frag = calc_in_fragment
        self.normalize = normalize
        self.displacement = displacement
        self.hdr = hdr
        self.use_normal = False#not self.atmosphere
        self.inside = False

    def set_parameters(self, parameters):
        self.parameters = parameters

    def set_inside(self, inside):
        self.inside = inside

    def set_hdr(self, hdr):
        self.hdr = hdr

    def set_extinction_only(self, extinction_only):
        self.extinction_only = extinction_only

    def get_id(self):
        name = self.str_id
        if self.atmosphere:
            name += "-sky"
        else:
            name += "-ground"
        if self.inside:
            name += '-inside'
        if self.calc_in_fragment:
            name += "-infrag"
        if self.hdr:
            name += "-hdr"
        if self.normalize:
            name += "-norm"
            if self.displacement:
                name += '-disp'
        if self.extinction_only:
            name += "-ext"
        return name

    def uniforms_colors(self, code):
        if not self.calc_in_fragment:
            code.append("uniform vec3 v3LightPos;")
        if self.atmosphere:
            code.append("uniform float fg;")
            code.append("uniform float fg2;")
        code.append("uniform float fExposure;")
        code.append("uniform float global_ambient;")

    def vertex_uniforms(self, code):
        if not self.calc_in_fragment:
            self.uniforms_scattering(code)

    def vertex_outputs(self, code):
        if not self.calc_in_fragment:
            code.append("out vec3 rayleigh_inscattering;")
            code.append("out vec3 mie_inscattering;")
            code.append("out vec3 transmittance;")
            if self.atmosphere:
                code.append("out vec3 v3Direction;")

    def fragment_uniforms(self, code):
        if self.calc_in_fragment:
            self.uniforms_scattering(code)
        self.uniforms_colors(code)

    def fragment_inputs(self, code):
        if not self.calc_in_fragment:
            code.append("in vec3 rayleigh_inscattering;")
            code.append("in vec3 mie_inscattering;")
            code.append("in vec3 transmittance;")
            if self.atmosphere:
                code.append("in vec3 v3Direction;")

    def vertex_shader(self, code):
        if not self.calc_in_fragment:
            self.calc_scattering(code)

    def calc_colors(self, code):
        if self.atmosphere:
            code.append("    float fCos = dot(v3LightPos, v3Direction) / length(v3Direction);")
            code.append("    float fRayleighPhase = 0.75 * (1.0 + fCos*fCos);")
            code.append("    float fMiePhase = 1.5 * ((1.0 - fg2) / (2.0 + fg2)) * (1.0 + fCos*fCos) / pow(1.0 + fg2 - 2.0*fg*fCos, 1.5);")
            code.append("    total_diffuse_color.rgb = shadow * (fRayleighPhase * rayleigh_inscattering + fMiePhase * mie_inscattering);")
            if self.hdr:
                code.append("    total_diffuse_color.rgb = 1.0 -exp(total_diffuse_color.rgb * -fExposure);")
            code.append("    total_diffuse_color.a = max(total_diffuse_color.r, max(total_diffuse_color.g, total_diffuse_color.b));")
        else:
            if self.extinction_only:
                code.append("  total_diffuse_color.rgb = total_diffuse_color.rgb * transmittance;")
            else:
                code.append("  total_diffuse_color.rgb = shadow * (rayleigh_inscattering + mie_inscattering) + total_diffuse_color.rgb * transmittance * (1.0 - global_ambient) + surface_color.rgb * global_ambient;")
            if self.hdr:
                code.append("  total_diffuse_color.rgb = 1.0 -exp(total_diffuse_color.rgb * -fExposure);")

    def fragment_shader(self, code):
        if self.calc_in_fragment:
            self.calc_scattering(code)
        self.calc_colors(code)

    def update_shader_shape(self, shape, appearance):
        planet = self.parameters.planet
        factor = 1.0 / shape.owner.scene_scale_factor
        inner_radius = self.parameters.planet_radius

        #TODO: We should get the oblateness correctly
        planet_scale = self.parameters.planet.surface.get_scale()
        descale = LMatrix4.scale_mat(inner_radius / planet_scale[0], inner_radius / planet_scale[1], inner_radius / planet_scale[2])
        rotation_mat = LMatrix4()
        orientation = LQuaternion(*shape.owner.scene_orientation)
        orientation.extract_to_matrix(rotation_mat)
        rotation_mat_inv = LMatrix4()
        rotation_mat_inv.invert_from(rotation_mat)
        descale_mat = rotation_mat_inv * descale * rotation_mat
        pos = planet.rel_position
        scaled_pos = descale_mat.xform_point(LPoint3(*pos))
        star_pos = planet.star._local_position - planet._local_position
        scaled_star_pos = descale_mat.xform_point(LPoint3(*star_pos))
        scaled_star_pos.normalize()
        camera_height = scaled_pos.length()
        if camera_height > inner_radius * 100:
            scaled_pos *= 100.0 * inner_radius / camera_height
            camera_height = 100.0 * inner_radius
        shape.instance.setShaderInput("v3OriginPos", pos)
        shape.instance.setShaderInput("v3CameraPos", -scaled_pos)

        shape.instance.setShaderInput("fCameraHeight", camera_height)
        shape.instance.setShaderInput("fCameraHeight2", camera_height * camera_height)

        shape.instance.setShaderInput("v3LightPos", scaled_star_pos)
        shape.instance.setShaderInput("model_scale", factor)
        shape.instance.setShaderInput("atm_descale", descale_mat)

class ONeilSimpleScattering(ONeilScatteringBase):
    str_id = 'oneil-simple'

    def uniforms_scattering(self, code):
        code.append("uniform vec3 v3OriginPos;")       # Center of the planet
        code.append("uniform vec3 v3CameraPos;")       # The camera's current position
        code.append("uniform vec3 v3LightPos;")        # The direction vector to the light source
        code.append("uniform vec3 v3InvWavelength;")   # 1 / pow(wavelength, 4) for the red, green, and blue channels
        code.append("uniform float fCameraHeight;")    # The camera's current height
        code.append("uniform float fCameraHeight2;")   # fCameraHeight^2
        code.append("uniform float fOuterRadius;")     # The outer (atmosphere) radius
        code.append("uniform float fOuterRadius2;")    # fOuterRadius^2
        code.append("uniform float fInnerRadius; ")    # The inner (planetary) radius
        code.append("uniform float fInnerRadius2;")    # fInnerRadius^2
        code.append("uniform float fKrESun;")          # Kr * ESun
        code.append("uniform float fKmESun;")          # Km * ESun
        code.append("uniform float fKr4PI;")           # Kr * 4 * PI
        code.append("uniform float fKm4PI;")           # Km * 4 * PI
        code.append("uniform float fScale;")           # 1 / (fOuterRadius - fInnerRadius)
        code.append("uniform float fScaleDepth;")      #/ The scale depth (i.e. the altitude at which the atmosphere's average density is found)
        code.append("uniform float fScaleOverScaleDepth;") # fScale / fScaleDepth

        code.append("uniform int nSamples;")
        code.append("uniform float fSamples;")
        code.append("uniform float model_scale;")
        code.append("uniform mat3 atm_descale;")

    def scale_func(self, code):
        code.append("float scale(float fCos)")
        code.append("{")
        code.append("  float x = 1.0 - fCos;")
        code.append("  return fScaleDepth * exp(-0.00287 + x*(0.459 + x*(3.83 + x*(-6.80 + x*5.25))));")
        code.append("}")

    def vertex_uniforms(self, code):
        ONeilScatteringBase.vertex_uniforms(self, code)
        if not self.calc_in_fragment:
            self.scale_func(code)

    def fragment_uniforms(self, code):
        ONeilScatteringBase.fragment_uniforms(self, code)
        if self.calc_in_fragment:
            self.scale_func(code)

    def calc_scattering(self, code):
        if self.calc_in_fragment and self.atmosphere:
            code.append("vec3 v3Direction;")
        if self.calc_in_fragment:
            code.append("vec3 rayleigh_inscattering;")
            code.append("vec3 mie_inscattering;")
            code.append("vec3 transmittance;")
        if self.normalize:
            if self.atmosphere:
                code.append("  vec3 scaled_vertex = normalize(atm_descale * (world_vertex * model_scale - v3OriginPos)) * fOuterRadius;")
            else:
                code.append("  vec3 scaled_vertex = normalize(atm_descale * (world_vertex * model_scale - v3OriginPos)) * fInnerRadius;")
                if self.displacement:
                    code.append("  scaled_vertex += world_normal * vertex_height * fInnerRadius;")
        else:
            code.append("  vec3 scaled_vertex = atm_descale * (world_vertex * model_scale - v3OriginPos);")
        code.append("  float scaled_vertex_length = length(scaled_vertex);")
        code.append("  vec3 scaled_vertex_dir = scaled_vertex / scaled_vertex_length;")
        code.append("  vec3 v3Ray = scaled_vertex - v3CameraPos;")
        code.append("  float fFar = length(v3Ray);")
        code.append("  v3Ray /= fFar;")

        if self.inside:
            code.append("  // Calculate the ray's starting position, then calculate its scattering offset")
            code.append("  vec3 v3Start = v3CameraPos;")
        else:
            code.append("  // Calculate the closest intersection of the ray with the outer atmosphere (which is the near point of the ray passing through the atmosphere)")
            code.append("  float B = 2.0 * dot(v3CameraPos, v3Ray);")
            code.append("  float C = fCameraHeight2 - fOuterRadius2;")
            code.append("  float fDet = max(0.0, B*B - 4.0 * C);")
            code.append("  float fNear = 0.5 * (-B - sqrt(fDet));")

            code.append("  // Calculate the ray's starting position, then calculate its scattering offset")
            code.append("  vec3 v3Start = v3CameraPos + v3Ray * fNear;")
            code.append("  fFar -= fNear;")

        if self.atmosphere:
            if self.inside:
                code.append("  float fHeight = length(v3Start);")
                code.append("  float fDepth = exp(fScaleOverScaleDepth * (fInnerRadius - fCameraHeight));")
                code.append("  float fStartAngle = dot(v3Ray, v3Start) / fHeight;")
                code.append("  float fStartOffset = fDepth*scale(fStartAngle);")
            else:
                code.append("  float fStartAngle = dot(v3Ray, v3Start) / fOuterRadius;")
                code.append("  float fStartDepth = exp(-1.0 / fScaleDepth);")
                code.append("  float fStartOffset = fStartDepth*scale(fStartAngle);")
        else:
            if self.inside:
                code.append("  float fDepth = exp((fInnerRadius - fCameraHeight) / fScaleDepth);")
            else:
                code.append("  float fDepth = exp((fInnerRadius - fOuterRadius) / fScaleDepth);")
            code.append("  float fCameraAngle;")
            code.append("  if(fCameraHeight > scaled_vertex_length) {")
            code.append("    fCameraAngle = dot(-v3Ray, scaled_vertex_dir);")
            code.append("  } else {")
            code.append("    fCameraAngle = dot(v3Ray, scaled_vertex_dir);")
            code.append("  }")
            #TODO: This is a crude workaround to avoid dark band on pixels at camera level
            code.append("  fCameraAngle = clamp(fCameraAngle, 0.1, 1.0);")
            code.append("  float fLightAngle = dot(v3LightPos, scaled_vertex_dir);")
            code.append("  float fCameraScale = scale(fCameraAngle);")
            code.append("  float fLightScale = scale(fLightAngle);")
            code.append("  float fCameraOffset = fDepth*fCameraScale;")
            code.append("  float fTemp = (fLightScale + fCameraScale);")
        code.append("  // Initialize the scattering loop variables")
        code.append("  float fSampleLength = fFar / fSamples;")
        code.append("  float fScaledLength = fSampleLength * fScale;")
        code.append("  vec3 v3SampleRay = v3Ray * fSampleLength;")
        code.append("  vec3 v3SamplePoint = v3Start + v3SampleRay * 0.5;")

        code.append("  // Now loop through the sample rays")
        code.append("  vec3 v3FrontColor = vec3(0.0, 0.0, 0.0);")
        code.append("  vec3 v3Attenuate = vec3(1.0);")
        code.append("  for(int i=0; i<nSamples; i++)")
        code.append("  {")
        code.append("    float fHeight = length(v3SamplePoint);")
        code.append("    float fDepth = exp(fScaleOverScaleDepth * (fInnerRadius - fHeight));")
        if self.atmosphere:
            code.append("    float fLightAngle = dot(v3LightPos, v3SamplePoint) / fHeight;")
            code.append("    float fCameraAngle = dot(v3Ray, v3SamplePoint) / fHeight * 0.99;")
            code.append("    float fScatter = (fStartOffset + fDepth*(scale(fLightAngle) - scale(fCameraAngle)));")
        else:
            code.append("    float fScatter = fDepth*fTemp - fCameraOffset;")
        code.append("    vec3 v3Attenuation = exp(-fScatter * (v3InvWavelength * fKr4PI + fKm4PI));")
        code.append("    v3Attenuate *= v3Attenuation;")
        code.append("    v3FrontColor += v3Attenuation * (fDepth * fScaledLength);")
        code.append("    v3SamplePoint += v3SampleRay;")
        code.append("  }")

        code.append("  // Finally, scale the Mie and Rayleigh colors and set up the varying variables for the pixel shader")
        code.append("  rayleigh_inscattering = v3FrontColor * (v3InvWavelength * fKrESun);")
        code.append("  mie_inscattering = v3FrontColor * fKmESun;")
        code.append("  transmittance = v3Attenuate;")
        if self.atmosphere:
            code.append("  v3Direction = v3CameraPos - scaled_vertex;")

    def update_shader_shape_static(self, shape, appearance):
        parameters = self.parameters
        inner_radius = parameters.planet_radius
        outer_radius = parameters.planet_radius * parameters.AtmosphereRatio
        scale = 1.0 / (outer_radius - inner_radius)

        shape.instance.setShaderInput("fKr4PI", parameters.Kr * 4 * pi)
        shape.instance.setShaderInput("fKm4PI", parameters.Km * 4 * pi)

        shape.instance.setShaderInput("fSamples", parameters.samples)
        shape.instance.setShaderInput("nSamples", parameters.samples)
        # These do sunsets and sky colors
        # Brightness of sun
        # Reyleight Scattering (Main sky colors)
        shape.instance.setShaderInput("fKrESun", parameters.Kr * parameters.ESun)
        # Mie Scattering -- Haze and sun halos
        shape.instance.setShaderInput("fKmESun", parameters.Km * parameters.ESun)
        # Color of sun
        shape.instance.setShaderInput("v3InvWavelength", 1.0 / pow(parameters.wavelength[0], 4),
                                                         1.0 / pow(parameters.wavelength[1], 4),
                                                         1.0 / pow(parameters.wavelength[2], 4))

        shape.instance.setShaderInput("fg", parameters.G)
        shape.instance.setShaderInput("fg2", parameters.G * parameters.G)
        shape.instance.setShaderInput("fExposure", parameters.exposure)

        shape.instance.setShaderInput("fOuterRadius", outer_radius)
        shape.instance.setShaderInput("fInnerRadius", inner_radius)
        shape.instance.setShaderInput("fOuterRadius2", outer_radius * outer_radius)
        shape.instance.setShaderInput("fInnerRadius2", inner_radius * inner_radius)

        shape.instance.setShaderInput("fScale", scale)
        shape.instance.setShaderInput("fScaleDepth", parameters.ScaleDepth)
        shape.instance.setShaderInput("fScaleOverScaleDepth", scale / parameters.ScaleDepth)

class ONeilLookupTableFragmentShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self, 'fragment')

    def create_uniforms(self, code):
        code.append("uniform float fOuterRadius;")     # The outer (atmosphere) radius
        code.append("uniform float fInnerRadius; ")    # The inner (planetary) radius
        code.append("uniform float fScale;")           # 1 / (fOuterRadius - fInnerRadius)
        code.append("uniform float fRayleighScaleHeight;")      # The Rayleigh scattering scale height
        code.append("uniform float fMieScaleHeight;")           # The Mie scattering scale height
        code.append("uniform int nSamples;")           # The number of samples

        code.append("#define DELTA 1e-6")

    def create_extra(self, code):
        self.pi(code)

    def create_inputs(self, code):
        code.append("in vec2 texcoord;")

    def create_outputs(self, code):
        if self.version >= 130:
            code.append("out vec4 frag_output;")

    def lookup_code(self, code):
        code.append("// As the y tex coord goes from 0 to 1, the angle goes from 0 to 180 degrees")
        code.append("float fCos = 1.0 - 2 * (texcoord.y);")
        code.append("float fAngle = acos(fCos);")
        code.append("vec3 v3Ray = vec3(sin(fAngle), cos(fAngle), 0);    // Ray pointing to the viewpoint")
        code.append("// As the x tex coord goes from 0 to 1, the height goes from the bottom of the atmosphere to the top")
        code.append("float fHeight = DELTA + fInnerRadius + ((fOuterRadius - fInnerRadius) * texcoord.x);")
        code.append("vec3 v3Pos = vec3(0, fHeight, 0);                // The position of the camera")

        code.append("// If the ray from vPos heading in the vRay direction intersects the inner radius (i.e. the planet), then this spot is not visible from the viewpoint")
        code.append("float B = 2.0f * dot(v3Pos, v3Ray);")
        code.append("float Bsq = B * B;")
        code.append("float Cpart = dot(v3Pos,v3Pos);")
        code.append("float C = Cpart - fInnerRadius*fInnerRadius;")
        code.append("float fDet = Bsq - 4.0f * C;")
        code.append("bool bVisible = (fDet < 0.0 || (0.5f * (-B - sqrt(fDet)) <= 0.0) && (0.5 * (-B + sqrt(fDet)) <= 0.0));")
        code.append("float fRayleighDensityRatio;")
        code.append("float fMieDensityRatio;")
        code.append("if(bVisible)")
        code.append("{")
        code.append("    fRayleighDensityRatio = exp(-(fHeight - fInnerRadius) * fScale / fRayleighScaleHeight);")
        code.append("    fMieDensityRatio = exp(-(fHeight - fInnerRadius) * fScale / fMieScaleHeight);")
        code.append("}")
        code.append("else")
        code.append("{")
        code.append("    fRayleighDensityRatio = 0.0;")
        code.append("    fMieDensityRatio = 0.0;")
        code.append("}")

        code.append("// Determine where the ray intersects the outer radius (the top of the atmosphere)")
        code.append("// This is the end of our ray for determining the optical depth (vPos is the start)")
        code.append("C = Cpart - fOuterRadius*fOuterRadius;")
        code.append("fDet = Bsq - 4.0 * C;")
        code.append("float fFar = 0.5 * (-B + sqrt(fDet));")

        code.append("// Next determine the length of each sample, scale the sample ray, and make sure position checks are at the center of a sample ray")
        code.append("float fSampleLength = fFar / nSamples;")
        code.append("float fScaledLength = fSampleLength * fScale;")
        code.append("vec3 v3SampleRay = v3Ray * fSampleLength;")
        code.append("v3Pos += v3SampleRay * 0.5;")

        code.append("// Iterate through the samples to sum up the optical depth for the distance the ray travels through the atmosphere")
        code.append("float fRayleighDepth = 0;")
        code.append("float fMieDepth = 0;")
        code.append("for(int i=0; i<nSamples; i++)")
        code.append("{")
        code.append("    float fHeight = length(v3Pos);")
        code.append("    float fAltitude = (fHeight - fInnerRadius) * fScale;")
        code.append("    fAltitude = max(fAltitude, 0.0);")
        code.append("    fRayleighDepth += exp(-fAltitude / fRayleighScaleHeight);")
        code.append("    fMieDepth += exp(-fAltitude / fMieScaleHeight);")
        code.append("    v3Pos += v3SampleRay;")
        code.append("}")

        code.append("// Multiply the sums by the length the ray traveled")
        code.append("fRayleighDepth *= fScaledLength;")
        code.append("fMieDepth *= fScaledLength;")

        code.append("// Store the results for Rayleigh to the light source, Rayleigh to the camera, Mie to the light source, and Mie to the camera")
        code.append("frag_output = vec4(fRayleighDensityRatio, fRayleighDepth, fMieDensityRatio, fMieDepth);")

    def create_body(self, code):
        if self.version < 130:
            code.append('vec4 frag_output;')
        self.lookup_code(code)
        if self.version < 130:
            code.append('gl_FragColor = frag_output;')

class ONeilLookupTableShader(StructuredShader):
    def __init__(self):
        StructuredShader.__init__(self)
        self.vertex_shader = GeneratorVertexShader()
        self.fragment_shader = ONeilLookupTableFragmentShader()

    def get_shader_id(self):
        name = 'oneil'
        return name

    def update(self, instance, parameters):
        planet_radius = parameters.planet_radius
        inner_radius = planet_radius
        outer_radius = parameters.radius

        scale = 1.0 / (outer_radius - inner_radius)

        instance.setShaderInput("nSamples", parameters.lookup_samples)
        instance.setShaderInput("fOuterRadius", outer_radius)
        instance.setShaderInput("fInnerRadius", inner_radius)
        instance.setShaderInput("fRayleighScaleHeight", parameters.rayleigh_scale_depth)
        instance.setShaderInput("fMieScaleHeight", parameters.mie_scale_depth)
        instance.setShaderInput("fScale", scale)

class ONeilLookupTableRenderStage(RenderStage):
    def __init__(self, size):
        RenderStage.__init__(self, "lookuptable", (size, size))

    def create_shader(self):
        shader = ONeilLookupTableShader()
        shader.create_and_register_shader(None, None)
        return shader

    def create(self):
        self.target = RenderTarget()
        (width, height) = self.get_size()
        self.target.make_buffer(width, height, Texture.F_rgb32, to_ram=False)
        self.target.set_shader(self.create_shader())

class ONeilScattering(ONeilScatteringBase):
    str_id = 'oneil'

    def uniforms_scattering(self, code):
        code.append("uniform vec3 v3OriginPos;")       # Center of the planet
        code.append("uniform vec3 v3CameraPos;")       # The camera's current position
        code.append("uniform vec3 v3LightPos;")        # The direction vector to the light source
        code.append("uniform vec3 v3Absorption;")      # Absorption coefs for the red, green, and blue channels
        code.append("uniform float fCameraHeight;")    # The camera's current height
        code.append("uniform float fCameraHeight2;")   # fCameraHeight^2
        code.append("uniform float fOuterRadius;")     # The outer (atmosphere) radius
        code.append("uniform float fOuterRadius2;")    # fOuterRadius^2
        code.append("uniform float fInnerRadius; ")    # The inner (planetary) radius
        code.append("uniform float fInnerRadius2;")    # fInnerRadius^2
        code.append("uniform vec3 v3KrESun;")          # Kr * ESun
        code.append("uniform vec3 v3KmESun;")          # Km * ESun
        code.append("uniform vec3 v3Kr4PI;")           # Kr * 4 * PI
        code.append("uniform vec3 v3Km4PI;")           # Km * 4 * PI
        code.append("uniform float fScale;")           # 1 / (fOuterRadius - fInnerRadius)

        code.append("uniform sampler2D pbOpticalDepth;")
        code.append("uniform int nSamples;")
        code.append("uniform float model_scale;")
        code.append("uniform mat3 atm_descale;")
        code.append("#define DELTA 1e-6")

    def calc_scattering(self, code):
        if self.calc_in_fragment and self.atmosphere:
            code.append("vec3 v3Direction;")
        if self.calc_in_fragment:
            code.append("vec3 rayleigh_inscattering;")
            code.append("vec3 mie_inscattering;")
            code.append("vec3 transmittance;")
        if self.normalize:
            if self.atmosphere:
                code.append("  vec3 scaled_vertex = normalize(atm_descale * (world_vertex * model_scale - v3OriginPos)) * fOuterRadius;")
            else:
                code.append("  vec3 scaled_vertex = normalize(atm_descale * (world_vertex * model_scale - v3OriginPos)) * fInnerRadius;")
                if self.displacement:
                    code.append("  scaled_vertex += world_normal * vertex_height * fInnerRadius;")
        else:
            code.append("  vec3 scaled_vertex = atm_descale * (world_vertex * model_scale - v3OriginPos);")
        code.append("  float scaled_vertex_length = length(scaled_vertex);")
        code.append("  vec3 scaled_vertex_dir = scaled_vertex / scaled_vertex_length;")
        code.append("  vec3 v3Ray = scaled_vertex - v3CameraPos;")
        code.append("  float fFar = length(v3Ray);")
        code.append("  v3Ray /= fFar;")

        code.append("  vec4 v4CameraDepth = vec4(0.0);")
        code.append("  vec4 v4LightDepth;")
        code.append("  vec4 v4SampleDepth;")
        code.append("  bool bCameraAbove = true;")

        if self.inside:
            code.append("  // Calculate the ray's starting position, then calculate its scattering offset")
            code.append("  vec3 v3Start = v3CameraPos;")
            code.append("  float fCameraAltitude = (fCameraHeight - fInnerRadius) * fScale;")
            code.append("  bCameraAbove = fCameraHeight >= length(scaled_vertex);")
            code.append("  float fCameraAngle = dot(bCameraAbove ? -v3Ray : v3Ray, v3CameraPos) / fCameraHeight;")
            code.append("  v4CameraDepth = texture2D(pbOpticalDepth, vec2(fCameraAltitude, 0.5 - fCameraAngle * 0.5));")
        else:
            code.append("  // Calculate the closest intersection of the ray with the outer atmosphere (which is the near point of the ray passing through the atmosphere)")
            code.append("  float B = 2.0 * dot(v3CameraPos, v3Ray);")
            code.append("  float C = fCameraHeight2 - fOuterRadius2;")
            code.append("  float fDet = max(0.0, B*B - 4.0 * C);")
            code.append("  float fNear = 0.5 * (-B - sqrt(fDet));")

            code.append("  // Calculate the ray's starting position, then calculate its scattering offset")
            code.append("  vec3 v3Start = v3CameraPos + v3Ray * fNear;")
            code.append("  fFar -= fNear;")

        code.append("  // Initialize a few variables to use inside the loop")
        code.append("  vec3 v3Attenuate = vec3(1.0);")
        code.append("  vec3 v3RayleighSum = vec3(0.0);")
        code.append("  vec3 v3MieSum = vec3(0.0);")
        code.append("  float fSampleLength = fFar / float(nSamples);")
        code.append("  float fScaledLength = fSampleLength * fScale;")
        code.append("  vec3 v3SampleRay = v3Ray * fSampleLength;")

        code.append("  // Start at the center of the first sample ray, and loop through each of the others")
        code.append("  vec3 v3SamplePoint = v3Start + v3SampleRay * 0.5;")
        code.append("  for(int i = 0; i < nSamples; i++)")
        code.append("  {")
        code.append("      float fHeight = length(v3SamplePoint);")
        code.append("      // Start by looking up the optical depth coming from the light source to this point")
        code.append("      float fLightAngle = dot(v3LightPos, v3SamplePoint) / fHeight;")
        code.append("      float fAltitude = (fHeight - fInnerRadius) * fScale;")
        code.append("      v4LightDepth = texture2D(pbOpticalDepth, vec2(fAltitude, 0.5 - fLightAngle * 0.5));")

        code.append("      // If no light light reaches this part of the atmosphere, no light is scattered in at this point")
        code.append("      if(v4LightDepth[0] < DELTA)")
        code.append("      {")
        code.append("          // Move the position to the center of the next sample ray")
        code.append("          v3SamplePoint += v3SampleRay;")
        code.append("          continue;")
        code.append("      }")

        code.append("      // Get the density at this point, along with the optical depth from the light source to this point")
        code.append("      float fRayleighDensity = fScaledLength * v4LightDepth[0];")
        code.append("      float fRayleighDepth = v4LightDepth[1];")
        code.append("      float fMieDensity = fScaledLength * v4LightDepth[2];")
        code.append("      float fMieDepth = v4LightDepth[3];")

        code.append("      // If the camera is above the point we're shading, we calculate the optical depth from the sample point to the camera")
        code.append("      // Otherwise, we calculate the optical depth from the camera to the sample point")
        code.append("      if(bCameraAbove)")
        code.append("      {")
        code.append("          float fSampleAngle = -dot(v3Ray, v3SamplePoint) / fHeight;")
        code.append("          v4SampleDepth = texture2D(pbOpticalDepth, vec2(fAltitude, 0.5 - fSampleAngle * 0.5));")
        code.append("          fRayleighDepth += v4SampleDepth[1] - v4CameraDepth[1];")
        code.append("          fMieDepth += v4SampleDepth[3] - v4CameraDepth[3];")
        code.append("      }")
        code.append("      else")
        code.append("      {")
        code.append("          float fSampleAngle = dot(v3Ray, v3SamplePoint) / fHeight;")
        code.append("          v4SampleDepth = texture2D(pbOpticalDepth, vec2(fAltitude, 0.5 - fSampleAngle * 0.5));")
        code.append("          fRayleighDepth += v4CameraDepth[1] - v4SampleDepth[1];")
        code.append("          fMieDepth += v4CameraDepth[3] - v4SampleDepth[3];")
        code.append("      }")

        code.append("      // Now multiply the optical depth by the attenuation factor for the sample ray")
        code.append("      // Calculate the attenuation factor for the sample ray")
        code.append("      vec3 v3Attenuation;")
        code.append("      v3Attenuation = exp(-fRayleighDepth * v3Absorption -fRayleighDepth * v3Kr4PI - fMieDepth * v3Km4PI);")
        code.append("      v3Attenuate = v3Attenuation;")

        code.append("      v3RayleighSum += fRayleighDensity * v3Attenuation;")
        code.append("      v3MieSum += fMieDensity * v3Attenuation;")

        code.append("      // Move the position to the center of the next sample ray")
        code.append("      v3SamplePoint += v3SampleRay;")
        code.append("  }")
        code.append("  // Finally, scale the Mie and Rayleigh colors and set up the varying variables for the pixel shader")
        code.append("  rayleigh_inscattering = v3RayleighSum * v3KrESun;")
        code.append("  mie_inscattering = v3MieSum * v3KmESun;")
        code.append("  transmittance = v3Attenuate;")
        if self.atmosphere:
            code.append("  v3Direction = -v3Ray;")

    def update_shader_shape_static(self, shape, appearance):
        parameters = self.parameters
        pbOpticalDepth = parameters.get_lookup_table()
        inner_radius = parameters.planet_radius
        outer_radius =  parameters.radius
        scale = 1.0 / (outer_radius - inner_radius)

        shape.instance.setShaderInput("nSamples", int(parameters.samples))
        # These do sunsets and sky colors
        # Brightness of sun
        # Reyleight Scattering (Main sky colors)
        Kr = LVector3d(parameters.Kr / pow(parameters.wavelength[0], 4),
                       parameters.Kr / pow(parameters.wavelength[1], 4),
                       parameters.Kr / pow(parameters.wavelength[2], 4))
        shape.instance.setShaderInput("v3KrESun", Kr * parameters.ESun)
        shape.instance.setShaderInput("v3Kr4PI", Kr * 4 * pi)
        shape.instance.setShaderInput("v3Absorption", parameters.rayleigh_absorption)
        # Mie Scattering -- Haze and sun halos
        Km = LVector3d(parameters.Km_beta / pow(parameters.wavelength[0], parameters.Km_alpha),
                       parameters.Km_beta / pow(parameters.wavelength[1], parameters.Km_alpha),
                       parameters.Km_beta / pow(parameters.wavelength[2], parameters.Km_alpha))
        shape.instance.setShaderInput("v3KmESun", Km * parameters.ESun)
        shape.instance.setShaderInput("v3Km4PI", Km * 4 * pi)

        shape.instance.setShaderInput("fg", parameters.G)
        shape.instance.setShaderInput("fg2", parameters.G * parameters.G)
        shape.instance.setShaderInput("fExposure", parameters.exposure)

        shape.instance.setShaderInput("fOuterRadius", outer_radius)
        shape.instance.setShaderInput("fInnerRadius", inner_radius)
        shape.instance.setShaderInput("fOuterRadius2", outer_radius * outer_radius)
        shape.instance.setShaderInput("fInnerRadius2", inner_radius * inner_radius)

        shape.instance.setShaderInput("fScale", scale)

        shape.instance.setShaderInput("pbOpticalDepth", pbOpticalDepth)
