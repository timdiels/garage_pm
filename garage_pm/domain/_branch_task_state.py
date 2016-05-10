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

from ._common import PlanningState
from ._task_state import TaskState

class BranchTaskState(TaskState):
    
    _planning_state_priorities = (PlanningState.planned, PlanningState.not_planned, PlanningState.cancelled, PlanningState.finished)
    
    def __init__(self, common_data):
        super().__init__(common_data)
        self._children = []

    def _get_planning_state(self):
        '''
        Returns
        -------
        TaskState
        '''
        child_states = set(child.planning_state for child in self.children)
        for state in self._planning_state_priorities:
            if state in child_states:
                return state
        assert False
        
    def _set_planning_state(self, value):
        raise ValueError(self.validate_set_planning_state(value))
        
    def validate_set_planning_state(self, state):
        return "A branch task's state is derived from its child tasks, not set"
    
    @property
    def children(self):
        return tuple(self._children)
    
    def insert_children(self, index, children):
        if set(children) & set(self._children):
            raise ValueError("Cannot add tasks as child when they're already a child of this task")
        if any(x.parent for x in children):
            raise ValueError("May only make orphans into children of a task")
        self._children[index:index] = children
        for child in children:
            child._common.parent = self._task
            
    @property
    def is_child_insertion_disallowed(self):
        return None
            
    def remove_children(self, begin, end):
        for child in self._children[begin:end]:
            child._common.parent = None
        del self._children[begin:end]
        if not self._children:
            self._task._become_effort_task()
        
    @property
    def is_leaf(self):
        return False
    