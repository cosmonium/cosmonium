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

from panda3d.core import LVector3d

from ..bodyelements import Atmosphere
from ..utils import TransparencyBlend
from ..shaders import BasicShader, AtmosphericScattering

from math import log

class CelestiaAtmosphere(Atmosphere):
    AtmosphereExtinctionThreshold = 0.05
    mieScaleHeight = 12
    def __init__(self, height,
                 mie_coef=0.0, mie_scale_height=0.0, mie_phase_asymmetry=0.0,
                 rayleigh_coef=None, rayleigh_scale_height=0.0,
                 absorption_coef=None,
                 shape=None, appearance=None, shader=None):
        Atmosphere.__init__(self, shape=shape, appearance=appearance, shader=shader)
        self.height = height
        self.mie_coef = mie_coef
        self.mie_scale_height = mie_scale_height
        self.mie_phase_asymmetry = mie_phase_asymmetry
        if rayleigh_coef is None:
            self.rayleigh_coef = LVector3d()
        else:
            self.rayleigh_coef = LVector3d(*rayleigh_coef)
        self.rayleigh_scale_height = rayleigh_scale_height
        if absorption_coef is None:
            self.absorption_coef = LVector3d()
        else:
            self.absorption_coef = LVector3d(*absorption_coef)
        self.blend = TransparencyBlend.TB_AlphaAdditive
        shader = BasicShader(lighting_model=CelestiaScattering(atmosphere=True))
        self.set_shader(shader)

    def set_parent(self, parent):
        Atmosphere.set_parent(self, parent)
        if parent is not None:
            self.planet_radius = parent.get_apparent_radius()
            self.radius = self.planet_radius + self.height
            self.ratio = self.radius / self.planet_radius

    def create_scattering_shader(self, atmosphere):
        return CelestiaScattering(atmosphere)

class CelestiaScattering(AtmosphericScattering):
    use_vertex = True
    world_vertex = True
    AtmosphereExtinctionThreshold = 0.05

    def __init__(self, atmosphere=False, shader=None):
        AtmosphericScattering.__init__(self, shader)
        self.atmosphere = atmosphere
        self.calc_in_fragment = False

    def get_id(self):
        name = "celestia-"
        if self.atmosphere:
            name += "sky"
        else:
            name += "ground"
        return name

    def uniforms_scattering(self, code):
        code += ['''
uniform vec3 atmosphereRadius;
uniform float mieCoeff;
uniform float mieH;
uniform float mieK;
uniform vec3 rayleighCoeff;
uniform float rayleighH;
uniform vec3 scatterCoeffSum;
uniform vec3 invScatterCoeffSum;
uniform vec3 extinctionCoeff;

uniform vec3 v3OriginPos;
uniform vec3 v3LightDir;
uniform vec3 v3CameraPos;

uniform float model_scale;
''']

    def uniforms_colors(self, code):
        code += ['''
uniform float mieK;
uniform float mieCoeff;
uniform vec3  rayleighCoeff;
uniform vec3  invScatterCoeffSum;

uniform vec3 v3LightDir;
''']

    def vertex_uniforms(self, code):
        if not self.calc_in_fragment:
            self.uniforms_scattering(code)

    def vertex_outputs(self, code):
        if not self.calc_in_fragment:
            code.append("out vec3 scatteredColor;")
            code.append("out vec3 scatterEx;")
            code.append("out vec3 eyeDir_obj;")

    def fragment_uniforms(self, code):
        if self.calc_in_fragment:
            self.uniforms_scattering(code)
        self.uniforms_colors(code)

    def fragment_inputs(self, code):
        if not self.calc_in_fragment:
            code.append("in vec3 scatteredColor;")
            code.append("in vec3 scatterEx;")
            code.append("in vec3 eyeDir_obj;")

    def calc_scattering(self, code):
        code += ['''
    vec3 v3Pos = (world_vertex - v3OriginPos) * model_scale;
    vec3 eyeDir = normalize(v3CameraPos - v3Pos);
    vec3 eyePosition = v3CameraPos;

    // Compute the intersection of the view direction and the cloud layer (currently assumed to be a sphere)
    float rq = dot(eyePosition, eyeDir);
    float qq = dot(eyePosition, eyePosition) - atmosphereRadius.y;
    float d = sqrt(rq * rq - qq);
    vec3 atmEnter = eyePosition + min(0.0, (-rq + d)) * eyeDir;
    vec3 atmLeave = v3Pos;

    vec3 atmSamplePoint = (atmEnter + atmLeave) * 0.5;
//    vec3 atmSamplePoint = atmEnter * 0.2 + atmLeave * 0.8;

    // Compute the distance through the atmosphere from the sample point to the sun
    vec3 atmSamplePointSun = atmEnter * 0.5 + atmLeave * 0.5;
    rq = dot(atmSamplePointSun, v3LightDir);
    qq = dot(atmSamplePointSun, atmSamplePointSun) - atmosphereRadius.y;
    d = sqrt(rq * rq - qq);
    float distSun = -rq + d;
    float distAtm = length(atmEnter - atmLeave);

    // Compute the density of the atmosphere at the sample point; it falls off exponentially
    // with the height above the planet's surface.
#if 0
    float h = max(0.0, length(atmSamplePoint) - atmosphereRadius.z);
    float density = exp(-h * mieH);
#else
    float density = 0.0;
    atmSamplePoint = atmEnter * 0.333 + atmLeave * 0.667;
    //    atmSamplePoint = atmEnter * 0.1 + atmLeave * 0.9;
    float h = max(0.0, length(atmSamplePoint) - atmosphereRadius.z);
    density += exp(-h * mieH);
    atmSamplePoint = atmEnter * 0.667 + atmLeave * 0.333;
    //    atmSamplePoint = atmEnter * 0.9 + atmLeave * 0.1;
    h = max(0.0, length(atmSamplePoint) - atmosphereRadius.z);
    density += exp(-h * mieH);
#endif

    vec3 sunColor = exp(-extinctionCoeff * density * distSun);
    vec3 ex = exp(-extinctionCoeff * density * distAtm);

    // If we're rendering the sky dome, compute the phase functions in the fragment shader
    // rather than the vertex shader in order to avoid artifacts from coarse tessellation.
    scatterEx = ex;
    scatteredColor = sunColor * (1.0 - exp(-scatterCoeffSum * density * distAtm));

    eyeDir_obj = eyeDir;
''']

    def calc_colors(self, code):
        code += ['''
    vec3 V = normalize(eyeDir_obj);
    float cosTheta = dot(V, v3LightDir);

    float phMie = (1.0 - mieK * mieK) / ((1.0 - mieK * cosTheta) * (1.0 - mieK * cosTheta));

    // Ignore Rayleigh phase function and treat Rayleigh scattering as isotropic
    // float phRayleigh = (1.0 + cosTheta * cosTheta);
    float phRayleigh = 1.0;

    // TODO: Consider premultiplying by invScatterCoeffSum
    vec3 scatteredComponent = (phRayleigh * rayleighCoeff + phMie * mieCoeff) * invScatterCoeffSum * scatteredColor;
''']
        if self.atmosphere:
            code.append("  total_diffuse_color = vec4(shadow * scatteredComponent, dot(scatterEx, vec3(0.333, 0.333, 0.333)));;")
        else:
            code.append("          total_diffuse_color = vec4(shadow * scatteredComponent + total_diffuse_color.rgb * scatterEx, total_diffuse_color.a);")

    def vertex_shader(self, code):
        if not self.calc_in_fragment:
            self.calc_scattering(code)

    def fragment_shader(self, code):
        if self.calc_in_fragment:
            self.calc_scattering(code)
        self.calc_colors(code)

    def update_shader_shape_static(self, shape, appearance):
        parameters = shape.owner.atmosphere
        planet_radius = shape.owner.get_apparent_radius()

        if self.atmosphere:
            #render.cpp 7193
            radius = planet_radius + shape.owner.atmosphere.height
            #renderglsl.cpp 557
            atmosphereRadius = radius + -parameters.mie_scale_height * log(self.AtmosphereExtinctionThreshold)
            atmPlanetRadius = radius
            objRadius = atmosphereRadius
        else:
            radius = planet_radius
            #rendercontext.cpp 785
            atmPlanetRadius = radius
            objRadius = radius

        #shadermanager.cpp 3446
        skySphereRadius = atmPlanetRadius + -parameters.mie_scale_height * log(self.AtmosphereExtinctionThreshold)
        mieCoeff        = parameters.mie_coef * objRadius
        rayleighCoeff   = parameters.rayleigh_coef * objRadius
        absorptionCoeff = parameters.absorption_coef * objRadius

        r = skySphereRadius / objRadius
        atmosphereRadius = LVector3d(r, r * r, atmPlanetRadius / objRadius)
        mieScaleHeight = objRadius / parameters.mie_scale_height

        # The scattering shaders use the Schlick approximation to the
        # Henyey-Greenstein phase function because it's slightly faster
        # to compute. Convert the HG asymmetry parameter to the Schlick
        # parameter.
        g = parameters.mie_phase_asymmetry
        miePhaseAsymmetry = 1.55 * g - 0.55 * g * g * g

        rayleighScaleHeight = 0.0

        # Precompute sum and inverse sum of scattering coefficients to save work
        # in the vertex shader.
        scatterCoeffSum = rayleighCoeff + LVector3d(mieCoeff, mieCoeff, mieCoeff)
        invScatterCoeffSum = LVector3d(1.0 / scatterCoeffSum[0], 1.0 / scatterCoeffSum[1], 1.0 / scatterCoeffSum[2])
        extinctionCoeff = scatterCoeffSum + absorptionCoeff

        shape.instance.setShaderInput("atmosphereRadius", *atmosphereRadius)
        shape.instance.setShaderInput("mieCoeff", mieCoeff)
        shape.instance.setShaderInput("mieH", mieScaleHeight)
        shape.instance.setShaderInput("mieK", miePhaseAsymmetry)
        shape.instance.setShaderInput("rayleighCoeff", *rayleighCoeff)
        shape.instance.setShaderInput("rayleighH", rayleighScaleHeight)
        # Color of sun
        shape.instance.setShaderInput("scatterCoeffSum", *scatterCoeffSum)
        shape.instance.setShaderInput("invScatterCoeffSum", *invScatterCoeffSum)
        shape.instance.setShaderInput("extinctionCoeff", *extinctionCoeff)

    def update_shader_shape(self, shape, appearance):
        planet_radius = shape.owner.get_apparent_radius()
        if self.atmosphere:
            #render.cpp 7193
            radius = planet_radius + shape.owner.atmosphere.height
        else:
            radius = planet_radius
        factor = 1.0 / (shape.owner.scene_scale_factor * radius)

        light_dir = shape.owner.vector_to_star
        shape.instance.setShaderInput("v3OriginPos", shape.owner.rel_position * shape.owner.scene_scale_factor)
        shape.instance.setShaderInput("v3CameraPos", -shape.owner.rel_position / radius)

        shape.instance.setShaderInput("v3LightDir", *light_dir)
        shape.instance.setShaderInput("model_scale", factor)
