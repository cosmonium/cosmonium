#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

from .. import units
from .parser import *

import sys
import re

class CSNParser(FixedFieldsParser):
    name_regex = re.compile('^(.{18})(.{13})')
    comment_regex = re.compile('\s*#.*$')
    def __init__(self):
        self.names = {}

    def parse_line(self, line):
        line = self.comment_regex.sub('', line)
        if line == '': return
        m = self.name_regex.search(line)
        if m is not None:
            (name, hr_id) = m.groups()
            name = name.rstrip(' ')
            hr_id = hr_id.rstrip(' ')
            self.names[hr_id] = name
        else:
            print("CSN: Invalid line", line)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parser = CSNParser()
        parser.load(sys.argv[1])
