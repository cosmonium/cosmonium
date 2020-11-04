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
    def update(self):
        pass

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
            print("Using Tk clipboard")
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

    def update(self):
        if self.r is not None:
            self.r.update()

    def copy_to(self, text):
        if self.r is not None:
            self.r.clipboard_clear()
            self.r.clipboard_append(text)
        else:
            print(text)

    def copy_from(self):
        text = ''
        if self.r is not None:
            try:
                text = self.r.clipboard_get()
            except:
                pass
        return text

class WinClipboard(Clipboard):
    def __init__(self):
        try:
            import win32clipboard
            import win32con
            self.w = win32clipboard
            self.type = win32con.CF_UNICODETEXT
            print("Using win32 clipboard")
        except ImportError:
            print("Could not import pywin32, no Windows copy&paste available")
            self.w = None

    def copy_to(self, text):
        self.w.OpenClipboard()
        self.w.EmptyClipboard()
        self.w.SetClipboardData(self.type, text)
        self.w.CloseClipboard()

    def copy_from(self):
        self.w.OpenClipboard()
        result = ''
        try:
            result = self.w.GetClipboardData(self.type)
        finally:
            self.w.CloseClipboard()
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
            print("Using xclip clipboard")
            self.cmd_read = '/usr/bin/xclip -selection "clipboard" -o'
            self.cmd_write = '/usr/bin/xclip -selection "clipboard" -i'
        elif os.path.isfile('/usr/bin/xsel'):
            print("Using xsel clipboard")
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
    if sys.platform == 'darwin':
        clipboard = DarwinClipboard()
    elif sys.platform == 'win32':
        clipboard = TkClipboard()
        if clipboard.r is None:
            clipboard = WinClipboard()
            if clipboard.w is None:
                clipboard = Clipboard()
    elif sys.platform.startswith('linux'):
        clipboard = XClipboard()
    else:
        print("No support for clipboard detected for platform", sys.platform)
        clipboard = Clipboard()
    return clipboard
