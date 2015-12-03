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

# how much data items to keep in memory per sensor, default 24h of data
N_DATA = 3600 * 24

def create_app(sensors, topic, path, refresh=1, host='0.0.0.0', port=8090):
    app = tawf.Application([
        (r'/(.*)', tornado.web.StaticFileHandler, {'path': path}),
    ])

    config = {
        'refresh': refresh,
        'data': sensors,
    }

    last_data = {s: deque([], N_DATA) for s in sensors}
    # read_data(preload_file, sensors, N_DATA, last_data)

    @app.route('/data', tawf.Method.OPTIONS, mimetype='application/json')
    def conf():
        return config

    @app.route('/data/{sensor}', mimetype='application/json')
    def data(sensor):
        data = last_data[sensor]
        return bin_data(data, 'mean', 480)

    @app.sse('/data', mimetype='application/json')
    async def data(callback):
        while True:
            items = await topic.get()
            for item in items:
                callback(item._asdict())

    app.listen(port, address=host)

    return last_data


# vim: sw=4:et:ai
