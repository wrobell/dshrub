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
Unit test utilities.
"""

from contextlib import contextmanager

from unittest import mock

class AsyncMock(mock.MagicMock):
    def __setattr__(self, name, value):
        if name == 'side_effect' and isinstance(value, list):
            value = value + [StopAsyncIteration()]
        super().__setattr__(name, value)


    async def __call__(self, *args, **kw):
        return super().__call__(*args, **kw)


@contextmanager
def patch_async(obj, name):
    p = mock.patch.object(obj, name, new_callable=AsyncMock)
    f = p.start()
    yield f
    p.stop()


def run_coroutine(coro):
    try:
        coro.send(None)
    except StopAsyncIteration:
        pass


# vim: sw=4:et:ai
