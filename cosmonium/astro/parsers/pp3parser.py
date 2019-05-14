from __future__ import print_function
from __future__ import absolute_import

from cosmonium.astro import units, astro

import sys
import re

class PP3LineParser(object):
    name_regex = re.compile('(\w+\s+\d+|;)')
    comment_regex = re.compile('\s*#.*$')
    switch_regex = re.compile('(\w{3})\s+(\d+)')
    def __init__(self):
        self.names = {}

    def parse_line(self, line):
        line = self.comment_regex.sub('', line)
        if line == '': return None
        return self.name_regex.findall(line)

    def load(self, filepath):
        asterisms = []
        segments = []
        segment = []
        with file(filepath) as data:
            for line in data.readlines():
                elements = self.parse_line(line.strip())
                if elements is not None:
                    for entry in elements:
                        if entry != ';':
                            entry = self.switch_regex.sub(r'\2 \1', entry)
                            segment.append(entry)
                        else:
                            segments.append(segment)
                            segment = []
                else:
                    if len(segments) > 0:
                        asterisms.append(segments)
                        segments = []
        if len(segments) > 0:
            asterisms.append(segments)
        return asterisms

def asterism_yaml(stream, asterisms):
    for (i, asterism) in enumerate(asterisms):
        stream.write("- asterism:\n")
        stream.write("    name: asterism%d\n" % (i + 1))
        stream.write("    segments:\n")
        for segment in asterism:
            stream.write("      - [%s]\n" % ', '.join(segment))

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parser = PP3LineParser()
        asterisms = parser.load(sys.argv[1])
        with file("asterisms.yaml", "w") as stream:
            asterism_yaml(stream, asterisms)
