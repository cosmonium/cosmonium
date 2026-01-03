#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


from ..shadernoise import BasicNoiseSource, NoiseSource


class NoiseAdd(NoiseSource):
    def __init__(self, noises, name=None):
        NoiseSource.__init__(self, name, 'add')
        self.noises = noises

    def get_id(self):
        return "add-" + '-'.join(map(lambda x: x.get_id(), self.noises))

    def noise_uniforms(self, code):
        for noise in self.noises:
            noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        for noise in self.noises:
            noise.noise_extra(program, code)

    def noise_func(self, code):
        for noise in self.noises:
            noise.noise_func(code)
        code.append('float noise_add_%d(vec3 point)' % self.num_id)
        code.append('{')
        for i, noise in enumerate(self.noises):
            code.append('  float value_%d;' % i)
        for i, noise in enumerate(self.noises):
            noise.noise_value(code, 'value_%d' % i, 'point')
        add = ' + '.join(map(lambda i: 'value_%d' % i, range(len(self.noises))))
        code.append('  return %s;' % add)
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_add_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        for noise in self.noises:
            noise.update(instance)

    def get_user_parameters(self):
        parameters = []
        for noise in self.noises:
            parameters += noise.get_user_parameters()
        return parameters


class NoiseSub(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'sub')
        self.noise_a = noise_a
        self.noise_b = noise_b

    def get_id(self):
        return self.noise_a.get_id() + "-sub-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_sub_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return value_a - value_b;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_sub_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()


class NoiseMul(NoiseSource):
    def __init__(self, noises, name=None):
        NoiseSource.__init__(self, name, 'mul')
        self.noises = noises

    def get_id(self):
        return "mul-" + '-'.join(map(lambda x: x.get_id(), self.noises))

    def noise_uniforms(self, code):
        for noise in self.noises:
            noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        for noise in self.noises:
            noise.noise_extra(program, code)

    def noise_func(self, code):
        for noise in self.noises:
            noise.noise_func(code)
        code.append('float noise_mul_%d(vec3 point)' % self.num_id)
        code.append('{')
        for i, noise in enumerate(self.noises):
            code.append('float value_%d;' % i)
        for i, noise in enumerate(self.noises):
            noise.noise_value(code, 'value_%d' % i, 'point')
        mul = ' * '.join(map(lambda i: 'value_%d' % i, range(len(self.noises))))
        code.append('  return %s;' % mul)
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_mul_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        for noise in self.noises:
            noise.update(instance)

    def get_user_parameters(self):
        parameters = []
        for noise in self.noises:
            parameters += noise.get_user_parameters()
        return parameters


class NoiseDiv(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'div')
        self.noise_a = noise_a
        self.noise_b = noise_b

    def get_id(self):
        return self.noise_a.get_id() + "-div-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_div_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return value_a / value_b;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_div_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()


class NoisePow(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'pow')
        self.noise_a = noise_a
        self.noise_b = noise_b

    def get_id(self):
        return self.noise_a.get_id() + "-pow-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_pow_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return pow(value_a, value_b);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_pow_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()


class NegNoise(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'neg')

    def get_id(self):
        return 'neg-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        tmp = self.create_tmp(code)
        self.noise.noise_value(code, tmp, point)
        code.append('          %s = -(%s);' % (value, tmp))
