#!/usr/bin/env python
# -*- coding: utf-8 -*-

# multimail - massive mail sender | run_tests file

from __future__ import print_function

import re
import os
import sys
import os.path as op_
import unittest


if __name__ == '__main__':
    pwd = op_.dirname(op_.realpath(__file__))
    os.chdir(pwd)
    basepackdir = op_.join(op_.split(pwd)[0], 'src')
    sys.path.insert(0, basepackdir)

    reg = re.compile(r'^test_.*\.py$')
    tests_suite = unittest.TestSuite()
    for testfile in filter(reg.match,  os.listdir(os.getcwd())):
        print("### importing module %s ###" % testfile)
        module = __import__(os.path.splitext(testfile)[0])
        tests_suite.addTests(module.load_tests())
    print("### RUNNING TESTS ###")
    unittest.TextTestRunner(verbosity=2).run(tests_suite)
