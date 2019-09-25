#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

import sys
import os

class Clipboard():
    def copy_to(self, text):
        pass

    def copy_from(self):
        return ''

class TkClipboard(Clipboard):
    def __init__(self):
        has_tk = False
        self.r = None
        try:
            if sys.version_info[0] < 3:
                from Tkinter import Tk, TclError
            else:
                from tkinter import Tk, TclError
            has_tk = True
        except ImportError:
            print("tinker not found, no Tk copy&paste available")
        if has_tk:
            try:
                self.r = Tk()
                self.r.withdraw()
            except TclError:
                print("tkinter not properly installed, no Tk copy&paste available")
        else:
            self.r = None

    def copy_to(self, text):
        if self.r is not None:
            self.r.clipboard_clear()
            self.r.clipboard_append(text)
            self.r.update()
        else:
            print(text)

    def copy_from(self):
        text = ''
        if self.r is not None:
            self.r.update()
            text = self.r.selection_get(selection="CLIPBOARD")
        return text

class WinClipboard(Clipboard):
    def __init__(self):
        import win32clipboard
        import win32con

    def copy_to(self, text):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_TEXT, text)
        win32clipboard.CloseClipboard()

    def copy_from(self):
        win32clipboard.OpenClipboard()
        result = w.GetClipboardData(win32con.CF_TEXT)
        win32clipboard.CloseClipboard()
        return result

class DarwinClipboard(Clipboard):
    def copy_to(self, text):
        pbcopy = os.popen('pbcopy', 'w')
        pbcopy.write(text)
        pbcopy.close()

    def copy_from(self):
        pbpaste = os.popen('pbpaste', 'r')
        result = pbpaste.read()
        pbpaste.close()
        return result

class XClipboard(Clipboard):
    def __init__(self):
        self.cmd_read = None
        self.cmd_write = None
        if os.path.isfile('/usr/bin/xclip'):
            self.cmd_read = '/usr/bin/xclip -selection "clipboard" -o'
            self.cmd_write = '/usr/bin/xclip -selection "clipboard" -i'
        elif os.path.isfile('/usr/bin/xsel'):
            self.cmd_read = '/usr/bin/xsel -b -o'
            self.cmd_write = '/usr/bin/xsel -b'
        else:
            print("No X clipboard helper found, please install xsel or xclip")

    def copy_to(self, text):
        if self.cmd_write is None:
            return
        cmd = os.popen(self.cmd_write, 'w')
        cmd.write(text)
        cmd.close()

    def copy_from(self):
        if self.cmd_read is None:
            return ''
        cmd = os.popen(self.cmd_read, 'r')
        result = cmd.read()
        cmd.close()
        return result

def create_clipboard():
    clipboard = TkClipboard()
    if clipboard.r is None:
        if sys.platform == 'darwin':
            clipboard = DarwinClipboard()
        elif sys.platform == 'win32':
            clipboard = WinClipboard()
        elif sys.platform.startswith('linux'):
            clipboard = XClipboard() 
        else:
            print("No support for clipboard detected for platform", sys.platform)
            clipboard = Clipboard()
    return clipboard