# Copyright (C) 2016 Tim Diels <timdiels.m@gmail.com>
# 
# This file is part of Garage PM.
# 
# Garage PM is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Garage PM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Garage PM.  If not, see <http://www.gnu.org/licenses/>.

# http://stackoverflow.com/a/30091579/1031434
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL) # Ignore SIGPIPE

import pytest
from garage_pm.main import Context
from click.testing import CliRunner
from freezegun import freeze_time

@pytest.fixture
def context(qapp):
    _context = []
    
    @Context.command()
    def main(context):
        _context.append(context)
    
    CliRunner().invoke(main, catch_exceptions=False)
    
    return _context[0]

@pytest.yield_fixture
def now():
    '''
    Freezegun fake time
    
    Note: pyqt ignores freezegun
    '''
    with freeze_time('2000-1-1') as frozen_datetime:
        yield frozen_datetime