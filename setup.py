#!/usr/bin/env python3
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

import sys
import os.path

from setuptools import setup, find_packages

setup(
    name='dshrub',
    version='0.1.0',
    description='dshrub - sendor data application',
    author='Artur Wroblewski',
    author_email='wrobell@pld-linux.org',
    url='https://github.com/wrobell/dshrub',
    setup_requires = ['setuptools_git >= 1.0',],
    packages=find_packages('.'),
    scripts=('bin/dshrub', 'bin/dshrub-dashboard'),
    include_package_data=True,
    long_description=\
"""\
DShrub is sensor data applicztion.
""",
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Development Status :: 2 - Pre-Alpha',
    ],
    license='GPL',
    install_requires=[],
)

# vim: sw=4:et:ai
