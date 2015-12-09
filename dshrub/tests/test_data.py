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
Unit tests fo sensor data processing functions.
"""

import asyncio
from n23 import Data, Topic
from dshrub.data import bin_data, cache_data, Cache

from .util import patch_async, run_coroutine


def test_bin_data():
    """
    Test binning of sensor data.
    """
    data = [
        (1.1, 2),
        (1.2, 3),
        (1.3, 4),
        (1.4, 6),
        (1.5, 8),
        (1.6, 9),
    ]
    result = bin_data(data, 'mean', 3)
    assert [2.5, 5.0, 8.5] == [v[1] for v in result]
    #assert [1.2, 1.4, 1.6] == [v[0] for v in result]


def test_data_cache_store_limit():
    """
    Test data cache storing no more than max size items.
    """
    cache = Cache(['n'], 2) # store just two items
    cache.add(Data('n', 1, 10, 101))
    cache.add(Data('n', 1, 11, 102))
    cache.add(Data('n', 1, 12, 103))
    cache.add(Data('n', 1, 13, 104))
    assert [(12, 103), (13, 104)] == list(cache['n'])


def test_data_cache_store_item():
    """
    Test data cache storing `n23.Data` item.
    """
    cache = Cache(['n'])
    cache.add(Data('n', 1, 10, 101))
    assert [(10, 101)] == list(cache['n'])


def test_data_cache_store_dict():
    """
    Test data cache storing dictionary item.
    """
    cache = Cache(['n'])
    cache.add({'name': 'n', 'time': 10, 'value': 101})
    assert [(10, 101)] == list(cache['n'])


def test_data_cache_store_list():
    """
    Test data cache storing list of items.
    """
    cache = Cache(['n'])
    cache.add({'name': 'n', 'time': 10, 'value': 101})
    cache.add(Data('n', 1, 11, 102))
    assert [(10, 101), (11, 102)] == list(cache['n'])


def test_cache_data():
    """
    Test sensor data caching coroutine.
    """
    topic = Topic()
    cache = Cache(['test-sensor'])
    values = [
        Data('test-sensor', 0, 10, 101),
        Data('test-sensor', 0, 11, 102),
    ]

    with patch_async(topic, 'get') as f:
        f.side_effect = [values]
        coro = cache_data(f, cache)
        run_coroutine(coro)

    assert [(10, 101), (11, 102)] == list(cache['test-sensor'])


# vim: sw=4:et:ai
