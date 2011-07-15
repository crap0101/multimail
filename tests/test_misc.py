#!/usr/bin/env python
# -*- coding: utf-8 -*-

# multimail - massive mail sender | test_misc file


import sys
import os
import os.path as op_
from io import BytesIO
import email.message
import email.parser
try:
    from email.mime.multipart import MIMEMultipart
except ImportError:
    from email.MIMEMultipart import MIMEMultipart
try:
    from email.mime.nonmultipart import MIMENonMultipart
except ImportError:
    from email.MIMENonMultipart import MIMENonMultipart
import unittest

pwd = op_.dirname(op_.realpath(__file__))
p_exe = sys.executable

basepackdir = op_.join(op_.split(pwd)[0], 'src')
sys.path.insert(0, basepackdir)

import multimail


class TestMessage(unittest.TestCase):
   def testPlain(self):
       values = [('foo@bar.baz', 'recv', '???', '!!!'),
                 ('spam@spam.eggs', 'mavco.pisellonio@legion.pa', 'c', 'C'),
                 ('unknown@nowhere.foo', 'x@y.z, bar@bar.bar', 'X', 'Y'),]
       #sender, receiver, subject, text
       for vals in values:
           msg = multimail.PlainMsg(*vals)
           headers = email.parser.Parser().parsestr(msg.get_message())
           for p, h in enumerate(('from', 'to', 'subject')):
               self.assertEqual(headers[h], vals[p])

   def testMime(self):
       values = [('foo@bar.baz', 'recv', '???', '!!!', 'html', []),
                 ('spam@spam.eggs', 'mavco.pisellonio@legion.pa',
                  'c', 'C', 'text', []),
                 ('unknown@nowhere.foo', 'x@y.z, bar@bar.bar', 'X', 'Y',
                  'text', [(op_.join(basepackdir, 'multimail.py'), 'spam')]),]
       #sender, receiver, subject, text, ttype, attachments
       for vals in values:
           msg = multimail.MimeMsg(*vals)
           headers = email.parser.Parser().parsestr(msg.get_message())
           if vals[-1]:
               self.assertTrue(isinstance(msg.msg, MIMEMultipart))
           else:
               self.assertTrue(isinstance(msg.msg, MIMENonMultipart),
                               "%s | %s" % (msg.text_type, msg.attachments))
           for p, h in enumerate(('from', 'to', 'subject')):
               self.assertEqual(headers[h], vals[p])
           pl = headers.get_payload()
           if not isinstance(pl, list):
               pl = pl.encode() if isinstance(pl, str) else pl
               self.assertEqual(pl, vals[3].encode())
           else:
               _t = pl[0].get_payload(decode=True)
               _t = _t.encode() if isinstance(_t, str) else _t
               _a = BytesIO(pl[1].get_payload(decode=True))
               with open(vals[5][0][0], 'rb') as f:
                   _oa = f.read()
               self.assertEqual(_t, vals[3].encode())
               self.assertEqual(_a.read(), _oa)
                                           
                   
            
def load_tests():
    loader = unittest.TestLoader()
    test_cases = (TestMessage,)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)


if __name__ == '__main__':
    os.chdir(pwd)
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(load_tests()))
