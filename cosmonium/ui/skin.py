from panda3d.core import LColor

class UISkinEntry():
    def __init__(self, extends):
        self.extends = extends
        if extends is None:
            self._background_color = LColor(0.3, 0.3, 0.3, 1)
            self._text_color = LColor(0.6, 0.6, 0.6, 1)
            self._border_color = LColor(1, 1, 1, 1)
        else:
            self._background_color = None
            self._text_color = None
            self._border_color = None

    @property
    def background_color(self):
        if self._background_color is not None:
            return self._background_color
        else:
            return self.extends.background_color

    @background_color.setter
    def background_color(self, color):
        self._background_color = color

    @property
    def text_color(self):
        if self._text_color is not None:
            return self._text_color
        else:
            return self.extends.text_color

    @text_color.setter
    def text_color(self, color):
        self._text_color = color

    @property
    def border_color(self):
        if self._border_color is not None:
            return self._border_color
        else:
            return self.extends.border_color

    @border_color.setter
    def border_color(self, color):
        self._border_color = color

    def get_dgui_parameters_for(self, dgui_type):
        if dgui_type == 'borders':
            parameters = {
                'background_color': self.background_color,
                'border_color': self.border_color,
                }
        elif dgui_type == 'frame':
            parameters = {
                'frameColor': self.background_color
                }
        elif dgui_type == 'label':
            parameters = {
                'frameColor': self.background_color,
                'text_fg': self.text_color,
                }
        elif dgui_type == 'button':
            parameters = {
                'text_fg': self.text_color,
                }
        else:
            parameters = {}
        return parameters

class UISkin:
    def __init__(self):
        self.entries = {}

    def add_entry(self, name, entry):
        self.entries[name] = entry

    def get(self, entry_name):
        try:
            return self.entries[entry_name]
        except KeyError:
            return self.entries['default']

    def get_dgui_parameters_for(self, identifier, dgui_type):
        entry = self.entries.get(identifier)
        if not entry:
            entry = self.entries.get('default')
        return entry.get_dgui_parameters_for(dgui_type)
