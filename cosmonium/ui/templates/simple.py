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


from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import TYPE_CHECKING

from .expression import PythonExpressionParser

if TYPE_CHECKING:
    from .expression import PythonExpression


class Section(ABC):

    @abstractmethod
    def render(self, global_vars) -> str: ...


class TextSection(Section):
    def __init__(self, text: str):
        self.text = text

    def render(self, global_vars) -> str:
        return self.text

    def __repr__(self):
        return self.text


class ExpressionSection(Section):
    def __init__(self, expression: PythonExpression):
        self.expression = expression

    def render(self, global_vars) -> str:
        return str(self.expression.execute(global_vars))

    def __repr__(self):
        return '{{' + self.expression.source + '}}'


class SimpleTemplate:
    def __init__(self, sections: list[Section]):
        self.sections = sections

    def render(self, global_vars) -> str:
        return "".join(section.render(global_vars) for section in self.sections)

    def __repr__(self):
        return f'"{"".join(repr(section) for section in self.sections)}"'


class SimpleTemplateParser:

    opening = '{{'
    closing = '}}'
    delimiters = re.compile(f'({re.escape(opening)}|{re.escape(closing)})')

    def __init__(self):
        self.in_text = True

    def create_template(self, text: str) -> SimpleTemplate:
        expression_parser = PythonExpressionParser()
        tokens = self.delimiters.split(text)
        sections = []
        for token in tokens:
            if token == self.opening:
                if self.in_text:
                    self.in_text = False
                else:
                    raise ValueError('Opening delimiter in expression')
            elif token == self.closing:
                if not self.in_text:
                    self.in_text = True
                else:
                    raise ValueError('Closing delimiter without opening delimiter in expression')
            else:
                if self.in_text:
                    sections.append(TextSection(token))
                else:
                    expression = expression_parser.compile_expression(token)
                    sections.append(ExpressionSection(expression))
        return SimpleTemplate(sections)


if __name__ == '__main__':
    parser = SimpleTemplateParser()
    template = parser.create_template('{{foo}} bar {{some}}thing')
    print(template)
    print(template.render({'foo': 'a', 'some': 'b'}))
