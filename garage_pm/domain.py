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

'''
PM domain classes
'''

from PyQt5.QtCore import QObject, pyqtSignal
from datetime import timedelta
from enum import Enum

class Interval(object):
    
    def __init__(self, begin, end):
        '''
        Parameters
        ----------
        start : datetime.datetime
        end : datetime.datetime
        '''
        assert begin < end 
        self._begin = begin
        self._end = end
        
    @property
    def begin(self):
        return self._begin
    
    @begin.setter
    def begin(self, value):
        self._validate(value, self._end)
        self._begin = value
    
    @property
    def end(self):
        return self._end
    
    @end.setter
    def end(self, value):
        self._validate(self._begin, value)
        self._end = value
        
    def _validate(self, begin, end):
        if begin > end:
            raise ValueError('Interval must begin before it ends')
        if begin == end:
            raise ValueError('Interval must not be empty (i.e. begin != end)')
    
    @property
    def duration(self):
        return self._end - self._begin
    
    def __lt__(self, other):
        if self.begin == other.begin:
            return self.end < other.end
        else:
            return self.begin < other.begin

class TaskState(Enum):
    planned = 'Planned'
    finished = 'Finished'
    cancelled = 'Cancelled'

class Task(QObject):
    
    name_changed = pyqtSignal([str])
    description_changed = pyqtSignal([str])
    optimistic_effort_changed = pyqtSignal([timedelta])
    likely_effort_changed = pyqtSignal([timedelta])
    pessimistic_effort_changed = pyqtSignal([timedelta])
    predicted_effort_changed = pyqtSignal([timedelta])
    actual_effort_changed = pyqtSignal([timedelta])
    state_changed = pyqtSignal([TaskState])  # refers to self.state only
    effort_spent_changed = pyqtSignal()
    
    def __init__(self, name, parent):
        super().__init__(parent)
        self._parent = None
        self._children = []
        self._name = name
        self._description = ''
        self._optimistic_effort = timedelta()
        self._likely_effort = timedelta()
        self._pessimistic_effort = timedelta()
        self._effort_spent = []
        self._state = TaskState.planned
        
        self.optimistic_effort_changed.connect(self._on_effort_input_changed)
        self.likely_effort_changed.connect(self._on_effort_input_changed)
        self.pessimistic_effort_changed.connect(self._on_effort_input_changed)
        self.effort_spent_changed.connect(self._on_effort_spent_changed)
        
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if self._name != value:
            self._name = value
            self.name_changed.emit(self._name)
            
    @property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, value):
        if self._description != value:
            self._description = value
            self.description_changed.emit(self._description)
            
    @property
    def state(self):
        '''
        Returns
        -------
        TaskState
        '''
        return self._state
    
    @state.setter
    def state(self, value):
        if self._state != value:
            self._state = value
            self.state_changed.emit(self._state)
            
    @property
    def optimistic_effort(self):
        '''
        Get effort required in optimistic scenario, according to user
        
        Returns
        -------
        datetime.timedelta
        '''
        return self._optimistic_effort
    
    @optimistic_effort.setter
    def optimistic_effort(self, value):
        print('optimistic change')
        if self._optimistic_effort != value:
            self._optimistic_effort = value
            self.optimistic_effort_changed.emit(self._optimistic_effort)
            
    @property
    def likely_effort(self):
        '''
        Get effort required in the most likely scenario, according to user
        '''
        return self._likely_effort
    
    @likely_effort.setter
    def likely_effort(self, value):
        if self._likely_effort != value:
            self._likely_effort = value
            self.likely_effort_changed.emit(self._likely_effort)
            
    @property
    def pessimistic_effort(self):
        '''
        Get effort required in pessimistic scenario, according to user
        '''
        return self._pessimistic_effort
    
    @pessimistic_effort.setter
    def pessimistic_effort(self, value):
        if self._pessimistic_effort != value:
            self._pessimistic_effort = value
            self.pessimistic_effort_changed.emit(self._pessimistic_effort)
            
    def _on_effort_input_changed(self):
        '''When effort optimistic, likely or pessimistic change'''
        print('predicted')
        self.predicted_effort_changed.emit(self.predicted_effort)
            
    @property
    def predicted_effort(self):
        '''
        Get predicted required effort
        
        E.g. based on discrepancies between a user's estimates and actual effort spent on tasks
        '''
        return (self._optimistic_effort + 4 * self._likely_effort + self._pessimistic_effort)/6
    
    @property
    def actual_effort(self):
        '''
        Get total effort spent on this task
        
        Notes
        -----
        Effort of child tasks is excluded, like the other effort_* attributes.
        '''
        return sum((x.duration for x in self._effort_spent), timedelta())
    
    @property
    def effort_spent(self):
        '''
        Get list of efforts spent on the task
        
        Returns
        -------
        tuple([Interval])
            Time intervals of effort spent on the task 
        '''
        return tuple(self._effort_spent)
    
    def _on_effort_spent_changed(self):
        self.actual_effort_changed.emit(self.actual_effort)
    
    def insert_effort_spent(self, index, effort):
        '''
        Parameters
        ----------
        index : int
        effort : [Interval]
        '''
        self._effort_spent[index:index] = effort
        self.effort_spent_changed.emit()
        
    def remove_effort_spent(self, begin, end):
        del self._effort_spent[begin:end]
        self.effort_spent_changed.emit()
    
    @property
    def children(self):
        '''
        Get children
        
        Returns
        -------
        tuple([Task])
        '''
        return tuple(self._children)
    
    @property
    def parent(self):
        return self._parent
    
    @property
    def ancestors(self):
        if self._parent:
            return self._parent.ancestors + [self._parent]
        else:
            return []
        
    def __repr__(self):
        return 'Task({!r})'.format(self.name)
    
    def insert_children(self, index, children):
        self._children[index:index] = children
        for child in children:
            child._parent = self
            
    def remove_children(self, begin, end):
        for child in self._children[begin:end]:
            child._parent = None
        del self._children[begin:end]
        