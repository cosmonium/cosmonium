from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import Texture

from ..shaders import ShaderComponent
from ..textures import TextureBase
from ..dircontext import defaultDirContext

from math import cos, pi

class DetailTexture(TextureBase):
    def __init__(self, filename, context=defaultDirContext):
        self.filename = filename
        self.context = context
        self.texture = None

    def load(self, patch):
        if self.texture is None:
            filename=self.context.find_texture(self.filename)
            if filename is not None:
                try:
                    self.texture = loader.loadTexture(filename)
                    self.texture.set_format(Texture.F_srgb)
                    self.texture.setMinfilter(Texture.FTLinearMipmapLinear)
                    self.texture.setMagfilter(Texture.FTLinearMipmapLinear)
                    self.texture.setAnisotropicDegree(2)
                except IOError:
                    print("Could not load texture", self.filename)
            else:
                print("File", self.filename, "not found")
        return self.texture

    def apply(self, shape, shader_name):
        if self.texture is not None:
            shape.instance.set_shader_input(shader_name, self.texture)

class TextureControl(ShaderComponent):
    def __init__(self, name, heightmap=None, shader=None):
        ShaderComponent.__init__(self, shader)
        self.name = name
        self.heightmap = heightmap

    def set_heightmap(self, heightmap):
        self.heightmap = heightmap

    def color_func_call(self, code):
        pass

class SimpleTextureControl(TextureControl):
    def color_func_call(self, code):
        code.append("    vec3 %s_color = tex_%s_color;" % (self.name, self.name))

class ColormapLayer(object):
    def __init__(self, height, bottom=None, top=None):
        self.height = height
        self.bottom = bottom
        self.top = top

class HeightColorMap(TextureControl):

    def __init__(self, name, colormap):
        TextureControl.__init__(self, name)
        self.colormap = colormap

    def fragment_extra(self, code):
        TextureControl.fragment_extra(self, code)
        code.append("vec3 detail_%s(vec2 position, float height, vec2 uv, float angle)" % self.name)
        code.append("{")
        code.append("    vec3 texture_color;")
        code.append("    float base;")
        code.append("    float delta;")
        code.append("    vec3 bottom;")
        code.append("    vec3 top;")
        previous_layer = None
        for layer in self.colormap:
            if previous_layer is None:
                code.append("   if (height <= %g) {" % (layer.height))
                previous_layer = layer
            else:
                code.append("   } else if (height <= %g) {" % (layer.height))
            bottom = layer.bottom
            if bottom is None:
                bottom = previous_layer.top
            code.append('       bottom = vec3(%g, %g, %g);' % (bottom[0], bottom[1], bottom[2]))
            code.append('       top = vec3(%g, %g, %g);' % (layer.top[0], layer.top[1], layer.top[2]))
            code.append('       base = %g;' % (previous_layer.height))
            code.append('       delta = %g;' % (layer.height - previous_layer.height))
            previous_layer = layer
        code.append("   } else {")
        code.append('       top = vec3(%g, %g, %g);' % (layer.top[0], layer.top[1], layer.top[2]))
        code.append('       return top;')
        code.append('    }')
        code.append('    float e = (height - base) / delta;')
        code.append('    vec3 color = top * e + bottom * (1 - e);')
        code.append('    return color;')
        code.append('}')

    def color_func_call(self, code):
        code.append("    vec3 %s_color = detail_%s(position, height, uv, angle);" % (self.name, self.name))

class HeightTextureControlEntry(object):
    def __init__(self, texture_control, height, blend):
        self.texture_control = texture_control
        self.height = height
        self.blend = blend

class HeightTextureControl(TextureControl):
    def __init__(self, name, entries):
        TextureControl.__init__(self, name)
        self.entries = entries

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
        code.append("vec3 detail_%s(vec2 position, float height, vec2 uv, float angle)" % self.name)
        code.append("{")
        code.append("    vec3 texture_color;")
        code.append("    float height_weight;")
        for entry in self.entries:
            entry.texture_control.color_func_call(code)
        previous = None
        for entry in self.entries:
            if previous is None:
                code.append("    if (height <= %g) {" % (entry.height - entry.blend / 2.0))
                code.append("      texture_color = %s_color;" % entry.texture_control.name)
            else:
                code.append("    } else if (height <= %g) {" % (entry.height - entry.blend / 2.0))
                code.append("    height_weight = clamp((height - %g) / %g, 0, 1);" % (previous.height - previous.blend / 2.0, previous.blend))
                code.append("    texture_color = mix(%s_color, %s_color, height_weight);" % (previous.texture_control.name, entry.texture_control.name))
            previous = entry
        code.append("   } else {")
        code.append("      texture_color = %s_color;" % entry.texture_control.name)
        code.append('    }')
        code.append("    return texture_color;")
        code.append("}")

    def color_func_call(self, code):
        code.append("    vec3 %s_color = detail_%s(position, height, uv, angle);" % (self.name, self.name))

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
        code.append("vec3 detail_%s(vec2 position, float height, vec2 uv, float angle)" % self.name)
        code.append("{")
        code.append("    vec3 texture_color;")
        code.append("    float slope_weight;")
        for entry in self.entries:
            entry.texture_control.color_func_call(code)
        previous = None
        for entry in self.entries:
            if previous is None:
                code.append("    texture_color = %s_color;" % entry.texture_control.name)
            else:
                code.append("    slope_weight = clamp((angle - %g) / %g, 0, 1);" % (entry.slope - entry.blend / 2.0, entry.blend))
                code.append("    texture_color = mix(%s_color, texture_color, slope_weight);" % entry.texture_control.name)
            previous = entry
        code.append("    return texture_color;")
        code.append("}")

    def color_func_call(self, code):
        code.append("    vec3 %s_color = detail_%s(position, height, uv, angle);" % (self.name, self.name))

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

    def set_shader(self, shader):
        TextureControl.set_shader(self, shader)
        for entry in self.entries:
            entry.texture_control.set_shader(shader)

    def fragment_uniforms(self, code):
        TextureControl.fragment_uniforms(self, code)
        #self.biome.fragment_uniforms(code)
        for entry in self.entries:
            entry.texture_control.fragment_uniforms(code)

    def fragment_extra(self, code):
        TextureControl.fragment_extra(self, code)
        for entry in self.entries:
            entry.texture_control.fragment_extra(code)
        code.append("vec3 detail_%s(vec2 position, float height, vec2 uv, float angle)" % self.name)
        code.append("{")
        code.append("    vec3 texture_color;")
        code.append("    float biome_weight;")
        code.append("    float biome_value = %s;" % self.shader.data_source.get_source_for('height_%s' % self.biome_name, 'uv'))
        for entry in self.entries:
            entry.texture_control.color_func_call(code)
        previous = None
        for entry in self.entries:
            if previous is None:
                code.append("    texture_color = %s_color;" % entry.texture_control.name)
            else:
                code.append("    biome_weight = clamp((biome_value - %g) / %g, 0, 1);" % (entry.value - entry.blend / 2.0, entry.blend))
                code.append("    texture_color = mix(%s_color, texture_color, biome_weight);" % entry.texture_control.name)
            previous = entry
        code.append("    return texture_color;")
        code.append("}")

    def color_func_call(self, code):
        code.append("    vec3 %s_color = detail_%s(position, height, uv, angle);" % (self.name, self.name))
