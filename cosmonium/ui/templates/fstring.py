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


from .expression import PythonExpressionParser


class FStringTemplate:
    def __init__(self, expression: str):
        self.expression = expression

    def render(self, global_vars) -> str:
        return self.expression.execute(global_vars)

    def __repr__(self):
        return self.expression.source


class FStringTemplateParser:

    def create_template(self, text: str) -> FStringTemplate:
        expression_parser = PythonExpressionParser()
        code = 'f"""' + text + '"""'
        expression = expression_parser.compile_expression(code)
        return FStringTemplate(expression)


if __name__ == '__main__':
    parser = FStringTemplateParser()
    template = parser.create_template('{foo:f} bar {some}thing')
    print(template)
    print(template.render({'foo': 1, 'some': 'b'}))
