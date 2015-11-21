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
import itertools
import logging

import h5py
import n23

from . import ws

logger = logging.getLogger(__name__)


def start(device, sensors, dashboard=None, data_dir=None, rotate=None,
        channel=None, replay=None):

    topic = n23.Topic()
    if dashboard:
        last_data = ws.create_app(sensors, topic, dashboard)
    else:
        last_data = None

    files = None
    if data_dir:
        files = n23.data_logger_file('dshrub', data_dir)

    w = n23.cycle(
        rotate, workflow, topic, device, sensors, files=files,
        channel=channel, replay=replay, last_data=last_data
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(w)


def workflow(topic, device, sensors, files=None, channel=None,
        replay=None, last_data=None):

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
        import braitebt

        logger.info('connecting to sensor {}'.format(device))
        dev = braitebt.connect(device)
        r_temp = braitebt.read_temperature(dev)
        r_pressure = braitebt.read_pressure(dev)
        r_hum = braitebt.read_humidity(dev)
        r_light = braitebt.read_light(dev)
        read_temp = functools.partial(next, r_temp)
        read_pressure = functools.partial(next, r_pressure)
        read_hum = functools.partial(next, r_hum)
        read_light = functools.partial(next, r_light)

        # FIXME: first read is long, n23 needs to deal with it nicely
        next(r_temp)
        next(r_hum)
        logger.info('connected to sensor {}'.format(device))

        readers = {
            'temperature': read_temp,
            'pressure': read_pressure,
            'humidity': read_hum,
            'light': read_light,
        }
        items = ((k, v) for k, v in readers.items() if k in sensors)
        for name, s_read in items:
            data_log = n23.data_logger(fout, name, 60) if fout else None
            consume = n23.split(topic.put_nowait, data_log)
            scheduler.add(name, s_read, consume)


    tasks = [scheduler()]
    if channel:
        p = publish(topic, channel)
        tasks.append(p)
        logger.info('publish data to redis channel {}'.format(channel))

    if last_data:
        t = ws.keep_data(topic, last_data)
        tasks.append(t)

    return asyncio.gather(*tasks)


def replay_file(f, group_name):
    data = itertools.cycle(f[group_name + '/data'])
    return lambda: float(next(data)[0])


@asyncio.coroutine
def publish(topic, name):
    import aioredis
    client = yield from aioredis.create_redis(('localhost', 6379))
    if __debug__:
        logger.debug('connected to redis server')
    while True:
        values = yield from topic.get()
        for v in values:
            client.publish_json(name, v._asdict())


# vim: sw=4:et:ai
