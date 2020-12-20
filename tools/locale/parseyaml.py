import sys
import os
from builtins import list

filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
print(filepath)
sys.path.insert(0, filepath)
sys.path.insert(1, os.path.join(filepath, 'third-party'))

if sys.version_info >= (3, 0):
    import builtins
else:
    import __builtin__ as builtins

from cosmonium.parsers.yamlparser import YamlModuleParser
from cosmonium.dircontext import DirContext
from cosmonium.ui.splash import NoSplash
from cosmonium import settings

class FakeBase:
    splash = NoSplash()
    def destroy(self):
        pass

class TranslationYamlParser(YamlModuleParser):
    translation_rules = {
        'system': {'translate-list': ['name'],
                   'recurse': ['children']},
        'body': {'translate-list': ['name']},
        'constellation': {'translate': ['name'],
                          'context': 'constellation'},
        'custom-translate': {'translate-list': ['names']},
        }
    aliases = {'planet': 'body', 
               'dwarfplanet': 'body',
               'moon': 'body',
               'minormoon': 'body',
               'asteroid': 'body',
               'lostmoon': 'body',
               'comet': 'body',
               'interstellar': 'body',
               'spacecraft': 'body',
               'star': 'body',
               'constellation': 'constellation'
               }

    output = None

    @classmethod
    def output_header(cls):
        cls.output.write("""# SOME DESCRIPTIVE TITLE.
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

    @classmethod
    def output_entry(cls, entry, rule):
        context = rule.get('context')
        if context is not None:
            cls.output.write('msgctxt "%s"\n' % context)
        cls.output.write('msgid "%s"\n' % entry)
        cls.output.write('msgstr ""\n')
        cls.output.write('\n')

    @classmethod
    def decode_object(cls, data):
        if len(data) == 1:
            object_type = list(data)[0]
            data = data[object_type]
        else:
            object_type = data.get('type')
        rules = cls.translation_rules.get(cls.aliases.get(object_type, object_type))
        if object_type == 'include':
            if isinstance(data, dict):
                filename = data.get('include')
            else:
                filename = data
            parser = TranslationYamlParser()
            parser.load_and_parse(filename)
        elif rules is not None:
            for key in rules.get('translate', []):
                entry = data.get(key)
                cls.output_entry(entry, rules)
            for key in rules.get('translate-list', []):
                entries = data.get(key, [])
                if not isinstance(entries, list):
                    entries = [entries]
                for entry in entries:
                    cls.output_entry(entry, rules)
            for key in rules.get('recurse', []):
                children = data.get(key)
                if children is not None:
                    for child in children:
                        cls.decode(child)
        else:
            print("object", object_type)

    @classmethod
    def decode(cls, data):
        if isinstance(data, list):
            for entry in data:
                cls.decode_object(entry)
        elif isinstance(data, dict):
            cls.decode_object(data)

builtins.base = FakeBase()

context = DirContext()
main_dir = os.getcwd()
context.add_all_path_auto(main_dir)
context.add_all_path(main_dir)

settings.cache_yaml = False
parser = TranslationYamlParser()
TranslationYamlParser.output = open(sys.argv[1], 'w')
parser.output_header()
for entry in sys.argv[2:]:
    parser.load_and_parse(entry, context=context)
TranslationYamlParser.output.close()
