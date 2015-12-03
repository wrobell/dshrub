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
import h5py
import itertools
import math

from collections import deque
from scipy.stats import binned_statistic


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


async def data_keeper(topic, data):
    """
    Receive sensor data item from topic and store it in data storage
    structure.

    Data storage structure is a dictionary with `(name, queue)` pairs,
    where name is name of a sensor and queue holds sensor data values.
    Sensor data value consists of a pair `(time, value)`.

    :param topic: Topic providing sensor data items. 
    :param data: Data storage structure.
    """
    while True:
        items = await topic.get()
        for item in items:
            data[item.name].append([item.time, item.value])


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

# vim: sw=4:et:ai
