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
import h5py
import logging
import operator
import signal
import sys
from contextlib import contextmanager

import n23

from . import ws
from .data import Cache, cache_data, replay_file
from .redis import publish

logger = logging.getLogger(__name__)

def start(device, sensors, dashboard=None, data_dir=None, rotate=None,
        channel=None, replay=None):

    dbus_loop = None
    topic = n23.Topic()

    if dashboard:
        cache = Cache(sensors)
        # read_data(preload_file, sensors, N_DATA, cache)
        ws.create_app(sensors, topic, cache, dashboard)
    else:
        cache = None

    if replay:
        logger.info('replaying a data file {}'.format(replay))
        replay = h5py.File(replay)
    else:
        import dbus
        import threading
        from dbus.mainloop.glib import DBusGMainLoop
        from gi.repository import GObject
        dbus_loop = DBusGMainLoop(set_as_default=True)
        dbus_main_loop = GObject.MainLoop()
        dbus_bus = dbus.SystemBus(mainloop=dbus_loop)
        thread = threading.Thread(target=dbus_main_loop.run, daemon=True)
        thread.start()

    files = None
    if data_dir:
        files = n23.dlog_filename('dshrub', data_dir)

    w = n23.cycle(
        rotate, workflow, topic, device, sensors, files=files,
        channel=channel, replay=replay, cache=cache, dbus_bus=dbus_bus
    )
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, sys.exit)
    try:
        loop.run_until_complete(w)
    finally:
        loop.remove_signal_handler(signal.SIGTERM)
        w.close()


@contextmanager
def workflow(topic, device, sensors, files=None, channel=None,
        replay=None, cache=None, dbus_bus=None):

    interval = 1
    scheduler = n23.Scheduler(interval)

    dlog = None
    if files:
        fout = h5py.File(next(files), 'w')
        dlog = n23.DLog(fout, interval, n_chunk=60, debug=True)
        scheduler.debug = dlog
        scheduler.add_observer(dlog.notify)

    items = sensor_replay(replay, sensors) if replay \
        else sensor_tag(dbus_bus, device, sensors)

    for name, read in items:
        if dlog:
            shape = ()
            if name == 'accelerometer':
                shape += (3,)
            dlog.add(name, shape=shape)

        @n23.coroutine
        def calc(callback):
            import math
            while True:
                item = yield
                value = math.sqrt(sum(v ** 2 for v in item.value))
                item = item._replace(value=value)
                callback(item)
        pt = calc(topic.put_nowait) if name == 'accelerometer' else topic.put_nowait
        consume = n23.split(pt, dlog)
        scheduler.add(name, read, consume)

    tasks = [scheduler]
    if channel:
        p = publish(topic, channel)
        tasks.append(p)
        logger.info('publish data to redis channel {}'.format(channel))

    if cache:
        t = cache_data(topic.get, cache)
        tasks.append(t)

    try:
        yield asyncio.gather(*tasks)
    finally:
        scheduler.close()
        dlog.close()
        fout.close()


def sensor_replay(fin, sensors):
    reader = functools.partial(replay_file, fin)
    items = ((s, reader(s)) for s in sensors)
    return items


def sensor_tag(bus, device, sensors):
    import btzen

    dev = btzen.connect(bus, device)
    logger.info('connected to sensor {}'.format(device))

    readers = {
        'temperature': btzen.Temperature,
        'pressure': btzen.Pressure,
        'humidity': btzen.Humidity,
        'light': btzen.Light,
        'accelerometer': btzen.Accelerometer,
    }
    items = [(n, cls(bus, dev)) for n, cls in readers.items() if n in sensors]
    for n, s in items:
        s.set_interval(1)
    return ((n, s.read_async) for n, s in items)

# vim: sw=4:et:ai
