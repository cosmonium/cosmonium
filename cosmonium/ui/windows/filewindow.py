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

from direct.gui.DirectGui import DirectFrame, DGG
from directfolderbrowser.DirectFolderBrowser import DirectFolderBrowser

from ..widgets.direct_widget_container import DirectWidgetContainer
from ..widgets.window_frame import WindowFrame
from .uiwindow import UIWindow


class FileWindow(UIWindow):
    icons = {
        'reload': "textures/icons/Reload.png",
        'up': "textures/icons/FolderUp.png",
        'new': "textures/icons/FolderNew.png",
        'showHidden': "textures/icons/FolderShowHidden.png",
        'folder': "textures/icons/Folder.png",
        'file': "textures/icons/File.png",
    }

    def __init__(self, title, path, callback, show_files=True, extensions=[], owner=None):
        UIWindow.__init__(self, owner)
        self.title = title
        if path is None:
            path = "~"
        self.path = path
        self.callback = callback
        self.show_files = show_files
        self.extensions = extensions
        self.browser = None

    def done(self, status):
        if status == 1:
            self.callback(self.browser.get())
        self.hide()

    def create_layout(self):
        width = 800
        height = 600
        self.layout = DirectWidgetContainer(DirectFrame(parent=self.owner.root, state=DGG.NORMAL))
        self.browser = DirectFolderBrowser(
            command=self.done,
            size=(width, height),
            parent=self.layout.frame,
            defaultPath=self.path,
            fileBrowser=self.show_files,
            fileExtensions=self.extensions,
            icons=self.icons,
        )
        self.layout.frame['frameSize'] = [0, width, -height, 0]
        self.window = WindowFrame(self.title, scale=self.scale, child=self.layout, owner=self)

    def hide(self):
        UIWindow.hide(self)
        self.browser = None
        self.callback = None
