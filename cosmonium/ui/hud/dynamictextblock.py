#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


from abc import ABC, abstractmethod
from .textblock import TextBlock


class DynamicTextBlockEntryInterface(ABC):

    @abstractmethod
    def compile(self, env) -> None:
        ...

    @abstractmethod
    def is_valid(self) -> bool:
        ...

    @abstractmethod
    def has_entries(self) -> bool:
        ...


class DynamicTextBlockEntry(DynamicTextBlockEntryInterface):
    def __init__(self, condition_source, title, text_source):
        self.condition_source = condition_source
        self.title = title
        self.text_source = text_source
        self.condition = None
        self.template = None

    def compile(self, env):
        if self.condition_source is not None:
            self.condition = env.compile_expression(self.condition_source)
        else:
            self.condition = lambda: True
        self.template = env.create_template(self.text_source)

    def has_entries(self) -> bool:
        return False

    def is_valid(self) -> bool:
        return self.condition()

    def render(self) -> str:
        return self.template.render()


class DynamicTextBlockEntries(DynamicTextBlockEntryInterface):
    def __init__(self,  condition_source, entries):
        self.condition_source = condition_source
        self.entries = entries
        self.condition = None

    def compile(self, env):
        if self.condition_source is not None:
            self.condition = env.compile_expression(self.condition_source)
        else:
            self.condition = lambda: True
        for entry in self.entries:
            entry.compile(env)

    def has_entries(self) -> bool:
        return True

    def is_valid(self) -> bool:
        return self.condition()


class DynamicTextBlock(TextBlock):
    def __init__(self, id_, align, down, count, entries, owner=None):
        TextBlock.__init__(self, id_, align, down, count, owner)
        self.entries = entries
        self._cursor = 0

    def compile(self, env):
        for entry in self.entries:
            entry.compile(env)

    def _update(self, entries):
        for entry in entries:
            if entry.is_valid():
                if entry.has_entries():
                    self._update(entry.entries)
                else:
                    if entry.title is None:
                        text = entry.render()
                    else:
                        text = entry.title + ": " + entry.render()
                    if self._cursor == self.count:
                        line = self.create_line(self._cursor)
                        self.instances.append(line)
                        self.text.append("")
                        self.count += 1
                        self.update_instance()
                    self.set(self._cursor, text)
                    self._cursor += 1

    def update(self):
        self._cursor = 0
        self._update(self.entries)
        for i in range(self._cursor, self.count):
            self.set(i, "")
