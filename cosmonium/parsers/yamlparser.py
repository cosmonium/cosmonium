from __future__ import print_function
from __future__ import absolute_import

from ..dircontext import defaultDirContext, DirContext
from ..cache import create_path_for
from ..import settings

import os
import sys
import hashlib
import pickle

if sys.version_info[0] < 3:
    from ..support import yaml2 as yaml
    try:
        from ..support.yaml2 import CLoader as Loader
    except ImportError:
        from ..support.yaml2 import Loader
else:
    from ..support import yaml
    try:
        from ..support.yaml import CLoader as Loader
    except ImportError:
        from ..support.yaml import Loader

def yaml_include(loader, node):
    print("Loading", node.value)
    filepath = node.value
    if filepath is not None:
        with file(filepath) as inputfile:
            data = yaml.load(inputfile)
            return data
    else:
        print("File", node.value, "not found")
        return None

yaml.add_constructor("!include", yaml_include)

class YamlParser(object):
    def __init__(self):
        pass

    def decode(self, data):
        return None

    def encode(self, data):
        return None

    def parse(self, stream, stream_name=None):
        data = None
        try:
            data = yaml.load(stream, Loader=Loader)
        #TODO: Why these are not caught ?
        #except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
        except Exception as e:
            if stream_name is not None:
                print("Syntax error in '%s' :" % stream_name, e)
            else:
                print("Syntax error : ", e)
        return data

    def store(self, data):
        return yaml.dump(data, default_flow_style=False)

    def encode_and_store(self, filename):
        try:
            stream = open(filename, 'w')
            data = self.encode()
            data = self.store(data)
            stream.write(data)
        except IOError as e:
            print("Could not write", filename, ':', e)
            return None

    def load_and_parse(self, filename):
        data = None
        try:
            text = open(filename).read()
            data = self.parse(text, filename)
            data = self.decode(data)
        except IOError as e:
            print("Could not read", filename, ':', e)
        return data

    @classmethod
    def get_type_and_data(cls, data, default=None):
        if data is None:
            object_type = default
            object_data = {}
        elif isinstance(data, str):
            object_type = data
            object_data = {}
        else:
            if len(data) == 1:
                object_type = list(data)[0]
                object_data = data[object_type]
            else:
                object_type = data.get('type', default)
                object_data = data
        return (object_type, object_data)

class YamlModuleParser(YamlParser):
    context = defaultDirContext

    def create_new_context(self, old_context, filepath):
        new_context = DirContext(old_context)
        path = os.path.dirname(filepath)
        new_context.add_all_path(path)
        for category in new_context.category_paths.keys():
            new_context.add_path(category, os.path.join(path, category))
        return new_context

    def load_from_cache(self, filename, filepath):
        data = None
        config_path = create_path_for('config')
        md5 = hashlib.md5(filepath.encode()).hexdigest()
        cache_file = os.path.join(config_path, md5 + ".dat")
        if os.path.exists(cache_file):
            file_timestamp = os.path.getmtime(filepath)
            cache_timestamp = os.path.getmtime(cache_file)
            if cache_timestamp > file_timestamp:
                print("Loading %s (cached)" % filepath)
                base.splash.set_text("Loading %s (cached)" % filepath)
                try:
                    with open(cache_file, "rb") as f:
                        data = pickle.load(f)
                except (IOError, ValueError) as e:
                    print("Could not read cache for", filename, cache_file, ':', e)
        return data

    def store_to_cache(self, data, filename, filepath):
        config_path = create_path_for('config')
        md5 = hashlib.md5(filepath.encode()).hexdigest()
        cache_file = os.path.join(config_path, md5 + ".dat")
        try:
            with open(cache_file, "wb") as f:
                print("Caching into", cache_file)
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        except IOError as e:
            print("Could not write cache for", filename, cache_file, ':', e)

    def load_and_parse(self, filename, context=None):
        data = None
        if context is None:
            context = YamlModuleParser.context
        filepath = context.find_data(filename)
        if filepath is not None:
            saved_context = YamlModuleParser.context
            YamlModuleParser.context = self.create_new_context(context, filepath)
            if settings.cache_yaml:
                data = self.load_from_cache(filename, filepath)
            if data is None:
                print("Loading %s" % filepath)
                base.splash.set_text("Loading %s" % filepath)
                try:
                    text = open(filepath).read()
                    data = self.parse(text, filepath)
                except IOError as e:
                    print("Could not read", filename, filepath, ':', e)
                if settings.cache_yaml and data is not None:
                    self.store_to_cache(data, filename, filepath)
            if data is not None:
                data = self.decode(data)
            YamlModuleParser.context = saved_context
        else:
            print("Could not find", filename)
        return data

