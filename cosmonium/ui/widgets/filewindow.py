# -*- coding: utf-8 -*-
#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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

from direct.gui.DirectGui import DirectFrame, DGG
from directfolderbrowser.DirectFolderBrowser import DirectFolderBrowser
from panda3d.core import LVector2

from ... import settings
from .window import Window
from .direct_widget_container import DirectWidgetContainer


class FileWindow():
    icons = {
        'reload': "textures/icons/Reload.png",
        'up': "textures/icons/FolderUp.png",
        'new': "textures/icons/FolderNew.png",
        'showHidden': "textures/icons/FolderShowHidden.png",
        'folder': "textures/icons/Folder.png",
        'file': "textures/icons/File.png"
        }
    def __init__(self, title, font_family, font_size = 14, owner=None):
        self.title = title
        self.window = None
        self.layout = None
        self.browser = None
        self.last_pos = None
        self.font_size = font_size
        self.scale = LVector2(settings.ui_scale, settings.ui_scale)
        self.owner = owner
        self.callback = None

    def done(self, status):
        if status == 1:
            self.callback(self.browser.get())
        self.hide()

    def create_layout(self, path, show_files, extensions):
        if path is None:
            path = "~"
        width = 800
        height = 600
        self.layout = DirectWidgetContainer(DirectFrame(parent=pixel2d, state=DGG.NORMAL))
        self.browser = DirectFolderBrowser(command=self.done,
                                           size=(width, height),
                                           parent=self.layout.frame,
                                           defaultPath=path,
                                           fileBrowser=show_files,
                                           fileExtensions=extensions,
                                           icons=self.icons)
        self.layout.frame['frameSize'] = [0, width, -height, 0]
        self.window = Window(self.title, scale=self.scale, child=self.layout, owner=self)

    def show(self, current_path, callback, show_files=True, extensions=[]):
        self.callback = callback
        self.create_layout(current_path, show_files, extensions)
        if self.last_pos is None:
            if self.owner is not None:
                width = self.layout.frame['frameSize'][1] - self.layout.frame['frameSize'][0]
                height = self.layout.frame['frameSize'][3] - self.layout.frame['frameSize'][2]
                self.last_pos = ((self.owner.width - width) / 2, 0, -(self.owner.height - height) / 2)
            else:
                self.last_pos = (100, 0, -100)
        self.window.setPos(self.last_pos)
        self.window.update()

    def hide(self):
        if self.window is not None:
            self.last_pos = self.window.getPos()
            self.window.destroy()
            self.window = None
            self.layout = None
            self.browser = None
            self.callback = None

    def shown(self):
        return self.window is not None

    def window_closed(self, window):
        if window is self.window:
            self.last_pos = self.window.getPos()
            self.window = None
            self.layout = None
            if self.owner is not None:
                self.owner.window_closed(self)
