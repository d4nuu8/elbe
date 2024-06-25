# ELBE - Debian Based Embedded Rootfilesystem Builder
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2014-2017 Linutronix GmbH

import logging

from beaker.middleware import SessionMiddleware

from spyne import Application
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from elbepack.projectmanager import ProjectManager

from .esoap import ESoap

logging.getLogger('spyne').setLevel(logging.INFO)


class EsoapApp(Application):
    def __init__(self, *args, **kargs):
        Application.__init__(self, *args, **kargs)
        self.pm = ProjectManager('/var/cache/elbe')


class MySession(SessionMiddleware):
    def __init__(self, app, pm):
        self.pm = pm
        super().__init__(app)

    def stop(self):
        self.pm.stop()


def get_app():

    app = EsoapApp([ESoap], 'soap',
                   in_protocol=Soap11(validator='lxml'),
                   out_protocol=Soap11())

    wsgi = WsgiApplication(app)
    return MySession(wsgi, app.pm)
