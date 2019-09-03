from __future__ import print_function
from __future__ import absolute_import

from .bodyelements import Atmosphere
from .shaders import AtmosphericScattering
from .utils import TransparencyBlend

from math import pow, pi

class ONeilAtmosphere(Atmosphere):
    AtmosphereRatio = 1.025
    def __init__(self,
                 shape=None,
                 mie_phase_asymmetry = -0.99,
                 rayleigh_coef = 0.0025,
                 mie_coef = 0.0015,
                 sun_power = 15.0,
                 wavelength = [0.650, 0.570, 0.465],
                 exposure = 0.8,
                 calc_in_fragment=False,
                 normalize=False,
                 hdr=False,
                 appearance=None, shader=None):
        Atmosphere.__init__(self, shape, appearance, shader)
        self.blend = TransparencyBlend.TB_Alpha
        self.G = mie_phase_asymmetry
        self.Kr = rayleigh_coef
        self.Km = mie_coef
        self.ESun = sun_power
        self.wavelength = wavelength
        self.exposure = exposure,
        self.calc_in_fragment = calc_in_fragment
        self.normalize = normalize
        self.hdr = hdr
        self.inside = None

    def set_parent(self, parent):
        Atmosphere.set_parent(self, parent)
        if parent is not None:
            self.planet_radius = parent.get_min_radius()
            self.radius = self.planet_radius * self.AtmosphereRatio
            self.ratio = self.AtmosphereRatio

    def create_scattering_shader(self, atmosphere):
        scattering = ONeilScattering(atmosphere=atmosphere, calc_in_fragment=self.calc_in_fragment, normalize=self.normalize, hdr=self.hdr)
        scattering.inside = self.inside
        return scattering

    def do_update_scattering(self, shape_object):
        shape_object.shader.scattering.inside = self.inside

    def update_instance(self, camera_pos, orientation):
        planet_radius = self.owner.get_min_radius()
        radius = planet_radius * self.AtmosphereRatio
        inside = self.owner.distance_to_obs < radius
        if self.inside != inside:
            self.inside = inside
            self.shader.scattering.inside = inside
            self.update_shader()
            self.update_scattering()
        return Atmosphere.update_instance(self, camera_pos, orientation)

class ONeilScattering(AtmosphericScattering):
    use_vertex = True
    world_vertex = True
    AtmosphereRatio = 1.025
    ScaleDepth = 0.25

    def __init__(self, atmosphere=False, calc_in_fragment=False, normalize=False, hdr=False):
        AtmosphericScattering.__init__(self)
        self.atmosphere = atmosphere
        self.calc_in_fragment = calc_in_fragment
        self.use_vertex_frag = calc_in_fragment
        self.normalize = normalize
        self.hdr = hdr
        self.use_normal = False#not self.atmosphere
        self.inside = False

    def get_id(self):
        name = "oneil-"
        if self.atmosphere:
            name += "sky"
        else:
            name += "ground"
        if self.inside:
            name += '-inside'
        if self.calc_in_fragment:
            name += "-infrag"
        if self.hdr:
            name += "-hdr"
        if self.hdr:
            name += "-norm"
        return name

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

    def uniforms_colors(self, code):
        if not self.calc_in_fragment:
            code.append("uniform vec3 v3LightPos;")
        if self.atmosphere:
            code.append("uniform float fg;")
            code.append("uniform float fg2;")
        code.append("uniform float fExposure;")

    def scale_func(self, code):
        code.append("float scale(float fCos)")
        code.append("{")
        code.append("  float x = 1.0 - fCos;")
        code.append("  return fScaleDepth * exp(-0.00287 + x*(0.459 + x*(3.83 + x*(-6.80 + x*5.25))));")
        code.append("}")

    def vertex_uniforms(self, code):
        if not self.calc_in_fragment:
            self.uniforms_scattering(code)
            self.scale_func(code)

    def vertex_outputs(self, code):
        if not self.calc_in_fragment:
            code.append("out vec4 primary_color;")
            code.append("out vec4 secondary_color;")
            if self.atmosphere:
                code.append("out vec3 v3Direction;")

    def fragment_uniforms(self, code):
        if self.calc_in_fragment:
            self.uniforms_scattering(code)
            self.scale_func(code)
        self.uniforms_colors(code)

    def fragment_inputs(self, code):
        if not self.calc_in_fragment:
            code.append("in vec4 primary_color;")
            code.append("in vec4 secondary_color;")
            if self.atmosphere:
                code.append("in vec3 v3Direction;")

    def calc_scattering(self, code):
        if self.calc_in_fragment and self.atmosphere:
            code.append("vec3 v3Direction;")
        if self.calc_in_fragment:
            code.append("vec4 primary_color;")
            code.append("vec4 secondary_color;")
        if self.normalize:
            if self.atmosphere:
                code.append("  vec3 scaled_vertex = normalize(world_vertex * model_scale - v3OriginPos) * fOuterRadius;")
            else:
                code.append("  vec3 scaled_vertex = normalize(world_vertex * model_scale - v3OriginPos);")
        else:
            code.append("  vec3 scaled_vertex = (world_vertex * model_scale - v3OriginPos);")
        code.append("  float scaled_vertex_length = length(scaled_vertex);")
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
            code.append("    fCameraAngle = dot(-v3Ray, scaled_vertex) / scaled_vertex_length;")
            code.append("  } else {")
            code.append("    fCameraAngle = dot(v3Ray, scaled_vertex) / scaled_vertex_length;")
            code.append("  }")
            code.append("  float fLightAngle = dot(v3LightPos, scaled_vertex) / scaled_vertex_length;")
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
        code.append("  vec3 v3Attenuate = vec3(0.0, 0.0, 0.0);")
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
        code.append("    v3Attenuate = exp(-fScatter * (v3InvWavelength * fKr4PI + fKm4PI));")
        code.append("    v3FrontColor += v3Attenuate * (fDepth * fScaledLength);")
        code.append("    v3SamplePoint += v3SampleRay;")
        code.append("  }")

        if self.atmosphere:
            code.append("  // Finally, scale the Mie and Rayleigh colors and set up the varying variables for the pixel shader")
            code.append("  primary_color = vec4(v3FrontColor * (v3InvWavelength * fKrESun), 0.0);")
            code.append("  secondary_color = vec4(v3FrontColor * fKmESun, 0.0);")
            code.append("  v3Direction = v3CameraPos - scaled_vertex;")
        else:
            code.append("  // Finally, scale the Mie and Rayleigh colors and alculate the attenuation factor for the ground")
            code.append("  primary_color = vec4(v3FrontColor * (v3InvWavelength * fKrESun + fKmESun), 1.0);")
            code.append("  secondary_color = vec4(v3Attenuate, 1.0);")

    def calc_colors(self, code):
        if self.atmosphere:
            code.append("    float fCos = dot(v3LightPos, v3Direction) / length(v3Direction);")
            code.append("    float fRayleighPhase = 0.75 * (1.0 + fCos*fCos);")
            code.append("    float fMiePhase = 1.5 * ((1.0 - fg2) / (2.0 + fg2)) * (1.0 + fCos*fCos) / pow(1.0 + fg2 - 2.0*fg*fCos, 1.5);")
            code.append("    total_diffuse_color = fRayleighPhase * primary_color + fMiePhase * secondary_color;")
            if self.hdr:
                code.append("    total_diffuse_color.rgb = 1.0 -exp(total_diffuse_color.rgb * -fExposure);")
            code.append("    total_diffuse_color.a = max(total_diffuse_color.r, max(total_diffuse_color.g, total_diffuse_color.b));")
        else:
            code.append("  total_diffuse_color.rgb = shadow * primary_color.rgb + total_diffuse_color.rgb * (secondary_color.rgb + (1.0 - secondary_color.rgb) * ambient.rgb);")
            if self.hdr:
                code.append("  total_diffuse_color.rgb = 1.0 -exp(total_diffuse_color.rgb * -fExposure);")

    def vertex_shader(self, code):
        if not self.calc_in_fragment:
            self.calc_scattering(code)

    def fragment_shader(self, code):
        if self.calc_in_fragment:
            self.calc_scattering(code)
        self.calc_colors(code)

    def update_shader_shape_static(self, shape, appearance):
        parameters = shape.owner.atmosphere
        inner_radius = 1.0
        outer_radius = self.AtmosphereRatio
        scale = 1.0 / (outer_radius - inner_radius)

        shape.instance.setShaderInput("fKr4PI", parameters.Kr * 4 * pi)
        shape.instance.setShaderInput("fKm4PI", parameters.Km * 4 * pi)
        
        shape.instance.setShaderInput("fSamples", 5.0)
        shape.instance.setShaderInput("nSamples", 5)
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
        shape.instance.setShaderInput("fScaleDepth", self.ScaleDepth)
        shape.instance.setShaderInput("fScaleOverScaleDepth", scale / self.ScaleDepth)

    def update_shader_shape(self, shape, appearance):
        planet_radius = shape.owner.get_apparent_radius()
        factor = 1.0 / (shape.owner.scene_scale_factor * planet_radius)

        camera_height = max(shape.owner.distance_to_obs / planet_radius, 1.0)
        light_dir = shape.owner.vector_to_star

        pos = shape.owner.rel_position / planet_radius
        distance = pos.length()
        if distance < 1.0:
            pos.normalize()
        shape.instance.setShaderInput("v3OriginPos", pos)
        shape.instance.setShaderInput("v3CameraPos", -pos)

        shape.instance.setShaderInput("fCameraHeight", camera_height)
        shape.instance.setShaderInput("fCameraHeight2", camera_height * camera_height)

        shape.instance.setShaderInput("v3LightPos", *light_dir)
        shape.instance.setShaderInput("model_scale", factor)
