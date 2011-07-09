#!/usr/bin/env python
# -*- coding: utf-8 -*-

# multimail - massive mail sender | test_utils file


import os
import os.path as op_
import subprocess as sbp
import sys
import time
import glob
try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import platform
import zipfile
import tarfile
import tempfile
import unittest


pwd = op_.dirname(op_.realpath(__file__))
data_dir = op_.join(pwd, 'data')

fake_exe = 'python%s.%s' % tuple(platform.python_version_tuple()[:2])
config_file_opts = ["host", "port", "ssl_port", "secure_conn",
                    "timeout", "debug_mode", "delay", "editor",
                    "sender", "login", "password", "text_type",]
config_file_no_opts = ['foo', 'bar', 'baz', 'spam']


try:
    import Multimail
except ImportError:
    basepackdir = op_.join(op_.split(pwd)[0], 'src')
    sys.path.insert(0, basepackdir)

from Multimail import mmutils


class TestArchives(unittest.TestCase):
    def testCreation(self):
        func_args = list(([os.getcwd()], atype)
                    for atype in ('tar', 'zip', 'gz', 'bz2'))
        err_args = list((['/foo/bar/baz'], t) for _, t in func_args)
        err_args.append(([os.getcwd()], 'asstar'))
        for p, t in err_args:
            self.assertRaises(mmutils.ArchiveError,
                              mmutils.create_archive, p, t)
        for args in func_args[:2]:
            ret_path = mmutils.create_archive(*args)
            self.assertNotEqual(ret_path, None)
            self.assertTrue(op_.exists(ret_path))
            self.assertTrue(ret_path.endswith(args[1]))
            os.remove(ret_path)

    def testFailCreation(self):
        if platform.python_version_tuple()[0] == '3':
            self.skipTest('why? see http://bugs.python.org/issue11513')
        # Fail in python3.2 , see http://bugs.python.org/issue11513
        func_args = list(([os.getcwd()], atype)
                    for atype in ('tar', 'zip', 'gz', 'bz2'))
        func_args.append(([os.sep], 'tar'))
        func_args.append(([os.sep], 'zip'))
        for p, t in func_args:
            self.assertRaises(IOError,
                              mmutils.create_archive, p, t, '/foo/bar/spam')

    def testClosing(self):
        atypes = ('zip', 'tar', 'gz', 'bz2')
        for i in range(10):
            for t in atypes:
                with tempfile.NamedTemporaryFile() as f:
                    c = '.tar' if t in ('gz', 'bz2') else ''
                    arc = f.name + c + '.' + t
                if t == 'zip':
                    with mmutils.ArchiveClosing(zipfile.ZipFile(arc, 'w')) as a:
                        self.assertTrue(op_.exists(arc))
                        self.assertTrue(arc.endswith(t))
                elif t in ('tar', 'gz', 'bz2'):
                    m = {'tar':'w:', 'gz':'w:gz', 'bz2':'w:bz2'}
                    with mmutils.ArchiveClosing(tarfile.open(arc, m[t])) as a:
                        self.assertTrue(op_.exists(arc))
                        self.assertTrue(arc.endswith(t))
                self.assertTrue(op_.exists(arc))
                os.remove(arc)
                self.assertFalse(op_.exists(arc))


class TestFormatTime(unittest.TestCase):
    def testFormat(self):
        fmts, ltime, gtime = (mmutils.mail_format_time(),
                              time.localtime(),
                              time.gmtime())
        dh = abs(int(fmts.split()[-1])/100)
        self.assertEqual(dh, abs(ltime.tm_hour - gtime.tm_hour))
        fmts = ' '.join(fmts.split()[:-1])
        st = time.strptime(fmts, "%a, %d %b %Y %H:%M:%S")
        for lv, fv in zip(ltime[:-1], st[:-1]):
            self.assertEqual(lv, fv)

    def testTimeDiff(self):
        stb = [2000, 11, 30, 0, 55, 0, 3, 335, -1]
        t1 = time.struct_time(stb)
        for h in range(23):            
            stb[3] = h
            t2 = time.struct_time(stb)
            fmts = mmutils.mail_format_time(t1, t2)
            dh = int(fmts.split()[-1])/100
            if t1 > t2:
                self.assertEqual(dh, t1.tm_hour - t2.tm_hour)
            elif t1 < t2:
                self.assertEqual(dh, t2.tm_hour - t1.tm_hour)
            fmts = mmutils.mail_format_time(t2, t1)
            dh = int(fmts.split()[-1])/100
            if t1 > t2:
                self.assertEqual(dh, t2.tm_hour - t1.tm_hour)
            elif t1 < t2:
                self.assertEqual(dh, t1.tm_hour - t2.tm_hour)


class TestConfig(unittest.TestCase):
    def testRead(self):
        for file in glob.glob(op_.join(data_dir, '*.cfg')):
            config = mmutils.read_config(file)
            self.assertTrue(isinstance(config, configparser.ConfigParser))
            for opt in config_file_opts:
                config.get('DEFAULT', opt)
            for opt in config_file_no_opts:
                self.assertRaises(
                    configparser.NoOptionError,
                    config.get, 'DEFAULT', opt)
                
    def testFakeConfig(self):
        for section in ('spam', 'eggs', 'foobar'):
            config = mmutils.fake_config(section)
            for opt in config_file_opts:
                config.get(section, opt)
                self.assertRaises(
                    configparser.NoOptionError,
                    config.get, 'DEFAULT', opt)
        config = mmutils.fake_config('DEFAULT')
        for opt in config_file_opts:
            config.get('DEFAULT', opt)
            

class TestGNUPG(unittest.TestCase):
    def testBuildCommand(self):
        def_args = {'exe':'gpg', 'key':1212121,
                    'infile': 'foo', 'outfile':'bar', 'detached':True}
        ch_args = ({'infile': 'foo/bar'},
                   {'outfile':'/foo/bar'},
                   {'infile': '/foo/bar', 'outfile':'foo/bar'},)
        err_args = ({'infile': "'foo/"},
                    {'infile': "'foo/"},
                    {'infile': "'fo''o/"})
        for args in ch_args:
            d = dict(def_args)
            for k, v in args.items():
                d[k] = v
            cmd = mmutils.build_gpg_cmd(d['exe'], d['key'], d['infile'],
                                        d['outfile'], d['detached'])
        for args in err_args:
            d = dict(def_args)
            for k, v in args.items():
                d[k] = v
            self.assertRaises(ValueError,
                              mmutils.build_gpg_cmd,
                              d['exe'], d['key'], d['infile'],
                              d['outfile'], d['detached'])

    def testSign(self):
        commands_ok = ([fake_exe, '-c', "1+1"],
                       [fake_exe, '-V'],
                       [fake_exe, '-c', 'print ("spam")'],)
        commands_err = ([fake_exe, '-c', "2+2=5"],
                        [fake_exe, '-c', "raise IndexError('spam')"],
                        [fake_exe, '-c', "--foo"],)
        for cmd in commands_ok:
            ret, err = mmutils.do_sign(cmd, sbp.PIPE, sbp.PIPE)
            self.assertEqual(ret, 0)
            self.assertEqual(err, None)
        for cmd in commands_err:
            ret, err = mmutils.do_sign(cmd, sbp.PIPE, sbp.PIPE)
            self.assertNotEqual(ret, 0, "{0}".format(cmd))
            self.assertTrue(isinstance(err, str))



def load_tests():
    loader = unittest.TestLoader()
    test_cases = (TestArchives, TestFormatTime, TestConfig,
                  TestGNUPG,)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)


if __name__ == '__main__':
    os.chdir(pwd)
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(load_tests()))
