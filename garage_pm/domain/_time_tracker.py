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

from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
from chicken_turtle_util.exceptions import InvalidOperationError
from ._common import Interval, EmptyIntervalError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TimeTracker(object):
    
    class _Events(QObject):
        
        current_interval_changed = pyqtSignal(object)
        
        def __init__(self, qt_parent):
            super().__init__()
    
    def __init__(self, context):
        self.events = self._Events(context.qt_parent)
        self._current_task = None
        self._current_start = None
        self._current_interval = None
        context.minute_timer.timeout.connect(self._update_current_interval)
    
    def start(self, task):
        if self._current_task:
            raise InvalidOperationError('')
        self._current_task = task
        self._current_start = datetime.now()
    
    def stop(self):
        if not self._current_task:
            raise InvalidOperationError('')
        self._current_task = None
        self._current_start = None
        self._update_current_interval()
    
    @property
    def current_task(self):
        '''
        Returns
        -------
        Task
            ``None`` if not time tracking, or when time tracking interval is too short
        '''
        return self._current_task
    
    @property
    def current_interval(self):
        '''
        Returns
        -------
        Interval or None
            ``None`` if not time tracking, or when time tracking interval is too short
        '''
        return self._current_interval
        
    def _update_current_interval(self):
        logger.error(datetime.now())
        old = self._current_interval
        if not self._current_start:
            self._current_interval = None
        else:
            try:
                self._current_interval = Interval(self._current_start, datetime.now())
            except EmptyIntervalError:
                self._current_interval = None
        if self._current_interval != old:
            self.events.current_interval_changed.emit(self)
