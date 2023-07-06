#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from ..component import ShaderComponent
from .base import ShaderShadowInterface


class ShaderPSSMShadowMap(ShaderComponent, ShaderShadowInterface):

    fragment_requires = {'world_vertex'}

    def __init__(self, name):
        ShaderComponent.__init__(self)
        self.name = name
        self.num_splits = 5

    def get_id(self):
        name = 'pssm-' + str(self.num_splits) + '-' + self.name
        return name

    def fragment_uniforms(self, code):
        code.append(f"const int split_count = {self.num_splits};")
        code.append(f"uniform sampler2D PSSMShadowAtlas;")

        code.append(f"uniform mat4 pssm_mvps[split_count];")
        code.append(f"uniform float border_bias;")
        code.append(f"uniform float fixed_bias;")

    def fragment_inputs(self, code):
        code.append("in vec4 %s_lightcoord;" % self.name)

    def project(self, code):
        code.append('''
// Projects a point using the given mvp
vec3 project(mat4 mvp, vec3 p) {
    vec4 projected = mvp * vec4(p, 1);
    return (projected.xyz / projected.w) * vec3(0.5) + vec3(0.5);
}''')

    def fragment_extra(self, code):
        self.shader.fragment_shader.add_function(code, 'project', self.project)

    def shadow_for(self, code, light, light_direction, eye_light_direction):
        code.append('''
    // Find in which split the current point is present.
    int split = 99;
    float border_bias = 0.5 - (0.5 / (1.0 + border_bias));

    // Find the first matching split
    for (int i = 0; i < split_count; ++i) {
        vec3 coord = project(pssm_mvps[i], world_vertex);
        if (coord.x >= border_bias && coord.x <= 1 - border_bias &&
            coord.y >= border_bias && coord.y <= 1 - border_bias &&
            coord.z >= 0.0 && coord.z <= 1.0) {
            split = i;
            break;
        }
    }

    // Compute the shadowing factor
    if (split < split_count) {

        // Get the MVP for the current split
        mat4 mvp = pssm_mvps[split];

        // Project the current pixel to the view of the light
        vec3 projected = project(mvp, world_vertex);
        vec2 projected_coord = vec2((projected.x + split) / float(split_count), projected.y);
        // Apply a fixed bias based on the current split to diminish the shadow acne
        float ref_depth = projected.z - fixed_bias * 0.001 * (1 + 1.5 * split);

        // Check if the pixel is shadowed or not
        float depth_sample = textureLod(PSSMShadowAtlas, projected_coord, 0).x;
        float shadow_factor = step(ref_depth, depth_sample);

        local_shadow *= shadow_factor;
    }
''')
