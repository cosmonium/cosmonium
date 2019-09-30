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

from ..support.ply import lex
from ..support.ply import yacc

import sys

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
    r'[\+-]?((\d*\.\d+)([eE][\+-]?\d+)?|[\+-]?([1-9]\d*[eE][\+-]?\d+))'
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

def p_definition_list(p):
    '''definition_list : definition_list definition'''
    p[0] = p[1]
    p[0].append(p[2])

def p_definition_list_1(p):
    '''definition_list : definition'''
    p[0]=[p[1]]

def p_definition_without_alias(p):
    ''' definition : NAME NAME INT '{' entry_list '}'
                   | NAME INT '{' entry_list '}'
                   | INT '{' entry_list '}'
    '''
    item_parent = None
    item_alias = None
    if len(p) == 7:
        disposition = p[1]
        item_type = p[2]
        item_name = p[3]
        item_data = p[5]
    elif len(p) == 6:
        disposition = 'Add'
        item_type = p[1]
        item_name = p[2]
        item_data = p[4]
    else:
        disposition = 'Add'
        item_type = 'Body'
        item_name = p[1]
        item_data = p[3]
    #print("Got definition of ", item_type, item_name, "of", item_parent)
    #print(item_data)
    p[0] = [disposition, item_type, item_name, item_parent, item_alias, item_data]

def p_definition_with_alias(p):
    ''' definition : NAME NAME INT STRING '{' entry_list '}'
                   | NAME INT STRING '{' entry_list '}'
                   | INT STRING '{' entry_list '}'
    '''
    item_parent = None
    if len(p) == 8:
        disposition = p[1]
        item_type = p[2]
        item_name = p[3]
        item_alias = p[4]
        item_data = p[6]
    elif len(p) == 7:
        disposition = 'Add'
        item_type = p[1]
        item_name = p[2]
        item_alias = p[3]
        item_data = p[5]
    else:
        disposition = 'Add'
        item_type = 'Body'
        item_name = p[1]
        item_alias = p[2]
        item_data = p[4]
    #print("Got definition of ", item_type, item_name, "of", item_parent)
    #print(item_data)
    p[0] = [disposition, item_type, item_name, item_parent, item_alias, item_data]


def p_definition_without_parent(p):
    ''' definition : NAME NAME STRING '{' entry_list '}'
                   | NAME STRING '{' entry_list '}'
                   | STRING '{' entry_list '}'
    '''
    item_parent = None
    item_alias = None
    if len(p) == 7:
        disposition = p[1]
        item_type = p[2]
        item_name = p[3]
        item_data = p[5]
    elif len(p) == 6:
        disposition = 'Add'
        item_type = p[1]
        item_name = p[2]
        item_data = p[4]
    else:
        disposition = 'Add'
        item_type = 'Body'
        item_name = p[1]
        item_data = p[3]
    #print("Got definition of ", item_type, item_name, "of", item_parent)
    #print(item_data)
    p[0] = [disposition, item_type, item_name, item_parent, item_alias, item_data]

def p_definition_with_parent(p):
    ''' definition : NAME NAME STRING STRING '{' entry_list '}'
                   | NAME STRING STRING '{' entry_list '}'
                   | STRING STRING '{' entry_list '}'
    '''
    item_alias = None
    if len(p) == 8:
        disposition = p[1]
        item_type = p[2]
        item_name = p[3]
        item_parent = p[4]
        item_data = p[6]
    elif len(p) == 7:
        disposition = 'Add'
        item_type = p[1]
        item_name = p[2]
        item_parent = p[3]
        item_data = p[5]
    else:
        disposition = 'Add'
        item_type = 'Body'
        item_name = p[1]
        item_parent = p[2]
        item_data = p[4]
    #print("Got definition of ", item_type, item_name, "of", item_parent)
    #print(item_data)
    p[0] = [disposition, item_type, item_name, item_parent, item_alias, item_data]

def p_definition_without_name(p):
    ''' definition : NAME '{' entry_list '}'
    '''
    item_parent = None
    item_alias = None
    disposition = 'Add'
    item_type = p[1]
    item_name = None
    item_data = p[3]
    #print("Got definition of ", item_type, item_name, "of", item_parent)
    #print(item_data)
    p[0] = [disposition, item_type, item_name, item_parent, item_alias, item_data]


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

parser = yacc.yacc(tabmodule='ssc_parsetab', write_tables=False, debug=False)

def parse(data, debug=0):
    parser.error = 0
    p = parser.parse(data, lexer=lexer, debug=debug)
    if parser.error:
        return None
    return p

if __name__ == '__main__':
    if len(sys.argv) == 2:
        data = open(sys.argv[1]).read()
        struct = parse(data)
        if not struct:
            raise SystemExit
        print(struct)
