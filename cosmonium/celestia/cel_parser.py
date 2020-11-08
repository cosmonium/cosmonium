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

from ply import lex
from ply import yacc
from ..dircontext import defaultDirContext
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

def p_program(p):
    '''program : '{' commands_list '}' '''
    p[0] = p[2]

def p_commands_list(p):
    '''commands_list : commands_list command'''
    p[0] = p[1]
    p[0].append(p[2])

def p_definition_list_1(p):
    '''commands_list : command'''
    p[0]=[p[1]]

def p_command(p):
    '''command : NAME '{' entry_list '}' '''
    p[0] = [p[1], p[3]]

def p_entry_list(p):
    '''entry_list : entry_list entry'''
    p[0] = p[1]
    entry = p[2]
    p[0][entry[0]] = entry[1]

def p_entry_list_1(p):
    '''entry_list : entry'''
    p[0] = {}
    entry = p[1]
    p[0][entry[0]] = entry[1]

def p_entry_list_2(p):
    '''entry_list : empty'''
    p[0] = {}

def p_entry(p):
    '''entry : NAME INT
             | NAME FLOAT
             | NAME STRING
             | NAME BOOL
             | NAME vector
             | NAME hash'''
    p[0] = [p[1], p[2]]

def p_vector(p):
    '''vector : '[' float_list ']' '''
    p[0] = p[2]

def p_float_list(p):
    '''float_list : float_list FLOAT
                  | float_list INT'''
    p[0] = p[1]
    p[0].append(p[2])

def p_float_list_1(p):
    '''float_list : FLOAT
                  | INT'''
    p[0] = [p[1]]

def p_float_list_2(p):
    '''float_list : empty'''
    p[0] = []

def p_hash(p):
    '''hash : '{' entry_list '}' '''
    p[0] = p[2]

def p_empty(p):
    '''empty : '''

# Catastrophic error handler

def p_error(p):
    if p:
        print("Syntax error at token", p.type, "line", p.lineno, ":", p.value)
    else:
        print("SYNTAX ERROR AT EOF")

parser = yacc.yacc(tabmodule='cel_parsetab', write_tables=False, debug=False)

def parse(data, debug=0):
    parser.error = 0
    p = parser.parse(data, lexer=lexer, debug=debug)
    if parser.error:
        return None
    return p

def load(filename, context=defaultDirContext, debug=0):
    filepath = context.find_script(filename)
    if filepath is not None:
        print("Loading", filepath)
        data = io.open(filepath, encoding='utf-8', errors='surrogateescape').read()
        struct = parse(data, debug)
        return struct
    else:
        print("File not found", filename)
        return None

if __name__ == '__main__':
    if len(sys.argv) == 2:
        data = open(sys.argv[1]).read()
        struct = parse(data)
        if not struct:
            raise SystemExit
        print(struct)
