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

from chicken_turtle_util.exceptions import InvalidOperationError
from ._leaf_task_state import LeafTaskState
from garage_pm.domain._common import PlanningState

class DelegatedTaskState(LeafTaskState):

    def __init__(self, common_data):
        super().__init__(common_data)
        self._duration = None
            
    def _validate_insert_child(self, index, child):
        return InvalidOperationError('Cannot add child tasks to a delegated task')

    def _get_delegated(self):
        return True

    @property
    def duration(self):
        return self._duration
    
    @duration.setter
    def duration(self, value):
        if self.planning_state == PlanningState.finished:
            raise InvalidOperationError('Cannot change duration on finished task')
        self._duration = value