from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import TextNode
from direct.gui.DirectLabel import DirectLabel

from ..fonts import fontsManager, Font

from .info import ObjectInfo
from .layout import Layout
from .window import Window

class InfoPanel():
    def __init__(self, scale, font_family, font_size = 14, owner=None):
        self.window = None
        self.layout = None
        self.last_pos = None
        self.scale = scale
        self.font_size = font_size
        self.owner = owner
        self.font_normal = fontsManager.get_font(font_family, Font.STYLE_NORMAL)
        if self.font_normal is not None:
            self.font_normal = self.font_normal.load()
        self.font_bold = fontsManager.get_font(font_family, Font.STYLE_BOLD)
        if self.font_bold is not None:
            self.font_bold = self.font_bold.load()
        if self.font_bold is None:
            self.font_bold = self.font_normal

    def create_layout(self, body, rows):
        self.layout = Layout(2, rows,
                             parent=None,
                             frameColor=(0.33, 0.33, 0.33, .66))
        title = "Body information"
        self.window = Window(title, scale=self.scale, child=self.layout, owner=self, transparent=True)

    def get_info_for(self, body):
        titles = []
        infos = []
        if body is None:
            return (titles, infos)
        info = ObjectInfo.get_info_for(body)
        for entry in info:
            if entry is None: continue
            if len(entry) != 2:
                print("Invalid entry", entry)
                continue
            (title, value) = entry
            if title is None:
                pass
            elif value is None:
                titles.append(title)
                infos.append('')
            else:
                if isinstance(value, str):
                    titles.append(title)
                    infos.append(value)
                else:
                    titles.append(title)
                    infos.append('')
                    for entry in value:
                        if len(entry) != 2:
                            print("Invalid entry for", title, entry)
                            continue
                        (title, value) = entry
                        titles.append(title)
                        infos.append(value)
        return (titles, infos)

    def show(self, body):
        if self.shown():
            print("Info panel already shown")
            return
        (titles, infos) = self.get_info_for(body)
        self.create_layout(body, len(infos))
        for (i, (title, info)) in enumerate(zip(titles, infos)):
            if title is not None:
                if info is not None and info != '':
                    title_widget = DirectLabel(text=title,
                                               text_align=TextNode.ALeft,
                                               text_scale=tuple(self.scale * self.font_size),
                                               text_font=self.font_normal,
                                               frameColor=(0, 0, 0, 0))
                else:
                    title_widget = DirectLabel(text=title,
                                               text_align=TextNode.ALeft,
                                               text_scale=tuple(self.scale * self.font_size * 1.2),
                                               text_font=self.font_bold,
                                               frameColor=(0, 0, 0, 0))
                self.layout.set_child(0, i, title_widget)
            if info is not None:
                info_widget = DirectLabel(text=info,
                                           text_align=TextNode.ALeft,
                                           text_scale=tuple(self.scale * self.font_size),
                                           text_font=self.font_normal,
                                           frameColor=(0, 0, 0, 0))
                self.layout.set_child(1, i, info_widget)
        self.layout.recalc_positions()
        if self.last_pos is None:
            self.last_pos = (-self.layout.frame['frameSize'][1] / 2, 0, -self.layout.frame['frameSize'][3] / 2)
        self.window.setPos(self.last_pos)
        self.window.update()

    def hide(self):
        if self.window is not None:
            self.last_pos = self.window.getPos()
            self.window.destroy()
            self.window = None
            self.layout = None

    def shown(self):
        return self.window is not None

    def window_closed(self, window):
        if window is self.window:
            self.last_pos = self.window.getPos()
            self.window = None
            self.layout = None
            if self.owner is not None:
                self.owner.window_closed(self)
