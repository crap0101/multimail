# -*- coding: utf-8 -*-

# multimail - massive email sender (parsopt.py module)

# Copyright (C) 2009,2010,2011  Marco Chieppa (aka crap0101)

# parsopts.py is part of multimail.
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


VERSION = 'multimail 2.2.1'

DESCRIPTION = """
                 multimail - massive email sender
NAME: multimail
VERSION: 2.2.1
AUTHORS: Marco Chieppa (aka crap0101)
DATE:    2011-06-17
LICENSE: GNU GPL v3 or later
REQUIRES:
  - Python < 3
  - argparse module (for python < 2.7)
OPTIONAL:
  - ssmtplib (for Python <2.6) http://aleph-null.tv/downloads/ssmtplib.py
    (but it's already shipped with the program)
  - ncurses module (for the internal text editor).
"""

EPILOG = """
EXAMPLES:


INTERNAL TEXT EDITOR KEYSTROKES:
------------------------------------------------
  [CRTL + G]  >> save and quit
  [RETURN]    >> CR :)
  [DELETE]    >> delete back
  [CRTL + B]  >> move left
  [CTRL + F]  >> move right
  [CRTL + P]  >> move up
  [CRTL + N]  >> move down
  [CRTL + O]  >> insert an empty line
  [CRTL + K]  >> delete from the cursor to the EOL
------------------------------------------------

VALUE NAMES RECOGNIZED (IN THE CONFIG FILE):
---------------------------------
sender =			;; email address
login =				;; login name
password =			;; login password
editor =			;; external text editor
text_type = text		;; one of plain|text|html
host = 	    			;; host to connect to
secure_conn = true  ;; use ssl encryption
port = 25           ;; used when secure_conn is false.
ssl_port = 465      ;; used when secure_conn is true (ssl encryption)
timeout = 50	    ;; timeout in seconds for blocking operations like the connection attempt
debug_mode = 	    ;; no value for disable 
delay = 0           ;; delay between mail sending
gpg_key_id =        ;; gpg key ID for sign mails 
gpg_exe =           ;; path to the gpg executable (default to gpg if not set)
---------------------------------
"""


import argparse

def get_parsed():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-a', '--attachments', dest='attachments', nargs='+',
                        metavar='FILE', action='append', default=[],
                        help='attach these files to the mail. Multiple use'
                        ' of this option together with the -c|--compress'
                        ' option cause the creation of multiple'
                        " archive and, in this case, they will be named with"
                        ' the corresponding parameter passed to the '
                        ' -A|--archive-name option.')
    parser.add_argument('-A', '--archive-name',
                        metavar='STR', dest='archive_name', nargs='+',
                        default=[], action='append',
                        help='Name of the archives to attach (the right'
                        " extension depending the archive's type will be"
                        ' automatically appended to the given name).'
                        ' This option will be used only if the -c|--compress'
                        ' option is present, raise an error otherwise). Without'
                        ' this option a randomly generated name is choosen.'
                        " In practice, this option's values must be in the same"
                        ' number of the -a|--attachments ones, for example'
                        ' a valid use is:'
                        '  [...] -a FILES_FOR_ARCH1 -a FILES_FOR_ARCH2'
                        ' -A NAME_OF_ARCH1 NAME_OF_ARCH2 [...] .')
    parser.add_argument('-c', '--compress', dest='compression', 
                        choices=('tar', 'gz', 'bz2', 'zip'),
                        help='make a (potentially) compressed archive'
                        ' of the attachments before attach them to the mail.'
                        ' "gz" and "bz2" creates a tar.(gz|bz2) archive.')
    parser.add_argument('-C', '--config-file', dest='custom_config_file',
                        help="Path to the config file from to read program's"
                        "configuration infos instead of the default one"
                        " (which is ~/.multimail.cfg ).")
    parser.add_argument('-D', '--debug', dest='debug', action='store_true',
                        help='show more info when sending mails.')
    parser.add_argument('-d', '--delay', type=float, dest='delay',
                        metavar='NUM', help='number of seconds to wait'
                        ' for sending between each mail (can be a'
                        ' floating point number and must be >= 0.')
    parser.add_argument('-e', '--editor', dest='editor', metavar='PROG',
                        help='external text editor for writing email.'
                        'This option conflict with the -m|--text-msg option.')
    parser.add_argument('-f', '--from', dest='sender_addr', metavar='ADDRESS',
                        help="sender's mail address, used as login name"
                        " if -l|--login option isn't provided from command line"
                        " nor available through the config file.")
    parser.add_argument('-H', '--host', dest='host', metavar='STR',
                        help='Host name to connect to.')
    parser.add_argument('-l', '--login', dest='login_name', metavar='STR',
                        help='string for login to the mail server. If not'
                        ' provided, read from the configuration file or '
                        ' (in case the -n|--no-config option is being used or'
                        ' no value is set for this option in the config file)'
                        ' use the -f|--from values provided at command line.')
    parser.add_argument('-m', '--text-msg', dest='text', metavar='TEXT|FILE',
                        help="text of the mail. Can be the path to a file,"
                        " in this case the file's content will be read and"
                        " stored as the text message. Without this option"
                        " the user will be asked to prompt the text message"
                        " using the internal editor (need the ncurses module)"
                        " or the external editor choosed in the config file;"
                        " fall back to take input from stdin if none of these"
                        " are available.")
    parser.add_argument('-n', '--no-config', dest='use_config_file',
                        action='store_false', help="Don't read missing info"
                        " from the config file, only command-line options will"
                        " be used. Without this option missing informations"
                        " needed by the program will be taked from the default"
                        " config file or from the one provided by the user"
                        " (see the -C|--config-file option).")
    parser.add_argument('-p', '--password', dest='password', metavar='PASSWORD',
                        help='password for login to the mail server. If not'
                        ' provided will be asked to prompt it from stdin.')
    parser.add_argument('-P','--port', dest='port', metavar='NUM', type=int,
                        help='Port number for the connection. If omitted,'
                        ' tries to read the value in the config file.')
    parser.add_argument('-r', '--recipients', dest='recipients', nargs='+',
                        metavar='EMAIL_ADDR', help='recipients of the mail.')
    parser.add_argument('--from-file', dest='from_file', nargs='+', default=[],
                        metavar='FILE', help='read recipients from FILE(s).'
                        ' FILE must have one recipient per line.')
    parser.add_argument('-S', '--SSL', dest='secure_conn', action='store_true',
                        help='Should be used for situations where SSL is'
                        ' required from the beginning of the connection. If'
                        ' omitted, read from config file. This option cause'
                        ' the program to use the smtplib.SMTP_SSL class,'
                        ' instead of the default smtplib.SMTP .')
    parser.add_argument('-s', '--subject', dest='subject', metavar='TEXT',
                        help="email's subject. Without this option the"
                        " user will be asked to prompt the subject"
                        " (one line, read using raw_input())")
    parser.add_argument('-t', '--timeout', dest='timeout', type=int,
                        metavar='NUM', help='specifies a timeout in seconds'
                        ' for blocking operations like the connection attempt')
    parser.add_argument('-T', '--text-type', dest='text_type',
                        choices=('html', 'text', 'plain'),
                        help="The mail's text type. Default behavior is to"
                        " build a MIME message type (for both 'text' or 'html')"
                        " choosing 'plain' cause the program to build a non-MIME,"
                        " plain message; also, use of 'plain' forbid the use"
                        " of the -a|-A options. If not specified from command"
                        " line or in config file, defalut to 'text'.")
    parser.add_argument('-u', '--user-settings', dest='u_set', metavar='STR',
                         default='DEFAULT', help='Section name in the config'
                        ' file from which read settings. This make possible'
                        ' to have various configuration templates.')
    parser.add_argument('-v', '--version', action='version',
                        version=VERSION)
    sig = parser.add_argument_group('signing mails', '(require GnuPG)')
    sig.add_argument('-k', '--gpg-key', metavar='KEY_ID', dest='gpg_key',
                     help='sign the mails using KEY_ID.')
    sig.add_argument('--sign', dest='sign', action='store_true',
                     help='make a clear signature.')
    sig.add_argument('--detach-sign', dest='detach', action='store_true',
                     help='make a detached signature.')
    sig.add_argument('--gpg-exe', dest='gpg_exe', metavar='PATH',
                     help='Path to the gnuPG executable.')
    return parser
