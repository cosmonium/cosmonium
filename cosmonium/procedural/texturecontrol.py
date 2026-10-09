#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from math import cos, pi

from ..shaders.component import ShaderComponent


class TextureControl(ShaderComponent):
    def __init__(self, name):
        ShaderComponent.__init__(self)
        self.name = name

    def get_sources_names(self):
        return set(['heightmap'])

    def collect_required_data(self, data):
        pass

    def color_func_call(self, code):
        pass

    def get_provided_categories(self, texture_source):
        return set(texture_source.texture_categories.keys())


class ColormapLayer(object):
    def __init__(self, height, bottom=None, top=None):
        self.height = height
        self.bottom = bottom
        self.top = top


class HeightColorMap(TextureControl):
    """
    Procedurally colors the terrain by interpolating between a list of
    (height, color) layers using the heightmap (and optionally the surface slope).
    """

    def __init__(self, name, colormap, interpolation='linear', slope_color=None, slope_start=0.0, slope_end=0.0):
        TextureControl.__init__(self, name)
        self.colormap = colormap
        self.interpolation = interpolation
        self.slope_color = slope_color
        # Converted angle to cos(angle) to directly compare with the slope value
        # (cosine of the angle between the surface normal and the up vector)
        self.slope_start = cos(slope_start * pi / 180)
        self.slope_end = cos(slope_end * pi / 180)

    def collect_required_data(self, data):
        data.setdefault('heightmap', set()).add('height')

    def get_provided_categories(self, texture_source):
        return {'albedo'}

    def fragment_extra(self, code):
        TextureControl.fragment_extra(self, code)
        signature = "float height"
        if self.slope_color is not None:
            signature += ", float angle"
        code.append("vec3 detail_%s(%s)" % (self.name, signature))
        code.append("{")
        code.append("    vec3 color;")
        if not self.colormap:
            # Misconfigured colormap (no entries) : flag it with an obviously wrong color
            # instead of failing shader generation.
            code.append("    color = vec3(1.0, 0.0, 1.0);")
        else:
            previous_layer = None
            for layer in self.colormap:
                bottom = layer.bottom
                if previous_layer is None:
                    # Below the first threshold, extend the first layer's bottom color (or its
                    # top color if no bottom was given).
                    if bottom is None:
                        bottom = layer.top
                    code.append("    if (height <= %g) {" % (layer.height))
                    code.append('        color = vec3(%g, %g, %g);' % (bottom[0], bottom[1], bottom[2]))
                    code.append("    }")
                else:
                    if bottom is None:
                        bottom = previous_layer.top
                    delta = layer.height - previous_layer.height
                    if delta <= 0.0:
                        # Guard against a degenerate (duplicated or decreasing) height entry
                        # producing a division by zero.
                        delta = 1e-6
                    code.append("    else if (height <= %g) {" % (layer.height))
                    if self.interpolation == 'none':
                        code.append('        color = vec3(%g, %g, %g);' % (layer.top[0], layer.top[1], layer.top[2]))
                    else:
                        code.append(
                            '        float e = clamp((height - %g) / %g, 0.0, 1.0);' % (previous_layer.height, delta)
                        )
                        if self.interpolation == 'smooth':
                            code.append('        e = smoothstep(0.0, 1.0, e);')
                        code.append(
                            '        color = mix(vec3(%g, %g, %g), vec3(%g, %g, %g), e);'
                            % (bottom[0], bottom[1], bottom[2], layer.top[0], layer.top[1], layer.top[2])
                        )
                    code.append("    }")
                previous_layer = layer
            code.append("    else {")
            code.append(
                '        color = vec3(%g, %g, %g);'
                % (previous_layer.top[0], previous_layer.top[1], previous_layer.top[2])
            )
            code.append("    }")
        if self.slope_color is not None:
            slope_range = self.slope_start - self.slope_end
            if abs(slope_range) < 1e-6:
                slope_range = 1e-6
            code.append("    float slope_e = clamp((%g - angle) / %g, 0.0, 1.0);" % (self.slope_start, slope_range))
            code.append(
                "    color = mix(color, vec3(%g, %g, %g), slope_e);"
                % (self.slope_color[0], self.slope_color[1], self.slope_color[2])
            )
        code.append("    return color;")
        code.append("}")

    def color_func_call(self, code):
        pass

    def get_value(self, code, category):
        args = "height"
        if self.slope_color is not None:
            args += ", angle"
        code.append("    vec4 %s_%s = vec4(detail_%s(%s), 1.0);" % (self.name, category, self.name, args))


class SimpleTextureControl(TextureControl):
    def color_func_call(self, code):
        index, nb_coefs = self.shader.data_source.get_source_for("%s_index" % self.name)
        major = index // 4
        minor = index % 4
        initializer = ', '.join(['vec4(0)' for x in range(nb_coefs)])
        code.append("    vec4 %s_coefs[NB_COEFS_VEC] = vec4[](%s);" % (self.name, initializer))
        code.append("    %s_coefs[%d][%d] = 1.0;" % (self.name, major, minor))


class HeightTextureControlEntry(object):
    def __init__(self, texture_control, height, blend):
        self.texture_control = texture_control
        self.height = height
        self.blend = blend


class HeightTextureControl(TextureControl):
    def __init__(self, name, entries):
        TextureControl.__init__(self, name)
        self.entries = entries

    def get_sources_names(self):
        sources = set(['heightmap'])
        for entry in self.entries:
            sources.update(entry.texture_control.get_sources_names())
        return sources

    def collect_required_data(self, data):
        data.setdefault('heightmap', set()).add('height')
        for entry in self.entries:
            entry.texture_control.collect_required_data(data)

    def set_shader(self, shader):
        TextureControl.set_shader(self, shader)
        for entry in self.entries:
            entry.texture_control.set_shader(shader)

    def fragment_uniforms(self, code):
        TextureControl.fragment_uniforms(self, code)
        for entry in self.entries:
            entry.texture_control.fragment_uniforms(code)

    def fragment_extra(self, code):
        TextureControl.fragment_extra(self, code)
        for entry in self.entries:
            entry.texture_control.fragment_extra(code)
        code.append("vec4[NB_COEFS_VEC] detail_%s(TextureControlParams params)" % self.name)
        code.append("{")
        code.append("    vec4 coefs[NB_COEFS_VEC];")
        code.append("    float height_weight;")
        for entry in self.entries:
            entry.texture_control.color_func_call(code)
        previous = None
        for entry in self.entries:
            if previous is None:
                code.append("    if (params.heightmap_height <= %g) {" % (entry.height - entry.blend / 2.0))
                code.append("      coefs = %s_coefs;" % entry.texture_control.name)
            elif entry.blend != 0.0:
                code.append("    } else if (params.heightmap_height <= %g) {" % (entry.height - entry.blend / 2.0))
                code.append(
                    "        height_weight = clamp((params.heightmap_height - %g) / %g, 0, 1);"
                    % (previous.height - previous.blend / 2.0, previous.blend)
                )
                code.append("        for (int i = 0; i < coefs.length(); ++i) {")
                code.append(
                    "            coefs[i] = mix(%s_coefs[i], %s_coefs[i], height_weight);"
                    % (previous.texture_control.name, entry.texture_control.name)
                )
                code.append("        }")
            else:
                code.append("    } else if (params.heightmap_height <= %g) {" % (entry.height - entry.blend / 2.0))
                code.append("      coefs = %s_coefs;" % entry.texture_control.name)
            previous = entry
        code.append("   } else {")
        code.append("      coefs = %s_coefs;" % entry.texture_control.name)
        code.append('    }')
        code.append("    return coefs;")
        code.append("}")

    def color_func_call(self, code):
        code.append("    vec4 %s_coefs[NB_COEFS_VEC] = detail_%s(params);" % (self.name, self.name))


class SlopeTextureControlEntry(object):
    def __init__(self, texture_control, slope, blend):
        self.texture_control = texture_control
        self.slope = cos(slope * pi / 180)
        a = cos((slope + blend / 2.0) * pi / 180)
        b = cos((slope - blend / 2.0) * pi / 180)
        self.blend = (b - a) / 2


class SlopeTextureControl(TextureControl):
    def __init__(self, name, entries):
        TextureControl.__init__(self, name)
        self.entries = entries

    def get_sources_names(self):
        sources = set(['heightmap'])
        for entry in self.entries:
            sources.update(entry.texture_control.get_sources_names())
        return sources

    def collect_required_data(self, data):
        data.setdefault('heightmap', set()).add('angle')
        for entry in self.entries:
            entry.texture_control.collect_required_data(data)

    def set_shader(self, shader):
        TextureControl.set_shader(self, shader)
        for entry in self.entries:
            entry.texture_control.set_shader(shader)

    def fragment_uniforms(self, code):
        TextureControl.fragment_uniforms(self, code)
        for entry in self.entries:
            entry.texture_control.fragment_uniforms(code)

    def fragment_extra(self, code):
        TextureControl.fragment_extra(self, code)
        for entry in self.entries:
            entry.texture_control.fragment_extra(code)
        code.append("vec4[NB_COEFS_VEC] detail_%s(TextureControlParams params)" % self.name)
        code.append("{")
        code.append("    vec4 coefs[NB_COEFS_VEC];")
        code.append("    float slope_weight;")
        for entry in self.entries:
            entry.texture_control.color_func_call(code)
        previous = None
        for entry in self.entries:
            if previous is None:
                code.append("    coefs = %s_coefs;" % entry.texture_control.name)
            else:
                code.append(
                    "    slope_weight = clamp((params.heightmap_angle - %g) / %g, 0, 1);"
                    % (entry.slope - entry.blend / 2.0, entry.blend)
                )
                code.append("    for (int i = 0; i < coefs.length(); ++i) {")
                code.append("        coefs[i] = mix(%s_coefs[i], coefs[i], slope_weight);" % entry.texture_control.name)
                code.append("    }")
            previous = entry
        code.append("    return coefs;")
        code.append("}")

    def color_func_call(self, code):
        code.append("    vec4 %s_coefs[NB_COEFS_VEC] = detail_%s(params);" % (self.name, self.name))


class BiomeTextureControlEntry(object):
    def __init__(self, texture_control, value, blend):
        self.texture_control = texture_control
        self.value = value
        self.blend = blend


class BiomeControl(TextureControl):
    def __init__(self, name, biome_name, entries):
        TextureControl.__init__(self, name)
        self.biome_name = biome_name
        self.entries = entries

    def get_sources_names(self):
        sources = set([self.biome_name])
        for entry in self.entries:
            sources.update(entry.texture_control.get_sources_names())
        return sources

    def collect_required_data(self, data):
        data.setdefault(self.biome_name, set()).add('height')
        for entry in self.entries:
            entry.texture_control.collect_required_data(data)

    def set_shader(self, shader):
        TextureControl.set_shader(self, shader)
        for entry in self.entries:
            entry.texture_control.set_shader(shader)

    def fragment_uniforms(self, code):
        TextureControl.fragment_uniforms(self, code)
        # self.biome.fragment_uniforms(code)
        for entry in self.entries:
            entry.texture_control.fragment_uniforms(code)

    def fragment_extra(self, code):
        TextureControl.fragment_extra(self, code)
        for entry in self.entries:
            entry.texture_control.fragment_extra(code)
        code.append("vec4[NB_COEFS_VEC] detail_%s(TextureControlParams params)" % self.name)
        code.append("{")
        code.append("    vec4 coefs[NB_COEFS_VEC];")
        code.append("    float biome_weight;")
        code.append("    float biome_value = params.%s_height;" % self.biome_name)
        for entry in self.entries:
            entry.texture_control.color_func_call(code)
        previous = None
        for entry in self.entries:
            if previous is None:
                code.append("    coefs = %s_coefs;" % entry.texture_control.name)
            else:
                code.append(
                    "    biome_weight = clamp((biome_value - %g) / %g, 0, 1);"
                    % (entry.value - entry.blend / 2.0, entry.blend)
                )
                code.append("    for (int i = 0; i < coefs.length(); ++i) {")
                code.append("        coefs[i] = mix(%s_coefs[i], coefs[i], biome_weight);" % entry.texture_control.name)
                code.append("    }")
            previous = entry
        code.append("    return coefs;")
        code.append("}")

    def color_func_call(self, code):
        code.append("    vec4[NB_COEFS_VEC] %s_coefs = detail_%s(params);" % (self.name, self.name))


class MixTextureControl(TextureControl):
    def __init__(self, name, textures_control):
        TextureControl.__init__(self, name)
        self.textures_control = textures_control
        self.required_data = {}
        self.collect_required_data(self.required_data)

    def get_sources_names(self):
        return self.textures_control.get_sources_names()

    def collect_required_data(self, data):
        self.textures_control.collect_required_data(data)

    def set_shader(self, shader):
        TextureControl.set_shader(self, shader)
        self.textures_control.set_shader(shader)

    def fragment_uniforms(self, code):
        TextureControl.fragment_uniforms(self, code)
        self.textures_control.fragment_uniforms(code)
        code.append("#define NB_COEFS_VEC {}".format(self.nb_coefs))

    def fragment_extra(self, code):
        TextureControl.fragment_extra(self, code)
        code.append("struct TextureControlParams {")
        for source_name, data in self.required_data.items():
            # TODO: Nested structs not allowed in GLSL 1.20
            # code.append("    struct {")
            for entry in data:
                code.append("        float %s_%s;" % (source_name, entry))
            # code.append("    } %s;" % source_name)
        code.append("};")
        self.textures_control.fragment_extra(code)
        for category in self.dictionary.texture_categories.keys():
            self.resolve_coefs(code, category)

    def resolve_coefs(self, code, category):
        code.append("vec4 resolve_%s_%s(vec4 coefs[NB_COEFS_VEC], vec2 position) {" % (self.name, category))
        code.append("    float coef;")
        code.append("    vec4 result = vec4(0.0);")
        for block_id in self.dictionary.blocks.keys():
            index = self.dictionary.blocks_index[block_id]
            major = index // 4
            minor = index % 4
            code.append("    coef = coefs[%d][%d];" % (major, minor))
            code.append("    if (coef > 0) {")
            code.append(
                "      vec3 tex_%s = %s;"
                % (
                    block_id,
                    self.shader.data_source.get_source_for('{}_{}'.format(block_id, category), 'position'),
                )
            )
            code.append("      result.rgb = mix(result.rgb, tex_%s, coef);" % (block_id))
            code.append("    }")
        code.append("    result.w = 1.0;")
        code.append("    return result;")
        code.append("}")

    def create_shader_configuration(self, appearance):
        # TODO: This hack should be removed
        # self.nb_coefs = appearance.texture_source.nb_blocks
        # self.dictionary = appearance.texture_source
        self.nb_coefs = appearance.nb_blocks
        self.dictionary = appearance

    def color_func_call(self, code):
        code.append("TextureControlParams params;")
        for source_name, data in self.required_data.items():
            for entry in data:
                # TODO: heightmap data is already calculated by detailmap, we should do this for all the sources.
                if source_name == 'heightmap':
                    source_value = entry
                else:
                    source_value = self.shader.data_source.get_source_for('%s_%s' % (entry, source_name), 'uv')
                code.append("    params.%s_%s = %s;" % (source_name, entry, source_value))
        self.textures_control.color_func_call(code)
        code.append("vec4 coefs[NB_COEFS_VEC] = %s_coefs;" % self.textures_control.name)

    def get_value(self, code, category):
        code.append("vec4 %s_%s = resolve_%s_%s(coefs, position);" % (self.name, category, self.name, category))
