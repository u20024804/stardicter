# -*- coding: utf-8 -*-
#
# Copyright © 2006 - 2017 Michal Čihař <michal@cihar.com>
#
# This file is part of Stardicter <https://cihar.com/software/slovnik/>
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

import io
import os.path

import stardicter.czechenglish
from stardicter.test_base import BaseTest


class CzechEnglishTest(BaseTest):
    writer_class = stardicter.czechenglish.CzechEnglishWriter


class CzechEnglishFileTest(CzechEnglishTest):
    def get_writer(self):
        '''
        Gets prepared writer class.
        '''
        return self.writer_class(
            file=io.open(os.path.join(
                os.path.dirname(__file__),
                'test_data.txt'
            ), 'rb')
        )
