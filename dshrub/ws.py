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

def create_app(sensors, topic, path, refresh=1, host='0.0.0.0', port=8090):
    app = tawf.Application([
        (r'/(.*)', tornado.web.StaticFileHandler, {'path': path}),
    ])

    config = {
        'refresh': refresh,
        'data': sensors,
    }

    last_data = {s: deque([], 3600 * 24) for s in sensors}

    @app.route('/conf', mimetype='application/json')
    def conf():
        return config

    @app.route('/data/{sensor}', mimetype='application/json')
    def data(sensor):
        return list(last_data[sensor])

    @app.sse('/data', mimetype='application/json')
    def data(callback):
        items = []
        while True:
            data = yield from topic.get()
            items.extend(v for v in data)
            if round(items[-1].time - items[0].time) >= refresh:
                for item in items:
                    callback(item._asdict())
                del items[:]

    app.listen(port, address=host)

    return last_data


@asyncio.coroutine
def keep_data(topic, last_data):
    while True:
        items = yield from topic.get()
        for item in items:
            last_data[item.name].append(item._asdict())

# vim: sw=4:et:ai
