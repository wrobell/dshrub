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

"""
Sensor data processing functions.
"""

import asyncio
import functools
import h5py
import itertools
import math

from collections import deque
from n23 import Data
from scipy.stats import binned_statistic

# how much data items to keep in memory per sensor, default 24h of data
N_DATA = 3600 * 24

def bin_data(data, agg, bins):
    """
    Bin sensor data and use `agg` function to aggregate values within one
    bin.

    Sensor data values is a list of (time, value) pairs.

    :param data: List of sensor data values.
    :param agg: Name of aggregation function, i.e. `mean'.
    :param bins: Numbers of bins.
    """
    times, values = zip(*data)
    values, times, *_ = binned_statistic(times, values, agg, bins=bins)
    data = [[t, v] for t, v in zip(times, values) if not math.isnan(v)]
    return data


async def cache_data(callable, cache):
    """
    Receive sensor data item from coroutine and store it in data cache.

    :param callable: Coroutine to receive sensor data.
    :param cache: Sensor data cache.
    """
    while True:
        item = await callable()
        cache.add(item)


def replay_file(f, sensor):
    """
    Return sensor data reader function getting data from HDF file.

    :param f: HDF file object.
    :param sensor: Sensor name.
    """
    data = itertools.cycle(f[sensor + '/data'])
    return lambda: float(next(data)[0])


def read_data(fn, sensors, n, data):
    f = h5py.File(fn)
    for name in sensors:
        ts = f[name + '/event_time'][-n:]
        ds = f[name + '/data'][-n:]
        data[name].extend(
            [float(t[0]), float(v[0])] for t, v in zip(ts, ds)
            if not math.isnan(t[0])
        )
    f.close()


def dispatch(func):
    """
    Like `functools.singledispatch` but for class methods.

    http://stackoverflow.com/a/24602374/722424
    """
    dispatcher = functools.singledispatch(func)
    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)
    wrapper.register = dispatcher.register
    functools.update_wrapper(wrapper, func)
    return wrapper


class Cache:
    """
    Senor data cache.

    Sensor data is kept in dictionary consisting of `(name, queue)` pairs,
    where `name` is name of a sensor and queue holds sensor data values.
    Sensor data value consists of a pair `(time, value)`.
    """
    def __init__(self, sensors, maxsize=N_DATA):
        """
        Create sensor data cach.

        :param sensors: List of sensors.
        :param maxsize: Maximum number of values kept per sensor.
        """
        self._cache = {s: deque([], maxsize) for s in sensors}


    @dispatch
    def add(self, item):
        """
        Add sensor data value.

        Sensor data item can be

        - `n23.core.Data` sensor data value
        - dictionary compatible with `n23.core.Data` class
        - list of above objects

        :param item: Sensor data item.
        """
        raise NotImplementedError('Not implemented for {}'.format(type(item)))


    def __getitem__(self, name):
        return self._cache[name]


    @add.register(Data)
    def _add(self, item):
        self._add_value(item.name, item.time, item.value)


    @add.register(dict)
    def _add(self, item):
        self._add_value(item['name'], item['time'], item['value'])


    @add.register(deque)
    @add.register(list)
    def _add(self, item):
        for v in item:
            self.add(v)


    def _add_value(self, name, time, value):
        self._cache[name].append((time, value))


# vim: sw=4:et:ai
