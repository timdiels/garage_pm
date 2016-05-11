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
from ._common import PlanningState
from ._task_state import TaskState

class LeafTaskState(TaskState):
    
    def __init__(self, common_data):
        super().__init__(common_data)
        self._planning_state = PlanningState.planned
    
    def _get_planning_state(self):
        return self._planning_state
    
    def _set_planning_state(self, value):
        ex = self.validate_set_planning_state(value)
        if ex:
            raise ex
        if self._planning_state != value:
            self._planning_state = value
            self._task.events.planning_state_changed.emit(self._planning_state)
    
    def validate_set_planning_state(self, state):
        if state == PlanningState.finished and self._has_unfinished_end_dependencies:
            return ValueError('Cannot finish before end_dependencies have finished')
        elif state != PlanningState.finished and self._has_finished_depender:
            return ValueError('Cannot unfinish task as a finished task depends on it (perhaps indirectly)')
        else:
            return None
        
    @property
    def children(self):
        return ()
    
    def insert_children(self, index, children):
        reason = self.validate_insert_children(index, children)
        if reason:
            raise reason
        else:
            self._task._become_branch_task(index, children)
    
    def validate_insert_children(self, index, children):
        if self.planning_state == PlanningState.finished:
            return InvalidOperationError('Cannot insert children into finished task')
        elif self.actual_effort:
            return InvalidOperationError('Leaf task with effort spent on it cannot become a branch task')
        else:
            return None
        
    @property
    def is_leaf(self):
        return True
