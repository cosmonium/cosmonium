from panda3d.core import LColor

class UISkinEntry():
    def __init__(self, extends):
        if extends is not None:
            self.background_color = extends.background_color
            self.text_color = extends.text_color
            self.border_color = extends.border_color
        else:
            self.background_color = LColor(0.3, 0.3, 0.3, 1)
            self.text_color = LColor(0.6, 0.6, 0.6, 1)
            self.border_color = LColor(1, 1, 1, 1)

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

    def get_dgui_parameters_for(self, identifier, dgui_type):
        entry = self.entries.get(identifier)
        if not entry:
            entry = self.entries.get('default')
        return entry.get_dgui_parameters_for(dgui_type)
