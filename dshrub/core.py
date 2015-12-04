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
import functools
import logging

import h5py
import n23

from . import ws
from .data import Cache, cache_data, replay_file
from .redis import publish

logger = logging.getLogger(__name__)

def start(device, sensors, dashboard=None, data_dir=None, rotate=None,
        channel=None, replay=None):

    topic = n23.Topic()

    if dashboard:
        cache = Cache(sensors)
        # read_data(preload_file, sensors, N_DATA, cache)
        ws.create_app(sensors, topic, cache, dashboard)
    else:
        cache = None

    files = None
    if data_dir:
        files = n23.data_logger_file('dshrub', data_dir)

    w = n23.cycle(
        rotate, workflow, topic, device, sensors, files=files,
        channel=channel, replay=replay, cache=cache
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(w)


def workflow(topic, device, sensors, files=None, channel=None,
        replay=None, cache=None):

    scheduler = n23.Scheduler(1, timeout=0.25)
    fout = next(files) if files else None

    if replay:
        logger.info('replaying a data file {}'.format(replay))
        fin = h5py.File(replay)

        # for each sensor
        for name in sensors:
            data_log = n23.data_logger(fout, name, 60) if fout else None
            consume = n23.split(topic.put_nowait, data_log)
            scheduler.add(name, replay_file(fin, name), consume)
    else:
        import btzen

        logger.info('connecting to sensor {}'.format(device))
        dev = btzen.connect(device)
        read_temp = btzen.Temperature(dev)
        read_pressure = btzen.Pressure(dev)
        read_hum = btzen.Humidity(dev)
        read_light = btzen.Light(dev)

        logger.info('connected to sensor {}'.format(device))

        readers = {
            'temperature': read_temp,
            'pressure': read_pressure,
            'humidity': read_hum,
            'light': read_light,
        }
        items = ((k, v) for k, v in readers.items() if k in sensors)
        for name, reader in items:
            data_log = n23.data_logger(fout, name, 60) if fout else None
            consume = n23.split(topic.put_nowait, data_log)
            scheduler.add(name, reader.read, consume)


    tasks = [scheduler()]
    if channel:
        p = publish(topic, channel)
        tasks.append(p)
        logger.info('publish data to redis channel {}'.format(channel))

    if cache:
        t = cache_data(topic.get, cache)
        tasks.append(t)

    return asyncio.gather(*tasks)


# vim: sw=4:et:ai
