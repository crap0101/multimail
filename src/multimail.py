#!/usr/bin/env python
# -*- coding: utf-8 -*-

# multimail - massive mail sender

# Copyright (C) 2009,2010,2011  Marco Chieppa (aka crap0101)

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


# IMPORTS #
from __future__ import print_function

import os
import os.path as osp
import sys
import time
import smtplib
import getpass
import locale
import itertools as it
try:                                               # __
    from email.mime.text import MIMEText           #   |--  email formatting
except ImportError:                                #   |
    from email.MIMEText import MIMEText            #   | some email's module
try:                                               #   | subpackages has been
    from email.mime.base import MIMEBase           #   | renamed nor moved, so
except ImportError:                                #   | we can try to import
    from email.MIMEBase import MIMEBase            #   | the right module
try:                                               #   | for running Python's
    from email.mime.multipart import MIMEMultipart #   | version above 2.1
except ImportError:                                #   |
    from email.MIMEMultipart import MIMEMultipart  #   |______
try:                                                      #   |
    from email.mime.nonmultipart import MIMENonMultipart  #   |
except ImportError:                                       #   |
    from email.MIMENonMultipart import MIMENonMultipart   #   |
try:                                                      #   |
    from email import Encoders                            #   |
except ImportError:                                       #   |
    from email import encoders as Encoders                # __|

import platform
PY_VERSION = int(platform.python_version_tuple()[0])
if PY_VERSION < 3:
    input = raw_input

# LOCAL IMPORTS #
from Multimail import parsopts
from Multimail import mmutils
from Multimail import editor

VERSION = parsopts.VERSION


class MailMessage(object):
    """ Bare Mail object."""
    def __init__(self, sender, receiver, subject, text, attachments):
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.text = text
        self.attachments = attachments
        self.xmailer = VERSION
        self.delimiter = "=========multimail_delimiter========="
        self.msg = None

    def sign(self, file, *args):
        with open(file) as f:
            self.text = f.read()


class PlainMsg(MailMessage):
    """Plain text mail object."""
    def __init__(self, sender, receiver, subject, text):
        super(PlainMsg, self).__init__(
            sender, receiver, subject, text, None);

    def get_message(self, receiver=None):
        receiver = receiver if receiver is not None else self.receiver
        _time = mmutils.mail_format_time()
        return ("From: %s\r\nTo: %s\r\nSubject: %s\r\n"
                "Date: %s\r\nX-Mailer: %s\r\n\r\n%s"
                % (self.sender, receiver, self.subject,
                   _time, self.xmailer, self.text))


class MimeMsg(MailMessage):
    """Plain text mail object."""
    def __init__(self, sender, receiver, subject, text, ttype, attachments):
        super(MimeMsg, self).__init__(
            sender, receiver, subject, text, attachments)
        self.text_type = ttype
        self.build()

    def build(self):
        if not self.attachments:
            if self.text_type == 'html':
                self.msg = MIMENonMultipart('text', 'html')
            else:
                self.msg = MIMENonMultipart('text', 'plain', charset='utf-8')
            self.msg.set_payload(self.text)
            self.msg['boundary'] = self.delimiter
        else:
            self.msg = MIMEMultipart(boundary=self.delimiter)
            if self.text_type == 'html':
                self.msg.attach(MIMEText(self.text, 'html'))
            else:
                self.msg.attach(MIMEText(self.text, _charset='utf-8'))
        self.msg['From'] = self.sender
        self.msg['To'] = self.receiver
        self.msg['Subject'] = self.subject
        self.msg['Date'] = "NULL"
        self.msg['X-Mailer'] = self.xmailer
        if self.attachments:
            for attachment, _name in self.attachments:
                to_attach = MIMEBase('application', "octet-stream")
                with open(attachment, "rb") as att:
                    to_attach.set_payload(att.read())
                Encoders.encode_base64(to_attach)
                _name = osp.basename(attachment) if not _name else _name
                to_attach.add_header(
                    'Content-Disposition',
                    'attachment; filename="%s"' % _name)
                self.msg.attach(to_attach)

    def get_message(self, receiver=None, as_string=True):
        receiver = receiver if receiver is not None else self.receiver
        _time = mmutils.mail_format_time()
        self.msg.replace_header('To', receiver)
        self.msg.replace_header('Date', _time)
        if as_string:
            return self.msg.as_string()
        return self.msg

    def sign(self, file, detached):
        if detached:
            self.attachments.append((file, 'signature.sig'))
        else:
            super(MimeMsg, self).sign(file)
        self.build()


class SendMails(object):
    def __init__(self, host, port, secure_conn=True, timeout=50):
        self.host = host
        self.port = port
        self.secure_conn = secure_conn
        self.debug_level = 0
        self.timeout = timeout
        self.delay_time = 0
        self.connection = None
        self.step = 0
        self.errors = 0
        self.total = 0

    def _connect(self):
        # TODO: timeout not available in python < 2.6
        if self.secure_conn:
            self.connection = smtplib.SMTP_SSL(
                self.host, self.port, timeout=self.timeout)
        else:
            self.connection = smtplib.SMTP(
                self.host, self.port, timeout=self.timeout)
        return self.connection

    def connect(self):
        try:
            self._connect()
        except smtplib.SMTPConnectError as e:
            print("ERROR during connection: %s" % str(e))
            return False
        return True

    def delay(self):
        time.sleep(self.delay_time)

    def login(self, login_name, pwd=None):
        if pwd is None:
            pwd = getpass.getpass()
        if self.connection is None:
            if not self.connect():
                return False
        self.connection.set_debuglevel(self.debug_level)
        try:
            self.connection.login(login_name, pwd)
        except smtplib.SMTPAuthenticationError as e:
            print("Authentication Error: invalid userID or password")
            return False
        except smtplib.SMTPHeloError as e:
            print("SMTPHelo Error: no response from %s" % self.host)
            return False
        except smtplib.SMTPException as e:
            print("No suitable authentication method was found.")
            return False
        return True

    def send(self, msg, receivers):
        _retval = 0
        sender = msg.sender
        self.total = len(receivers)
        for rec in receivers:
            self.print_progress()
            try:
                self.connection.sendmail(sender, rec, msg.get_message(rec))
                self.step += 1
                self.delay()
            except (smtplib.SMTPDataError,
                    smtplib.SMTPRecipientsRefused,
                    smtplib.SMTPHeloError,
                    smtplib.SMTPSenderRefused,) as e:
                self.errors += 1
                _retval = 255
                print("%s [when sending to %s]" %s (str(e), rec))
            except smtplib.SMTPServerDisconnected as e:
                print('Error: disconnected from the server: %s' % e)
                self.errors += self.total - self.step
                _retval = 3
                break
        self.quit()
        self.print_progress()
        print()
        return _retval

    def print_progress(self, out=sys.stdout):
        """Print the status of the job."""
        out.write("\r%d%% job completed... (%d errors)"
            % (self.step*100/self.total, self.errors))
        out.flush()

    def quit(self):
        self.connection.quit()

def main(args):
    def clean():
        to_clean = filter(None, (_attachment, _signed_file))
        for path in to_clean:
            try:
                os.remove(path)
            except OSError as e:
                print ("clean: {0}".format(str(e)))
    parser = parsopts.get_parser()
    opts = parser.parse_args(args)
    _attachment = None
    _signed_file = None
    _section = opts.u_set
    if opts.editor and opts.text:
        parser.error("conflict between options -e|--editor and"
                   " -m|--text-msg")
    if not opts.use_config_file:
        if opts.custom_config_file:
            parser.error("conflict between options -C|--config-file and"
                       " -n|--no-config")
        config = mmutils.fake_config(_section)
    else:
        cfg_path = (os.path.expanduser('~/.multimail.cfg')
                    if not opts.custom_config_file
                    else opts.custom_config_file)
        try:
            config = mmutils.read_config(cfg_path)
        except (IOError, ConfigParser.ParsingError) as e:
            parser.error("Error reading %s: no file or not valid one: %s"
            % (cfg_path, str(e)))
    for file in opts.from_file:
        with open(file) as f:
            opts.recipients.extend(list(addr.strip() for addr in f))
    if not opts.recipients:
        parser.error("No recipient found")
    if not opts.sender_addr:
        _sender = config.get(_section, 'sender')
        if not _sender:
            parser.error("sender address not found")
        else:
            opts.sender_addr = _sender
    if not opts.login_name:
        _login = config.get(_section, 'login')
        opts.login_name = _login or opts.sender_addr
    if not opts.text_type:
        if not opts.use_config_file:
            opts.text_type = 'text'
        else:
            opts.text_type = config.get(_section, 'text_type') or 'text'
            if opts.text_type not in ('html', 'text', 'plain'):
                parser.error("invalid values for text_type in the config file,"
                           " must be one of ['html', 'text', 'plain'],"
                           " got '%s' instead" % opts.text_type)
    if opts.compression and not opts.attachments:
        parser.error("Nothing to compress.")
    if (opts.detach and opts.sign):
        parser.error("sign must be clear or detached, not both.")
    if opts.text_type == 'plain' and opts.detach:
        parser.error("can't make detached signature in plain text mode")
    if opts.text_type == 'plain':
        if any((opts.compression, opts.attachments, opts.archive_name,)):
            parser.error("can't send attachments in plain text mode")
    else:
        if opts.archive_name and not opts.attachments:
            parser.error('No attachments for naming.')
        elif opts.archive_name and not opts.compression:
            parser.error("Can't naming without compression.")
        elif opts.compression and not opts.attachments:
            parser.error('No attachments for compression.')
        if opts.attachments:
            _dirs = [_p for _p in opts.attachments if osp.isdir(_p)]
            if _dirs and not opts.compression:
                parser.error('directories need compression.')
            if opts.compression:
                try:
                    _attachment = mmutils.create_archive(
                        opts.attachments, opts.compression)
                except (mmutils.ArchiveError, IOError) as e:
                    clean()
                    raise mmutils.ArchiveError(
                        "Can't create archive: %s" % str(e))
                # add extension to attachment's name
                _ext = ('.tar' if opts.compression in ('gz', 'bz2')
                        else '') + '.' + opts.compression
                if opts.archive_name:
                    _a_name = opts.archive_name + _ext
                else:
                    _a_name = osp.basename(_attachment)
                opts.attachments = [(_attachment, _a_name)]
            else:
                opts.attachments = list(mmutils.izip_longest(
                    it.chain(opts.attachments), ()))
    if not opts.subject:
        opts.subject = input("email's subject [hit RETURN when done]: ")
    if not opts.text:
        _editor = opts.editor or config.get(_section, 'editor')
        if _editor:
            try:
                opts.text = editor.use_ext_editor(_editor)
            except editor.EditorError as e:
                print(e)
                clean()
                sys.exit(1)
        elif editor.YOU_HAVE_CURSES and PY_VERSION < 3:
            # temporary disable curses editor for python >= 3
            # 'cause it must be fixed for work with that version
            opts.text = editor.use_curses_editor()
        else:
            opts.text = editor.no_curses()
    elif osp.isfile(osp.abspath(opts.text)):
        with open(opts.text) as t:
            opts.text = t.read()
    if opts.text_type == 'plain':
        msg_obj = PlainMsg(opts.sender_addr, '', opts.subject, opts.text)
    else:
        msg_obj = MimeMsg(opts.sender_addr, '', opts.subject,
                          opts.text, opts.text_type, opts.attachments)
    # ---
    _host = config.get(_section, 'host')
    if not opts.host:
        if _host:
            opts.host = _host
        else:
            clean()
            parser.error("No host specified")
    _secure_conn = False
    if config.get(_section, 'secure_conn'):
        _secure_conn = config.getboolean(_section, 'secure_conn')
    opts.secure_conn = opts.secure_conn or _secure_conn
    if not opts.port:
        _port = (config.get(_section, 'ssl_port') if opts.secure_conn
                    else config.get(_section, 'port'))
        try:
            opts.port = int(_port)
        except ValueError:
            clean()
            parser.error("No port specified or not a valid one: '%s'" % _port)
    if opts.timeout is None:
        _timeout = config.get(_section, 'timeout')
        if _timeout:
            try:
                _timeout = int(_timeout)
            except ValueError:
                clean()
                parser.error("Not a valid timeout value: '%s'" % _timeout)
        opts.timeout = _timeout or 40
    if opts.timeout < 0:
        parser.error("invalid timeout value: %s" % opts.timeout)
    send_obj = SendMails(opts.host, opts.port, opts.secure_conn, opts.timeout)
    _debug = 0
    if config.get(_section, 'debug_mode'):
        _debug = config.getboolean(_section, 'debug_mode')
    opts.debug = opts.debug or _debug
    if opts.delay is None:
        if not opts.use_config_file:
            opts.delay = 0
        else:
            _delay = config.get(_section, 'delay')
            try:
                opts.delay = float(_delay)
            except ValueError:
                clean()
                parser.error("Not a valid delay value: '%s'" % _delay)
    if opts.delay < 0:
        clean()
        parser.error("delay must be >= 0, got %f instead" % opts.delay)
    opts.password = (opts.password or (config.get(_section, 'password') or None))
    send_obj.debug_level = opts.debug
    send_obj.delay_time = opts.delay
    if not send_obj.login(opts.login_name, opts.password):
        clean()
        sys.exit(2)
    #signing:
    if (opts.detach or opts.sign):
        gpg_exe = opts.gpg_exe or config.get(_section, 'gpg_exe')
        if not gpg_exe or not osp.isfile(gpg_exe):
            send_obj.quit()
            clean()
            parser.error("Can't find gnuPG, surely not here: %s" % gpg_exe)
        gpg_key = opts.gpg_key or config.get(_section, 'gpg_key_id')
        if not gpg_key:
            send_obj.quit()
            clean()
            parser.error("can't find the gpg key for signing.")
        _detach = True if opts.detach else False
        try:
            _text = msg_obj.text
            _signed_file = mmutils.gpg_sign(gpg_exe, gpg_key, _text, _detach)
        except mmutils.SignError as e:
            send_obj.quit()
            clean()
            raise mmutils.SignError(str(e))
        msg_obj.sign(_signed_file, _detach)
    # send:
    _ex_val = send_obj.send(msg_obj, opts.recipients)
    clean()
    sys.exit(_ex_val)


if __name__ == '__main__':
    main(sys.argv[1:])
