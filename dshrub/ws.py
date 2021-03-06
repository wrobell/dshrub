#
# DShrub - sensor data application.
#
# Copyright (C) 2015 by Artur Wroblewski <wrobell@pld-linux.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import asyncio
from collections import deque

import tornado.web
import tawf

from .data import bin_data, read_data

def create_app(sensors, topic, cache, path, refresh=1, host='0.0.0.0',
        port=8090):

    app = tawf.Application([
        (r'/(.*)', tornado.web.StaticFileHandler, {'path': path}),
    ])

    config = {
        'refresh': refresh,
        'data': sensors,
    }

    @app.route('/data', tawf.Method.OPTIONS, mimetype='application/json')
    def conf():
        return config

    @app.route('/data/{sensor}', mimetype='application/json')
    def data(sensor):
        data = cache[sensor]
        return bin_data(data, 'mean', 480)

    @app.sse('/data', mimetype='application/json')
    async def data(callback):
        while True:
            items = await topic.get()
            for item in items:
                callback(item._asdict())

    app.listen(port, address=host)


# vim: sw=4:et:ai
