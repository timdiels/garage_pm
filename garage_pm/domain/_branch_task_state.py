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
from ._common import PlanningState, DependencyCycleError
from ._task_state import TaskState

class BranchTaskState(TaskState):
    
    def __init__(self, common_data):
        super().__init__(common_data)
        self._children = []

    def _get_planning_state(self):
        '''
        Returns
        -------
        TaskState
        '''
        return self._planning_state
    
    def _on_child_planning_state_changed(self, child):
        self._update_planning_state()
        self._dependency_graph[self.end_node][child.end_node]['active'] = child.is_active
    
    def _update_planning_state(self):
        old_state = self._planning_state
        if any(child.planning_state == PlanningState.planned for child in self.children):
            self._planning_state = PlanningState.planned
        else:
            self._planning_state = PlanningState.finished
        if old_state != self._planning_state:
            self.events.planning_state_changed.emit(self._task)
        
    def _set_planning_state(self, value):
        raise self.validate_set_planning_state(value)
        
    def validate_set_planning_state(self, state):
        return InvalidOperationError("A branch task's state is derived from its child tasks, not set")
    
    @property
    def children(self):
        return tuple(self._children)
    
    def _insert_child(self, index, child):
        ex = self._validate_insert_child(index, child)
        if ex:
            raise ex
        self._dependency_graph.add_edges_from((
            (child.start_node, self.start_node, {'active': True}),
            (self.end_node, child.end_node, {'active': True})
        ))
        cycles = self._dependency_cycles
        if cycles:
            self._remove_child_dependencies(child)
            raise DependencyCycleError(cycles)
        self._children.insert(index, child)
        child._parent = self._task
        child.events.planning_state_changed.connect(self._on_child_planning_state_changed)
        self._on_child_planning_state_changed(child)
            
    def _validate_insert_child(self, index, child): # not a ton of validation needed as it's internal and we know how to behave
        assert child not in self.children
        assert not child.parent
        if self._has_finished_depender and child.planning_state == PlanningState.planned:
            return ValueError('Cannot insert planned task into finished branch which is depended on (perhaps indirectly) by a finished task')
        return None
            
    def _remove_child_dependencies(self, child):
        '''
        Remove structural parent-child dependencies
        '''
        self._dependency_graph.remove_edges_from((
            (child.start_node, self.start_node),
            (self.end_node, child.end_node)
        ))
        
    def _remove_child(self, child):
        child._parent = None
        child.events.planning_state_changed.disconnect(self._on_child_planning_state_changed)
        self._children.remove(child)
        self._remove_child_dependencies(child)
        if not self._children and not self._is_root:
            self._task._become_effort_task()
        else:
            self._update_planning_state()
        
    @property
    def is_leaf(self):
        return False

    def validate_set_delegated(self, delegated):
        ex = super().validate_set_delegated(delegated)
        if ex:
            return ex
        if delegated:
            return ValueError('Cannot delegate branch task')
        return None
