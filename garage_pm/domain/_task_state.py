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
from PyQt5.QtCore import QObject, pyqtSignal
from itertools import chain
from ._common import PlanningState

class _Events(QObject):
    
    name_changed = pyqtSignal(str)
    description_changed = pyqtSignal(str)
    planning_state_changed = pyqtSignal(PlanningState)
    set_planning_state_validity_changed = pyqtSignal([PlanningState, str])
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self._task = task
        
    def __getattr__(self, attr):
        return getattr(self._task._state._events, attr)

class TaskStateData(object):
    
    def __init__(self, name, task, qt_parent):
        self.events = _Events(task, qt_parent)
        self.task = task
        self.qt_parent = qt_parent
        self.name = name
        self.description = ''
        self.dependencies = set()
        self.dependers = set() # inverse relation of dependencies, i.e. those who depend on us
        self.parent = None

class TaskState(object):
    
    def __init__(self, task_state_data):
        self._common = task_state_data
        self._events = QObject(self._qt_parent)
    
    @property
    def _dependers(self):
        return self._common.dependers
    
    @property
    def _task(self):
        return self._common.task
    
    @property
    def _qt_parent(self):
        return self._common.qt_parent
    
    @property
    def events(self):
        return self._common.events
            
    @property
    def name(self):
        return self._common.name
    
    @name.setter
    def name(self, value):
        if self._common.name != value:
            self._common.name = value
            self.events.name_changed.emit(self._common.name)
            
    @property
    def description(self):
        return self._common.description
    
    @description.setter
    def description(self, value):
        if self._common.description != value:
            self._common.description = value
            self.events.description_changed.emit(self._common.description)
        
    @property
    def is_active(self):
        return self.planning_state in (PlanningState.planned, PlanningState.finished)
    
    @property
    def parent(self):
        return self._common.parent
    
    def validate_insert_children(self, index, children):
        '''
        Get whether may call insert_children with given args
        
        Returns
        -------
        Exception or None
            the exception that would be thrown if called with these args,
            ``None`` otherwise
        '''
        raise NotImplementedError()
    
    @property
    def children(self):
        '''
        Get children
        
        Returns
        -------
        tuple([Task])
        '''
        raise NotImplementedError()
    
    @property
    def ancestors(self):
        if self.parent:
            yield from self.parent.ancestors
            yield self.parent
            
    @property
    def descendants(self):
        for child in self.children:
            yield child
            yield from child.descendants
    
    @property
    def is_leaf(self):
        '''
        Get whether is leaf (True) or branch (False)
        '''
        raise NotImplementedError()
    
    @property
    def dependencies(self):
        '''
        Get direct dependencies, in addition to the parent's
        
        Yields
        ------
        Task
            tasks that must be finished in addition to the parent task before this task can start
        '''
        return iter(self._common.dependencies)
    
    def add_dependency(self, task):
        if self.planning_state == PlanningState.finished:
            raise InvalidOperationError('Cannot add dependency to finished task')
        if task in self.ancestors:
            raise ValueError('Task may not depend on an ancestor')
        if task in self.descendants:
            raise ValueError('Task may not depend on a descendant')
        for dependency in self._common.dependencies:
            if task in dependency.descendants:
                return
        self._common.dependencies -= {x for x in self._common.dependencies if x in task.descendants} 
        self._common.dependencies.add(task)
        task._dependers.add(self)
        
    def remove_dependency(self, task):
        self._common.dependencies.remove(task)
        task._dependers.remove(self)
    
    @property
    def start_dependencies(self):
        '''
        Get tasks that must be finished before this task can start
        
        Yields
        -------
        Task
            returns the direct dependencies only, i.e. not dependencies of dependencies.
        '''
        if self.parent:
            return chain(self.dependencies, self.parent.start_dependencies)
        else:
            return self.dependencies
        
    @property
    def end_dependencies(self):
        '''
        Get tasks that must be finished before this task can start
        
        Yields
        -------
        Task
            returns the direct dependencies only, i.e. not dependencies of dependencies.
        '''
        return chain(self.start_dependencies, (x for x in self.children if x.is_active))
    
    planning_state = property(
        fget=lambda self: self._get_planning_state(), 
        fset=lambda self, value: self._set_planning_state(value),
        doc='''
        Returns
        -------
        PlanningState
        '''
    )
    
    def validate_set_planning_state(self, state):
        '''
        Get whether may set given state
        
        Parameters
        ----------
        state : PlanningState

        Returns
        -------
        Exception or None
            the exception that would be thrown if called with these args,
            ``None`` otherwise
        '''
        raise NotImplementedError()
    
    @property
    def _has_unfinished_end_dependencies(self):
        return any(dependency.planning_state != PlanningState.finished for dependency in self.end_dependencies)

    @property
    def _has_finished_depender(self):
        '''
        Get whether has a (direct or indirect) finished depender
        '''
        dependers = set.union(*chain((x._dependers for x in self.ancestors), (self._dependers,)))
        return any(x.planning_state == PlanningState.finished for x in dependers)
        