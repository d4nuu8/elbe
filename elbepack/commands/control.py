# ELBE - Debian Based Embedded Rootfilesystem Builder
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2014-2017 Linutronix GmbH

import argparse
import socket
import sys
from http.client import BadStatusLine
from urllib.error import URLError

from suds import WebFault

from elbepack.cli import add_arguments_from_decorated_function
from elbepack.config import cfg
from elbepack.elbexml import ValidationMode
from elbepack.soapclient import ElbeSoapClient, client_actions


def run_command(argv):

    aparser = argparse.ArgumentParser(prog='elbe control')

    aparser.add_argument('--host', dest='host', default=cfg['soaphost'],
                         help='Ip or hostname of elbe-daemon.')

    aparser.add_argument('--port', dest='port', default=cfg['soapport'],
                         help='Port of soap itf on elbe-daemon.')

    aparser.add_argument('--pass', dest='passwd', default=cfg['elbepass'],
                         help='Password (default is foo).')

    aparser.add_argument('--user', dest='user', default=cfg['elbeuser'],
                         help='Username (default is root).')

    aparser.add_argument(
        '--retries',
        dest='retries',
        type=int,
        default=10,
        help='How many times to retry the connection to the server before '
             'giving up (default is 10 times, yielding 10 seconds).')

    devel = aparser.add_argument_group(
        'options for elbe developers',
        "Caution: Don't use these options in a productive environment")
    devel.add_argument('--skip-urlcheck', action='store_true',
                       dest='url_validation', default=ValidationMode.CHECK_ALL,
                       help='Skip URL Check inside initvm')

    devel.add_argument('--debug', action='store_true',
                       dest='debug', default=False,
                       help='Enable debug mode.')

    subparsers = aparser.add_subparsers(required=True)

    for action_name, do_action in client_actions.items():
        action_parser = subparsers.add_parser(action_name)
        action_parser.set_defaults(func=do_action)
        add_arguments_from_decorated_function(action_parser, do_action)

    args = aparser.parse_args(argv)
    args.parser = aparser

    try:
        control = ElbeSoapClient(
            args.host,
            args.port,
            args.user,
            args.passwd,
            debug=args.debug,
            retries=args.retries)
    except URLError:
        print(
            f'Failed to connect to Soap server {args.host}:{args.port}\n',
            file=sys.stderr)
        print('', file=sys.stderr)
        print('Check, whether the initvm is actually running.', file=sys.stderr)
        print("try 'elbe initvm start'", file=sys.stderr)
        sys.exit(13)
    except socket.error:
        print(
            f'Failed to connect to Soap server {args.host}:{args.port}\n',
            file=sys.stderr)
        print('', file=sys.stderr)
        print(
            'Check, whether the Soap Server is running inside the initvm',
            file=sys.stderr)
        print("try 'elbe initvm attach'", file=sys.stderr)
        sys.exit(14)
    except BadStatusLine:
        print(
            f'Failed to connect to Soap server {args.host}:{args.port}\n',
            file=sys.stderr)
        print('', file=sys.stderr)
        print('Check, whether the initvm is actually running.', file=sys.stderr)
        print("try 'elbe initvm start'", file=sys.stderr)
        sys.exit(15)

    try:
        args.func(control, args)
    except WebFault as e:
        print('Server returned error:', file=sys.stderr)
        print('', file=sys.stderr)
        if hasattr(e.fault, 'faultstring'):
            print(e.fault.faultstring, file=sys.stderr)
        else:
            print(e, file=sys.stderr)
        sys.exit(6)
