#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


"""
Pytest configuration file for Cosmonium tests.

This file provides global fixtures for testing.
"""

import pytest

# ============================================================================
# Runner copied from Panda3D test infrastructure to perform GLSL tests
# ============================================================================

# This is the template for the compute shader that is used by run_glsl_test.
# It defines an assert() macro that writes failures to a buffer, indexed by
# line number.
# The reset() function serves to prevent the _triggered variable from being
# optimized out in the case that the assertions are being optimized out.
GLSL_COMPUTE_TEMPLATE = """#version {version}
{extensions}

layout(local_size_x = 1, local_size_y = 1) in;

{preamble}

layout(r8ui) uniform writeonly uimageBuffer _triggered;

void _reset() {{
    imageStore(_triggered, 0, uvec4(0, 0, 0, 0));
    memoryBarrier();
}}

void _assert(bool cond, int line) {{
    if (!cond) {{
        imageStore(_triggered, line, uvec4(1));
    }}
}}

#define assert(cond) _assert(cond, __LINE__)

void main() {{
    _reset();
{body}
}}
"""


def run_glsl_test(gsg, body, preamble="", inputs={}, version=150, exts=set(), state=None):
    """Runs a GLSL test on the given GSG.  The given body is executed in the
    main function and should call assert().  The preamble should contain all
    of the shader inputs."""

    from panda3d.core import GeomEnums, RenderState, Shader, ShaderAttrib, Texture

    if not gsg.supports_compute_shaders or not gsg.supports_glsl:
        pytest.skip("compute shaders not supported")

    if not gsg.supports_buffer_texture:
        pytest.skip("buffer textures not supported")

    exts = exts | {'GL_ARB_compute_shader', 'GL_ARB_shader_image_load_store'}
    missing_exts = sorted(ext for ext in exts if not gsg.has_extension(ext))
    if missing_exts:
        pytest.skip("missing extensions: " + ' '.join(missing_exts))

    extensions = ''
    for ext in exts:
        extensions += '#extension {ext} : require\n'.format(ext=ext)

    __tracebackhide__ = True

    preamble = preamble.strip()
    body = body.rstrip().lstrip('\n')
    code = GLSL_COMPUTE_TEMPLATE.format(version=version, extensions=extensions, preamble=preamble, body=body)
    line_offset = code[: code.find(body)].count('\n') + 1
    shader = Shader.make_compute(Shader.SL_GLSL, code)
    assert shader, code

    # Create a buffer to hold the results of the assertion.  We use one byte
    # per line of shader code, so we can show which lines triggered.
    result = Texture("")
    result.set_clear_color((0, 0, 0, 0))
    result.setup_buffer_texture(code.count('\n'), Texture.T_unsigned_byte, Texture.F_r8i, GeomEnums.UH_static)

    # Build up the shader inputs
    attrib = ShaderAttrib.make(shader)
    for name, value in inputs.items():
        attrib = attrib.set_shader_input(name, value)
    attrib = attrib.set_shader_input('_triggered', result)

    if not state:
        state = RenderState.make(attrib)
    else:
        state = state.set_attrib(attrib)

    # Run the compute shader.
    engine = gsg.get_engine()
    try:
        engine.dispatch_compute((1, 1, 1), state, gsg)
    except AssertionError:
        assert False, "Error executing compute shader:\n" + code

    # Download the texture to check whether the assertion triggered.
    assert engine.extract_texture_data(result, gsg)
    triggered = result.get_ram_image()
    if any(triggered):
        count = len(triggered) - triggered.count(0)
        lines = body.split('\n')
        formatted = ''
        for i, line in enumerate(lines):
            if triggered[i + line_offset]:
                formatted += '=>  ' + line + '\n'
            else:
                formatted += '    ' + line + '\n'
        pytest.fail("{0} GLSL assertions triggered:\n{1}".format(count, formatted))
