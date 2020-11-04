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

from ..annotations import NamedAsterism
from ..catalogs import objectsDB
from ..astro.orbits import FixedPosition
from ..astro import bayer
from ..dircontext import defaultDirContext
from ply import lex
from ply import yacc
from .. import utils

import sys
import io

tokens = ('STRING', 'NAME', 'INT', 'FLOAT', 'BOOL')

literals = ['(', ')', '[', ']', '{', '}']

# Ignored characters
t_ignore = " \t"
t_ignore_COMMENT = r'\#.*'

def t_BOOL(t):
    r'true|false'
    t.value = t.value == 'true'
    return t
 
def t_NAME(t):   
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    return t

def t_STRING(t):
    r'\".*?\"'
    t.value = t.value[1:-1]
    return t

def t_FLOAT(t):
    r'[\+-]?((\d*\.\d+)(E[\+-]?\d+)?|[\+-]?([1-9]\d*E[\+-]?\d+))'
    try:
        t.value = float(t.value)
    except ValueError:
        print("Float value too large %d", t.value)
        t.value = 0
    return t

def t_INT(t):
    r'[\+-]?\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t
 
def t_newline(t):
    r'(\r?\n)+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)
    
# Build the lexer
lexer = lex.lex()

precedence=()

def p_asterims(p):
    '''asterisms : asterisms_list'''
    p[0] = p[1]

def p_asterisms_list(p):
    '''asterisms_list : asterisms_list asterism'''
    p[0] = p[1]
    p[0].append(p[2])

def p_asterisms_list_1(p):
    '''asterisms_list : asterism'''
    p[0]=[p[1]]

def p_asterism(p):
    '''asterism : STRING '[' segments_list ']' '''
    p[0] = [p[1], p[3]]

def p_segments_list(p):
    '''segments_list : segments_list segment'''
    p[0] = p[1]
    p[0].append(p[2])

def p_entry_list_1(p):
    '''segments_list : segment'''
    p[0] = [p[1]]

def p_entry_list_2(p):
    '''segments_list : empty'''
    p[0] = []

def p_segment(p):
    '''segment : '[' string_list ']' '''
    p[0] = p[2]

def p_string_list(p):
    '''string_list : string_list STRING'''
    p[0] = p[1]
    p[0].append(p[2])

def p_float_list_1(p):
    '''string_list : STRING'''
    p[0] = [p[1]]

def p_string_list_2(p):
    '''string_list : empty'''
    p[0] = []

def p_empty(p):
    '''empty : '''

# Catastrophic error handler

def p_error(p):
    if p:
        print("Syntax error at token", p.type, "line", p.lineno, ":", p.value)
    else:
        print("SYNTAX ERROR AT EOF")

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
            #star = universe.find_by_name(star_name)
            star = objectsDB.get(bayer.encode_name(star_name))
            if star is not None:
                if not isinstance(star.orbit, FixedPosition):
                    star = star.parent
                segment.append(star)
            else:
                print("Could not find star", star_name)
        segments.append(segment)
    asterism = NamedAsterism(name)
    asterism.set_segments_list(segments)
    universe.add_component(asterism)

def load(filename, universe, context=defaultDirContext, debug=0):
    filepath = context.find_data(filename)
    if filepath is not None:
        print("Loading", filepath)
        base.splash.set_text("Loading %s" % filepath)
        data = io.open(filepath, encoding='iso8859-1').read()
        asterisms = parse(data, debug)
        for asterism in asterisms:
            create_asterism(universe, asterism[0], asterism[1])
    else:
        print("File not found", filepath)
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        data = open(sys.argv[1]).read()
        struct = parse(data)
        if not struct:
            raise SystemExit
        print(struct)
