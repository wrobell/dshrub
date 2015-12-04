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
Coroutines to simplify communication with Redis server.
"""

import aioredis
import logging

logger = logging.getLogger(__name__)


class Channel(object):
    """
    Subscribe to Redis channel `name`.

    It is coroutine and context manager.

    The context manager returns Redis channel.
    """
    def __init__(self, name):
        """
        Create context manager for Redis channel.

        :param name: Redis channel.
        """
        super().__init__()
        self.name = name


    async def __aenter__(self):
        self.client = await aioredis.create_redis(('localhost', 6379))
        self.channel, = await self.client.subscribe(self.name)
        return self.channel


    async def __aexit__(self, *args):
        self.client.close()


    def __await__(self):
        return self.__aenter__().__await__()


class Client(object):
    """
    Connect to Redis server.

    It is coroutine and context manager.

    The context manager returns Redis connection.
    """
    async def __aenter__(self):
        self.client = await aioredis.create_redis(('localhost', 6379))
        return self.client


    async def __aexit__(self, *args):
        self.client.close()


    def __await__(self):
        return self.__aenter__().__await__()



async def publish(topic, name):
    """
    Publish sensor data received from a topic to Redis channel.

    :param topic: Sensor data topic.
    :param name: Redis channel name.
    """
    async with Client() as client:
        while True:
            values = await topic.get()
            for v in values:
                client.publish_json(name, v._asdict())


# vim: sw=4:et:ai
