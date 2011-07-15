# -*- coding: utf-8 -*-

# multimail - inviatore di email (editor.py module)

# Copyright (C) 2009  Marco Chieppa (aka crap0101)

# editor.py is part of multimail.
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not see <http://www.gnu.org/licenses/>

"""
This module implements a primitive text editor using curses.
"""


from __future__ import print_function

import sys
import tempfile
import subprocess
try:
    import curses
    import curses.ascii as ascii
    YOU_HAVE_CURSES = True
except ImportError:
    YOU_HAVE_CURSES = False
import platform
PYVERSION = int(platform.python_version_tuple()[0])

class EditorError(Exception):
    pass

def no_curses(stream=sys.stdin, verbose=True):
    """If the curses module isn't available,
    read from *stream* (default: stdin).
    """
    if verbose:
        print("module curses not found or not usable yet.\n"
              "Reading from stdin(C-d or C-z to stop typing)")
    return stream.read()


def use_ext_editor(editor):
    """Run *editor* writing in a temporary file.
    Return the written text.
    """
    with tempfile.NamedTemporaryFile() as f:
        f_name = f.name
        try:
            subprocess.check_call([editor, f_name])
        except (subprocess.CalledProcessError,
                OSError) as e:
            raise EditorError("error editing text: %s" % str(e))
    with open(f_name) as f:
        text = f.read()
    return text


def _write_chr_test(func):
    """Debug only."""
    testFile = open("ct", "w")
    def inner(inst):
        res = func(inst)
        if res in(7, 360, 361):
            testFile.close()
        else:
            testFile.write("|%d|" % res)
        return res
    return inner


class Editor(object):
    """
    Primitive text editor using the curses library
    KEYS:
        C-h  > shifted delete, delete the previous character
        C-d  > delete the char at the current position
        C-k  > cut from the currrent position to the EOL, saving in the buffer
        C-u  > paste the buffer at the current position
        C-o  > insert a blank line
        HOME > go to uppert-left position
        FINE > go to the bottom-right position
        PAG↑ > move up by self.changePage lines
        PAG↓ > move down by self.changePage lines
        ARROW(↑ ↓ → ←) > move up/down/right/left by one.
        C-g  > exit
    """
    def __init__(self, encoding='UTF-8'):
        self.CODE = encoding
        self.buffer = []
        curses.setupterm()
        self.win = curses.initscr()
        self.win.idlok(1)
        self.win.scrollok(True)
        curses.nl()
        curses.echo()
        curses.newwin(0, 0)
        self._start_point = (0, 0)
        y, x = self.win.getmaxyx()
        self.maxY, self.maxX = y - 1, x - 1
        del y, x
        self.yMaxPoint, self.xMaxPoint = 0, 0
        self.changePage = 10
        self._new_line = [''] *(self.maxX + 1)
        self.table = [self._new_line[:] for i in range(self.maxY + 1)]
        self._actualY, self._actualX = (0, 0)

    def edit(self):
        """ start editing. Exit with C-g. """
        while True:
            try:
                if not self._get_chr():
                    break
            except KeyboardInterrupt:
                pass
        self.quit_curses()

    #@_write_chr_test
    def _scan(self):
        """Get the next input """
        return self.win.getch()

    def _insert_line(self, line):
        """Insert a line at the given position """
        self.table.insert(self._actualY, line)
        self.table.pop()

    def _fill(self, line):
        """Fill ``line'' with the missing positions """
        toFill = len([_f for _f in self.table[line] if _f])
        self.table[line].extend([''] *(self.maxX - toFill))
        del self.table[line][self.maxX:]

    def _insert_chr(self, string):
        """Insert the given char or string at the current position, moving
        right the line by the length's input """
        self.table[self._actualY].insert(self._actualX, string)
        self.table[self._actualY].pop()

    def _cancel_back(self, y, x):
        """Delete the char at the current position, moving left the
        current line or up to 1 the next line """
        self._delete_chr()
        if y < self.maxY:
            chrs = [_f for _f in self.table[y][x:] if _f]
            nextl = [_f for _f in self.table[y + 1] if _f]
            if not chrs and len(nextl) < self.maxX - x + 1:
                del self.table[y][x:]
                self.table[y].extend(self.table[y + 1])
                self._fill(y)
                del self.table[y + 1]
                self.table.append(self._new_line[:])

    def _delete_chr(self):
        """Delete the char at the current position, moving
        right the line by the input length """
        self.table[self._actualY].pop(self._actualX)
        self.table[self._actualY].append('')

    def _delete_line(self):
        """Delete the line at the actual position """
        del self.table[self._actualY]
        self.table.append(self._new_line[:])

    def _cut_until_eol(self):
        """Cut the line from the actual position until the EOL
        and save that in the buffer """
        self.buffer = self.table[self._actualY][self._actualX:self.maxX + 1]
        del self.table[self._actualY][self._actualX:]
        self.table[self._actualY].extend([''] * len(self.buffer))
        self._fill(self._actualY)

    def _paste(self):
        """Paste the buffer's content at the current position, moving
        right the line by the buffer length """
        for char in [_f for _f in self.buffer if _f]:
            self.table[self._actualY].insert(self._actualX, char)
            self._actualX += 1
        self._fill(self._actualY)
        if self._actualX > self.maxX:
            self._actualX = self.maxX

    def _goto_max(self, line):
        """ go to the position of the last chr of line 'line' """
        self._actualY = line
        newX = len([_f for _f in self.table[self._actualY] if _f])
        if self._actualX > newX:
            self._actualX = newX

    def _get_chr(self):
        """ get the user input and perform the right job... I suppose. """
        y, x = self._actualY, self._actualX
        self.win.move(y, x)
        curses.noecho()
        self.win.refresh()
        c = self._scan()
        if (c >= 32) and(c < 127):
            self._insert_chr(chr(c))
            if x < self.maxX:
                self._actualX += 1
            elif y < self.maxY:
                self._actualY += 1
                self._actualX = 0
        elif(c >= 194) and(c < 224):
            self._insert_chr(''.join(
                    chr(c) + chr(self._scan())).decode(self.CODE))
            if x < self.maxX:
                self._actualX += 1
            elif y < self.maxY:
                self._actualY += 1
                self._actualX = 0
        elif c in(curses.KEY_ENTER, 10, ascii.CR):  # carriage return
            if y < self.maxY:
                if any([_f for _f in self.table[y][x:] if _f]):
                    self._cut_until_eol()
                    self._actualY += 1
                    self._actualX = 0
                    self._insert_line(self._new_line[:])
                    self._paste()
                    self._actualX = 0
                else:
                    self._actualY += 1
                    self._actualX = 0
                    self._insert_line([''] *(self.maxX + 1))
        elif c in(8, ascii.DEL, curses.KEY_SDC): # C-h, shifted delete( <- )
            if x > 0:
                self._actualX -= 1
                self._delete_chr()
            elif x == 0 and(0 < y <= self.maxY):  # -%%%?<+
                _buffer = self.table[self._actualY][:]
                self._actualX = self.maxX # trick for _goto_max
                self._goto_max(self._actualY - 1)
                _delta = self.maxX - self._actualX + 1
                chrs = [_f for _f in _buffer if _f]
                del self.table[self._actualY + 1]
                if len(chrs) < _delta:
                    self.table.append(self._new_line[:])
                    del self.table[self._actualY][self._actualX:]
                    self.table[self._actualY].extend(chrs)
                    self._fill(self._actualY)
                else:
                    del self.table[self._actualY][self._actualX:]
                    self.table[self._actualY].extend(chrs[:_delta])
                    self.table.insert(self._actualY + 1, chrs[_delta:])
                    self._fill(self._actualY + 1)
            else:
                self._delete_line()
        elif c in(4, curses.KEY_CANCEL): # C-d - delete
            self._cancel_back(y, x)
        elif c == 27:
            _c = self._scan()
            _cc = self._scan()
            if _c == 79:
                if _cc == 72 or c == curses.KEY_HOME:   # start
                    self._actualY, self._actualX = self._start_point
                elif _cc == 70 or c == curses.KEY_END:    # end
                    self._goto_max(self.maxY)
            elif _c == 91:
                if _cc == 51 or c == curses.KEY_CANCEL:
                    self._scan()
                    self._cancel_back(y, x)
                elif _cc == 53 or c == curses.KEY_PPAGE:
                    if(y - self.changePage) > 0:
                        self._scan()
                        self._goto_max(self._actualY - self.changePage)
                    else:
                        self._scan()
                        self._goto_max(0)
                elif _cc == 54 or c == curses.KEY_NPAGE:
                    if self.maxY >(y + self.changePage):
                        self._scan()
                        self._goto_max(self._actualY + self.changePage)
                    else:
                        self._scan()
                        self._goto_max(self.maxY)
                elif _cc == 65 or c == curses.KEY_UP:
                    if y > 0:
                        self._goto_max(self._actualY - 1)
                elif _cc == 66 or c == curses.KEY_DOWN:
                    if y < self.maxY:
                        self._goto_max(self._actualY + 1)
                elif _cc == 67 or c == curses.KEY_RIGHT:
                    if x < self.maxX:
                        if x < len([_f for _f in self.table[y] if _f]):
                            self._actualX += 1
                        elif y < self.maxY:
                            self._actualY += 1
                            self._actualX = 0
                    elif y < self.maxY:
                        self._actualY += 1
                        self._actualX = 0
                elif _cc == 68 or c == curses.KEY_LEFT:
                    if x > 0:
                        self._actualX -= 1
                    elif x <= 0 and y > 0:
                        self._actualX = self.maxX # trick for _goto_max
                        self._goto_max(self._actualY - 1)
                else:
                    curses.beep()
            else:
                curses.beep()
        elif c in(ascii.VT, curses.KEY_EOL): # C-k |delete from cursor to EOL
            self._cut_until_eol()
            if self._actualX == 0:
                del self.table[self._actualY]
                self.table.append(self._new_line[:])
        elif c == ascii.NAK: # C-u(past text from self.buffer)
            self._paste()
        elif c in(15, ascii.SI): # C-o(insert blank line)
            if y < self.maxY:
                self._actualY += 1
                self._insert_line([''] *(self.maxX + 1))
        elif c in(ascii.BEL, curses.KEY_END, curses.KEY_EXIT): # C-g(exit)
            return False
        else:
            curses.beep()
        self._update_win()
        return True

    def _update_win(self):
        """ update the window with the content of the table """
        self.win.move(*self._start_point)
        self.win.clrtobot()
        y = self._start_point[0]
        for n, line in enumerate(self.table):
            lineNum = y + n
            self.win.move(lineNum, 0)
            for pos, x in enumerate(line):
                self.win.insstr(lineNum, pos, x.encode(self.CODE))

    def save_text(self):
        """ return a string, the content of the table """
        return '\n'.join(''.join(line).encode(self.CODE)
                          for line in self.table).rstrip()

    def quit_curses(self):
        """Do the proper things before exiting such as de-initialize the
        curses library and return the terminal to normal status.
        """
        curses.endwin()
        curses.nocbreak()
        self.win.keypad(0)
        curses.echo()
        curses.endwin()


def use_curses_editor():
    import locale
    locale.setlocale(locale.LC_ALL, '')
    CODE = locale.getpreferredencoding()
    try:
        ed = Editor(CODE)
        ed.edit()
        text = ed.save_text()
    except Exception as e:
        ed.quit_curses()
        try:
            import traceback
            traceback.print_tb(e.__traceback__)
        except:
            pass
        print(str(e))
        return
    finally:
        locale.setlocale(locale.LC_ALL, 'C')
    return text

if __name__ == '__main__':
    if YOU_HAVE_CURSES and PYVERSION < 3:
        print(use_curses_editor())
    else:
        print(no_curses())
