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


def true_expression():
    return True


def false_expression():
    return False


def zero_expression():
    return 0


class PythonExpression:
    def __init__(self, source: str, global_vars):
        self.source = source
        self.code = compile(source, "<inline>", 'eval')
        self.global_vars = global_vars

    def execute(self, global_vars=None):
        if global_vars is None:
            global_vars = self.global_vars
        return eval(self.code, global_vars, {})

    def __call__(self):
        return eval(self.code, self.global_vars, {})


class PythonExpressionParser:

    def compile_expression(self, source: str, global_vars=None) -> PythonExpression:
        try:
            return PythonExpression(source, global_vars)
        except Exception:
            print(f"Error while compiling '{source}'")
            raise
