# -*- coding: utf-8 -*-
#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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


from .. import settings
import re

# The greek letter encoding follows gthe SIMBAD convention : http://simbad.u-strasbg.fr/guide/chA.htx
greek_utf8_map = {
    "ALF": u'α',
    "BET": u'β',
    "GAM": u'γ',
    "DEL": u'δ',
    "EPS": u'ε',
    "ZET": u'ζ',
    "ETA": u'η',
    "TET": u'θ',
    "IOT": u'ι',
    "KAP": u'κ',
    "LAM": u'λ',
    "MU.": u'μ',
    "NU.": u'ν',
    "KSI": u'ξ',
    "OMI": u'ο',
    "PI.": u'π',
    "RHO": u'ρ',
    "SIG": u'σ',
    "TAU": u'τ',
    "UPS": u'υ',
    "PHI": u'φ',
    "KHI": u'χ',
    "PSI": u'ψ',
    "OME": u'ω',
}

greek_word_map = {
    "ALF": 'Alpha',
    "BET": 'Beta',
    "GAM": 'Gamma',
    "DEL": 'Delta',
    "EPS": 'Epsilon',
    "ZET": 'Zeta',
    "ETA": 'Eta',
    "TET": 'Theta',
    "IOT": 'Iota',
    "KAP": 'Kappa',
    "LAM": 'Lambda',
    "MU.": 'Mu',
    "NU.": 'Nu',
    "KSI": 'Xi',
    "OMI": 'Omicron',
    "PI.": 'Pi',
    "RHO": 'Rho',
    "SIG": 'Sigma',
    "TAU": 'Tau',
    "UPS": 'Upsilon',
    "PHI": 'Phi',
    "KHI": 'Chi',
    "PSI": 'Psi',
    "OME": 'Omega',
}

greek_canonize = {
    'ALP': 'ALF',
    'THE': 'TET',
    'MU': 'MU.',
    'NU': 'NU.',
    'XI': 'KSI',
    'XI.': 'KSI',
    'PI': 'PI.',
    'CHI': 'KHI',
}

constellations = [
    'Aql',
    'And',
    'Ara',
    'Lib',
    'Cet',
    'Ari',
    'Pyx',
    'Boo',
    'Cae',
    'Cha',
    'Cnc',
    'Cap',
    'Car',
    'Cas',
    'Cen',
    'Cep',
    'Com',
    'CVn',
    'Aur',
    'Col',
    'Cir',
    'Crv',
    'Crt',
    'CrA',
    'CrB',
    'Cru',
    'Cyg',
    'Del',
    'Dor',
    'Dra',
    'Sct',
    'Eri',
    'Sge',
    'For',
    'Gem',
    'Cam',
    'CMa',
    'UMa',
    'Gru',
    'Her',
    'Hor',
    'Hya',
    'Hyi',
    'Ind',
    'Lac',
    'Mon',
    'Lep',
    'Leo',
    'Lup',
    'Lyn',
    'Lyr',
    'Ant',
    'Mic',
    'Mus',
    'Oct',
    'Aps',
    'Oph',
    'Ori',
    'Pav',
    'Peg',
    'Pic',
    'Per',
    'Equ',
    'CMi',
    'LMi',
    'Vul',
    'UMi',
    'Phe',
    'PsA',
    'Vol',
    'Psc',
    'Pup',
    'Nor',
    'Ret',
    'Sgr',
    'Sco',
    'Scl',
    'Ser',
    'Sex',
    'Men',
    'Tau',
    'Tel',
    'Tuc',
    'Tri',
    'TrA',
    'Aqr',
    'Vir',
    'Vel',
]

greek_abv_map = {}
for abv, text in greek_word_map.items():
    greek_abv_map[text] = abv

constellations_map = {}
for constellation in constellations:
    constellations_map[constellation.lower()] = constellation

greek_abv_match = re.compile(r"^([A-Z][A-Z\.]{0,2})(\d*) ([A-Za-z]{3})")

greek_word_match = re.compile(r"^([A-Za-z]+)(\d*) ")

superscripts = [u'⁰', u'¹', u'²', u'³', u'⁴', u'⁵', u'⁶', u'⁷', u'⁸', u'⁹']


def canonize_name(name):
    if not settings.convert_utf8:
        return name
    try:
        match = greek_abv_match.match(name)
        if match:
            (greek, number, const) = match.groups()
            if const.lower() in constellations_map:
                greek = greek.upper()
                if greek in greek_canonize:
                    name = name.replace(greek, greek_canonize[greek], 1)
    except (TypeError, ValueError):
        print(f"Invalid name '{name}'")
    return name


def decode_name(name):
    if not settings.convert_utf8:
        return name
    match = greek_abv_match.match(name)
    if match:
        (greek, number, const) = match.groups()
        if const.lower() in constellations_map:
            greek = greek.upper()
            if greek in greek_utf8_map:
                try:
                    name = name.replace(greek, greek_utf8_map[greek], 1)
                except UnicodeDecodeError:
                    print("Failure to decode", name, greek)
                    print(name.__class__, greek.__class__, greek_utf8_map[greek].__class__)
            if number != '':
                str_number = str(int(number))
                superscript = ''
                for c in str_number:
                    superscript += superscripts[int(c)]
                name = name.replace(number, superscript, 1)
    return name


def decode_names(encoded_names):
    names = []
    for name in encoded_names:
        names.append(decode_name(name))
    return names


def encode_name(name):
    match = greek_word_match.match(name)
    if match:
        (greek, number) = match.groups()
        if greek in greek_abv_map:
            name = name.replace(greek, greek_abv_map[greek], 1)
    return name
