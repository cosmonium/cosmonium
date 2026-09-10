import os
import sys
from collections import OrderedDict

filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, filepath)
sys.path.insert(1, os.path.join(filepath, 'third-party'))

from cosmonium.parsers.yamlloader import YamlLoader  # noqa: E402


class UIPotExtractor:

    def __init__(self, output):
        self.output = output
        self.msgs = OrderedDict()

    def output_header(self):
        self.output.write("""# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR ORGANIZATION
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"POT-Creation-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"


""")

    def output_entry(self, entry, rule):
        context = rule.get('context')
        if context is not None:
            self.output.write('msgctxt "%s"\n' % context)
        self.output.write('msgid "%s"\n' % entry)
        self.output.write('msgstr ""\n')
        self.output.write('\n')

    def output_entries(self):
        for entry, rule in self.msgs.items():
            self.output_entry(entry, rule)

    def add_entry(self, msgid, rule={}):
        if not msgid.startswith('@'):
            self.msgs[msgid] = rule

    def parse(self, ui_config_file):
        basedir = os.path.dirname(ui_config_file)
        data = YamlLoader.load_file(ui_config_file)
        menus_file = data.get('menus')
        if menus_file is not None:
            if not os.path.isabs(menus_file):
                menus_file = os.path.join(basedir, menus_file)
            self.parse_menus(menus_file)

    def parse_submenu(self, data):
        for entry in data:
            if entry is None:
                continue
            title = entry.get('title')
            self.add_entry(title)
            entries = entry.get('entries')
            if entries is not None:
                self.parse_submenu(entries)

    def parse_menus(self, menus_file):
        data = YamlLoader.load_file(menus_file)
        for name, entries in data.get('menus', {}).items():
            self.parse_submenu(entries)


output = open(sys.argv[1], 'w')

parser = UIPotExtractor(output)
parser.output_header()
parser.parse(sys.argv[2])
parser.output_entries()

output.close()
