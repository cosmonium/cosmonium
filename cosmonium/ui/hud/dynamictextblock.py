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


from abc import ABC, abstractmethod
from .textblock import TextBlock


class DynamicTextBlockEntryInterface(ABC):

    @abstractmethod
    def is_valid(self) -> bool: ...

    @abstractmethod
    def has_entries(self) -> bool: ...


class DynamicTextBlockEntry(DynamicTextBlockEntryInterface):
    def __init__(self, condition, title, template):
        self.condition = condition
        self.title = title
        self.template = template

    def has_entries(self) -> bool:
        return False

    def is_valid(self, global_vars) -> bool:
        return not self.condition or self.condition.execute(global_vars)

    def render(self, global_vars) -> str:
        return self.template.render(global_vars)


class DynamicTextBlockEntries(DynamicTextBlockEntryInterface):
    def __init__(self, condition, entries):
        self.condition = condition
        self.entries = entries

    def has_entries(self) -> bool:
        return True

    def is_valid(self, global_vars) -> bool:
        return not self.condition or self.condition.execute(global_vars)


class DynamicTextBlock(TextBlock):
    def __init__(self, id_, location, align, down, count, entries, parent=None):
        TextBlock.__init__(self, id_, location, align, down, count, parent=parent)
        self.entries = entries
        self._cursor = 0

    def _update(self, entries, global_vars):
        for entry in entries:
            if entry.is_valid(global_vars):
                if entry.has_entries():
                    self._update(entry.entries, global_vars)
                else:
                    if entry.title is None:
                        text = entry.render(global_vars)
                    else:
                        text = entry.title + ": " + entry.render(global_vars)
                    if self._cursor == self.count:
                        line = self.create_line(self._cursor)
                        self.instances.append(line)
                        self.text.append("")
                        self.count += 1
                        self.update_instance()
                    self.set(self._cursor, text)
                    self._cursor += 1

    def update(self, global_vars):
        self._cursor = 0
        self._update(self.entries, global_vars)
        for i in range(self._cursor, self.count):
            self.set(i, "")
