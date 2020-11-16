from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from ..plugins import moduleLoader

class AddonYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, parent=None):
        if isinstance(data, str):
            data = {'file': data}
        name = data.get('name', None)
        filename = data.get('file')
        module_path = self.context.find_module(filename)
        if module_path is not None:
            module = moduleLoader.load_module(module_path)
            plugin = module.CosmoniumPlugin()
            plugin.init(self.app)
        else:
            print("ERROR: Could not find '{}'".format(filename))
        return None

ObjectYamlParser.register_object_parser('plugin', AddonYamlParser())
