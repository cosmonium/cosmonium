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

"""Parser for Celestia asterism data files.

Builds :class:`~NamedAsterism` objects from the PLY-parsed token stream and
registers them in the universe.
"""

import builtins
import io
import logging
import sys

from ply import lex, yacc
from ply.lex import Token

from ..astro import bayer
from ..astro.orbits import FixedPosition
from ..catalogs import objectsDB
from ..components.annotations.asterism import NamedAsterism

logger = logging.getLogger('asterisms')


def Rule(r):
    def set_rule(f):
        f.__doc__ = r
        return f

    return set_rule


tokens = ('STRING',)

literals = ['(', ')', '[', ']', '{', '}']


# Ignored characters
t_ignore = " \t"
t_ignore_COMMENT = r'\#.*'


@Token(r'\".*?\"')
def t_STRING(t):
    t.value = t.value[1:-1]
    return t


@Token(r'(\r?\n)+')
def t_newline(t):
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    logger.warning("Illegal character '%s'", t.value[0])
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()


precedence = ()


@Rule('''asterisms : asterisms_list''')
def p_asterims(p):
    p[0] = p[1]


@Rule('''asterisms_list : asterisms_list asterism''')
def p_asterisms_list(p):
    p[0] = p[1]
    p[0].append(p[2])


@Rule('''asterisms_list : asterism''')
def p_asterisms_list_1(p):
    p[0] = [p[1]]


@Rule('''asterism : STRING '[' segments_list ']' ''')
def p_asterism(p):
    p[0] = [p[1], p[3]]


@Rule('''segments_list : segments_list segment''')
def p_segments_list(p):
    p[0] = p[1]
    p[0].append(p[2])


@Rule('''segments_list : segment''')
def p_entry_list_1(p):
    p[0] = [p[1]]


@Rule('''segments_list : empty''')
def p_entry_list_2(p):
    p[0] = []


@Rule('''segment : '[' string_list ']' ''')
def p_segment(p):
    p[0] = p[2]


@Rule('''string_list : string_list STRING''')
def p_string_list(p):
    p[0] = p[1]
    p[0].append(p[2])


@Rule('''string_list : STRING''')
def p_float_list_1(p):
    p[0] = [p[1]]


@Rule('''string_list : empty''')
def p_string_list_2(p):
    p[0] = []


@Rule('''empty : ''')
def p_empty(p):
    pass


# Catastrophic error handler


def p_error(p):
    if p:
        logger.error("Syntax error at token %s line %d: %s", p.type, p.lineno, p.value)
    else:
        logger.error("SYNTAX ERROR AT EOF")


parser = yacc.yacc(tabmodule='asterism_parsetab', write_tables=False, debug=False)


def parse(data, debug=0):
    parser.error = 0
    p = parser.parse(data, lexer=lexer, debug=debug)
    if parser.error:
        return None
    return p


def create_asterism(universe, name, text_segments):
    segments = []
    for text_segment in text_segments:
        segment = []
        for star_name in text_segment:
            star = objectsDB.get(bayer.encode_name(star_name))
            if star is not None:
                if not isinstance(star.anchor.orbit, FixedPosition):
                    star = star.parent
                segment.append(star.anchor)
            else:
                logger.warning("Could not find star '%s'", star_name)
        segments.append(segment)
    asterism = NamedAsterism(name)
    asterism.set_segments_list(segments)
    universe.add_component(asterism)


def load(filename, universe, context, debug=0):
    filepath = context.find_data(filename)
    if filepath is not None:
        logger.info("Loading %s", filepath)
        builtins.base.splash.set_text("Loading %s" % filepath)
        data = io.open(filepath, encoding='iso8859-1').read()
        asterisms = parse(data, debug)
        for asterism in asterisms:
            create_asterism(universe, asterism[0], asterism[1])
    else:
        logger.warning("File not found: %s", filename)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        data = open(sys.argv[1]).read()
        struct = parse(data)
        if not struct:
            raise SystemExit
        print(struct)
