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

class Task(object):
    
    '''
    See `TaskState` for full interface.
    
    Do not create this directly. Use context.tasks.root instead.
    
    Parameters
    ----------
    name : str
    qt_parent : QObject
        parent of self.events, do not confuse it with self.parent, the Task parent
    '''
    
    def __init__(self, name, context, is_root=False):
        self._common = TaskStateData(name, self, context, is_root)
        if is_root:
            self._state = BranchTaskState(self._common)
        else:
            self._become_effort_task()
        
        # one time init (not to be repeated when changing state)
        self._dependency_graph.add_nodes_from([self.start_node, self.end_node])
        
    def __getattr__(self, attr):
        return getattr(self._state, attr)
    
    def __setattr__(self, attr, value):
        if attr in ('_common', '_state'):
            super().__setattr__(attr, value)
        else:
            setattr(self._state, attr, value)
    
    def _become_branch_task(self):
        self._state = BranchTaskState(self._common)
        self._dependency_graph.remove_edge(self.end_node, self.start_node)
        
    def __become_leaf_task(self):
        self._dependency_graph.add_edge(self.end_node, self.start_node, {'active': True})
        
    def _become_delegated_task(self):
        self._state = DelegatedTaskState(self._common)
        self.__become_leaf_task()
        
    def _become_effort_task(self):
        self._state = EffortTaskState(self._common)
        self.__become_leaf_task()
        
    def __repr__(self):
        return 'Task({!r})'.format(self.name)
    
from ._task_state import TaskStateData
from ._effort_task_state import EffortTaskState
from ._branch_task_state import BranchTaskState
from ._delegated_task_state import DelegatedTaskState