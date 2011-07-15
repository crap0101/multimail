#!/usr/bin/env python
# -*- coding: utf-8 -*-

# multimail - massive mail sender | test_parse file


import sys
import os
import os.path as op_
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import subprocess as sbp
import unittest

pwd = op_.dirname(op_.realpath(__file__))
p_exe = sys.executable
m_exe = op_.join(op_.split(pwd)[0], 'src', 'multimail.py')

try:
    import Multimail
except ImportError:
    basepackdir = op_.join(op_.split(pwd)[0], 'src')
    sys.path.insert(0, basepackdir)
    
from Multimail import editor


class TestMisc(unittest.TestCase):
    def testNoCurses(self):
        texts = ('foo, bar and baz',
                 '''spam,
                 eggs,''',
                 '',
                 'foo\nbar\nbaz',)
        for text in texts:
            written = editor.no_curses(StringIO(text), False)
            self.assertEqual(text, written)

    def testExtEditor(self):
        fake_editors = ('nanetto', 'imecs', 'eddie', 'Vi-Hai', 'geddito')
        for fake in fake_editors:
            self.assertRaises(editor.EditorError,
                              editor.use_ext_editor, fake)


def load_tests():
    loader = unittest.TestLoader()
    test_cases = (TestMisc,)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)


if __name__ == '__main__':
    os.chdir(pwd)
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(load_tests()))
