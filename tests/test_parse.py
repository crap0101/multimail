#!/usr/bin/env python
# -*- coding: utf-8 -*-

# multimail - massive mail sender | test_parse file


import sys
import os
import os.path as op_
import random
import shlex
import argparse
import subprocess as sbp
import platform
import unittest

pwd = op_.dirname(op_.realpath(__file__))
p_exe = 'python%s.%s' % tuple(platform.python_version_tuple()[:2])
m_exe = op_.join(op_.split(pwd)[0], 'src', 'multimail.py')
config_file = op_.join(op_.split(pwd)[0], 'src', 'multimail.cfg')

try:
    import Multimail
    config_file = os.path.expanduser('~/.multimail.cfg')
except ImportError:
    basepackdir = op_.join(op_.split(pwd)[0], 'src')
    sys.path.insert(0, basepackdir)
    
from Multimail import parsopts


class TestParser(unittest.TestCase):
    def testParser(self):
        parser = parsopts.get_parser()
        self.assertTrue(isinstance(parser, argparse.ArgumentParser))

    def testProcessFail(self):
        _base_cmdline = ('{exe} {prog} -f {from} -C {config}'
                         '-r {to} -s baz -m foobar ')
        opts = {'from':'foo@bar.org', 'config': config_file,
                'to': 'spam@spam.com', 'exe': p_exe, 'prog': m_exe}
        _cmd = _base_cmdline.format(**opts)
        fails = ('--fail',
                 '-a foo bar -A',
                 '-a foo bar -A foo -A',
                 '-c bz2 -a foo bar -A foo -A',
                 '-c spam -a foo bar -A foo -A',
                 '-d "I am not a number, I am a free man."',
                 '-n',
                 '-S xxx',
                 '-t spam'
                 '-T eggs',
                 '-u non-existent-user-section',
                 '--sign don-t-require-arg',
                 '--detach-sign this-too',)
        for args in fails:
            cmd = _cmd + args
            p = sbp.Popen(shlex.split(cmd), stdout=sbp.PIPE,
                          stderr=sbp.PIPE)
            self.assertNotEqual(0, p.returncode)

    def testOptionsValue(self):
        delay = random.randint(0, 1001)
        delayf = random.randint(100, 1001)/3.0
        diff = 0.5
        timeout = random.randint(0, 1001)
        args = {
            '-a foo bar baz': lambda o: o.attachments == ['foo bar baz'.split()],
            '-a foo -a baz': lambda o: o.attachments == [['foo'], ['baz']],
            '-A x y z': lambda o: o.archive_name == ['x y z'.split()],
            '-A x -A y z': lambda o: o.archive_name == [['x'], ['y', 'z']],
            '-c tar': lambda o: o.compression == 'tar' and o.delay is None,
            '-c gz': lambda o: o.compression == 'gz' and o.debug is False,
            '-c bz2': lambda o: o.compression == 'bz2' and o.secure_conn is False,
            '-c zip': lambda o: o.compression == 'zip',
            '-C config-file': lambda o: o.custom_config_file == 'config-file',
            '-D': lambda o: o.debug is True and o.use_config_file is True,
            '-d %d' % delay: lambda o: o.delay == delay,
            '-d %f' % delayf: lambda o: abs(o.delay - delayf) < diff,
            '-n': lambda o: o.use_config_file is False and o.u_set == 'DEFAULT',
            '-r Alice Bob': lambda o:o.recipients == 'Alice Bob'.split(),
            '-r x y -r Alice Bob': lambda o:o.recipients == 'Alice Bob'.split(),
            '-S': lambda o: o.secure_conn is True and o.sign is False,
            '-t %d' % timeout: lambda o: o.timeout == timeout,
            '--sign': lambda o: o.sign is True and o.detach is False,
            '-u section': lambda o: o.u_set == 'section',
            '--detach-sign': lambda o: o.detach is True and o.sign is False,}
        for cmd, res in args.items():
            parser = parsopts.get_parser()
            opts = parser.parse_args(shlex.split(cmd))
            self.assertTrue(res(opts), cmd)




def load_tests():
    loader = unittest.TestLoader()
    test_cases = (TestParser,)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)


if __name__ == '__main__':
    os.chdir(pwd)
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(load_tests()))
