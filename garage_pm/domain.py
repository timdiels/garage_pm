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
from datetime import datetime, timedelta
from enum import Enum
from itertools import chain

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
    not_planned = 'Not planned'
    planned = 'Planned'
    finished = 'Finished'
    cancelled = 'Cancelled'

class EstimateType(Enum):
    
    '''
    Type of estimate that can be made
    '''
    
    optimistic = 'Optimistic'
    likely = 'Likely'
    pessimistic = 'Pessimistic'
    
class _EffortEstimates(object):
    
    '''
    Effort estimates given by user
    '''
    
    class _Events(QObject):
        
        optimistic_effort_changed = pyqtSignal(object)
        likely_effort_changed = pyqtSignal(object)
        pessimistic_effort_changed = pyqtSignal(object)
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self._signals = {
                EstimateType.optimistic: self.optimistic_effort_changed,
                EstimateType.likely: self.likely_effort_changed,
                EstimateType.pessimistic: self.pessimistic_effort_changed,
            }
            
        def __getitem__(self, key):
            return self._signals[key]
    
    def __init__(self, task, qt_parent):
        self.changed = self._Events(qt_parent)
        self._task = task
        self._estimates = {x: None for x in EstimateType}
        
    def __getitem__(self, key):
        '''
        Get estimated effort required, according to user
        
        Parameters
        ----------
        key : Estimate
            Whether the estimate is optimistic or ...
            
        Returns
        -------
        datetime.timedelta or None
            ``None`` iff user did not specify
        '''
        if self._task.is_leaf:
            return self._estimates[key]
        else:
            estimates = [x.effort_estimates[key] for x in self._task.children if x.is_active]
            if any(x is None for x in estimates):
                return None
            else:
                return sum(estimates, timedelta())
    
    def __setitem__(self, key, value):
        '''
        Parameters
        ----------
        key : Estimate
        value : datetime.timedelta or None
        '''
        if value is not None and value <= timedelta():
            raise ValueError('Effort estimate must be > timedelta(0)')
        if not self._task.is_leaf:
            raise ValueError('May not set effort estimate on branch task')
        if self._estimates[key] != value:
            self._estimates[key] = value
            self.changed[key].emit(value)

class _TaskEvents(QObject):
    name_changed = pyqtSignal(str)
    description_changed = pyqtSignal(str)
    predicted_effort_changed = pyqtSignal(timedelta)
    actual_effort_changed = pyqtSignal(timedelta)
    state_changed = pyqtSignal(TaskState)  # refers to self.state only
    planned_start_changed = pyqtSignal(object)
    planned_end_changed = pyqtSignal(datetime)
    predicted_start_changed = pyqtSignal(datetime)
    predicted_end_changed = pyqtSignal(datetime)
    state_validity_changed = pyqtSignal([TaskState, str])
    effort_spent_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
class Task(object):
    
    '''
    Parameters
    ----------
    parent : QObject
        parent of self.events, do not confuse it with self.parent, the Task parent
    '''
    
    _task_state_priorities = (TaskState.planned, TaskState.not_planned, TaskState.cancelled, TaskState.finished)
    
    def __init__(self, name, parent):
        self.events = _TaskEvents(parent)
        self._parent = None
        self._children = []
        self._name = name
        self._description = ''
        self._effort_estimates = _EffortEstimates(self, parent)
        self._effort_spent = []
        self._state = TaskState.planned
        self._planned_start = None
        self._dependencies = set()
        
        self.events.effort_spent_changed.connect(self._on_effort_spent_changed)
        
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if self._name != value:
            self._name = value
            self.events.name_changed.emit(self._name)
            
    @property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, value):
        if self._description != value:
            self._description = value
            self.events.description_changed.emit(self._description)
            
    @property
    def state(self):
        '''
        Returns
        -------
        TaskState
        '''
        if self.is_leaf:
            return self._state
        else:
            child_states = set(child.state for child in self.children)
            for state in self._task_state_priorities:
                if state in child_states:
                    return state
            assert False
    
    @state.setter
    def state(self, value):
        reason = self.validate_set_state(value)
        if reason:
            raise ValueError(reason)
        if self._state != value:
            self._state = value
            self.events.state_changed.emit(self._state)
            
    def validate_set_state(self, state):
        '''
        Get whether may set given state
        
        Parameters
        ----------
        state : TaskState

        Returns
        -------
        str or None
            ``None`` if the state may be entered, else the reason why it may not
            be entered
        '''
        if not self.is_leaf:
            return 'May not set state on branch task'
        elif state == TaskState.finished and self.actual_effort == timedelta():
            return 'Cannot finish a task effortlessly'
        else:
            return None
        
    @property
    def is_active(self):
        return self.state in (TaskState.planned, TaskState.finished)
            
    @property
    def planned_start(self):
        '''
        Date time at which task is planned to start.
        
        Returns
        -------
        datetime.datetime or None
            Returns ``None`` iff one of its paths along the dependency tree to the root has no task with start date set.
        '''
        return self._planned_start
    
    @planned_start.setter
    def planned_start(self, value):
        if self._planned_start != value:
            self._planned_start = value
            self.events.planned_start_changed.emit(self._planned_start)
            
    @property
    def planned_end(self):
        '''
        Date time at which task is planned to end.state_validity
        
        Returns
        -------
        datetime.datetime or None
            Returns ``None`` iff `planned_start` is None
        '''
        return None
    
    @property
    def predicted_start(self):
        '''
        Date time at which task is predicted to end.
        
        When effort has been spent on the task, this is the date time at which
        the task actually started.
        
        Returns
        -------
        datetime.datetime or None
            Returns ``None`` iff no effort has been spent on the task and one of its
            dependencies' `predicted_end` is None.
        '''
        return min((x.begin for x in self._effort_spent), default=None)
    
    @property
    def predicted_end(self):
        '''
        Date time at which task is predicted to end.
        
        When the task is finished, this is the date time at which the task
        actually ended.
        
        Returns
        -------
        datetime.datetime or None
            Returns ``None`` iff `predicted_start` is None and task is
            not finished.
        '''
        try:
            if self._state == TaskState.finished:
                return max((x.end for x in self._effort_spent), default=None)
            return None
        except Exception as ex:
            print(ex)
            raise ex
            
    @property
    def effort_estimates(self):
        return self._effort_estimates
    
    def _on_effort_input_changed(self): #TODO
        '''When effort optimistic, likely or pessimistic change'''
        self.events.predicted_effort_changed.emit(self.predicted_effort)
            
    @property
    def predicted_effort(self):
        '''
        Get predicted required effort
        
        E.g. based on discrepancies between a user's estimates and actual effort spent on tasks
        '''
        if any(self._effort_estimates[x] is None for x in EstimateType):
            return None
        weights = {
            EstimateType.optimistic: 1,
            EstimateType.likely: 4,
            EstimateType.pessimistic: 1,
        }
        return sum((weight * self._effort_estimates[estimate_type] for estimate_type, weight in weights.items()), timedelta()) / sum(weights.values())
    
    @property
    def actual_effort(self):
        '''
        Get total effort spent on this task
        
        Notes
        -----
        Effort of child tasks is excluded, like the other effort_* attributes.
        '''
        if self.is_leaf:
            return sum((x.duration for x in self._effort_spent), timedelta())
        else:
            return sum((x.actual_effort for x in self.children if x.is_active), timedelta())
    
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
        self.events.actual_effort_changed.emit(self.actual_effort)
    
    def insert_effort_spent(self, index, effort):
        '''
        Parameters
        ----------
        index : int
        effort : [Interval]
        '''
        self._effort_spent[index:index] = effort
        self.events.effort_spent_changed.emit()
        
    def remove_effort_spent(self, begin, end):
        del self._effort_spent[begin:end]
        self.events.effort_spent_changed.emit()
    
    @property
    def children(self):
        '''
        Get children
        
        Returns
        -------
        tuple([Task])
        '''
        return tuple(self._children)
    
    def insert_children(self, index, children):
        if set(children) & set(self._children):
            raise ValueError("Cannot add tasks as child when they're already a child of this task")
        if any(x.parent for x in children):
            raise ValueError("May only make orphans into children of a task")
        reason = self.is_child_insertion_disallowed
        if reason:
            raise ValueError(reason)
        
        self._children[index:index] = children
        for child in children:
            child._parent = self
            
    @property
    def is_child_insertion_disallowed(self): #TODO rename validate_insert_children
        '''
        Get whether task could be a valid parent
        
        Returns
        -------
        str or None
            if cannot be a parent, user-friendly reason, else None
        '''
        if self._effort_spent:
            return 'Task cannot become a parent as it already has effort spent on it'
        else:
            return None
        
    def remove_children(self, begin, end):
        for child in self._children[begin:end]:
            child._parent = None
        del self._children[begin:end]
        
    @property
    def is_leaf(self):
        '''
        Get whether is leaf (True) or branch (False)
        '''
        return not self._children
        
    @property
    def parent(self):
        return self._parent
    
    @property
    def ancestors(self):
        if self._parent:
            for ancestor in self._parent.ancestors:
                yield ancestor
            yield self._parent
            
    @property
    def descendants(self):
        for child in self._children:
            yield child
            for grandchild in child.descendants:
                yield grandchild
    
    @property
    def dependencies(self):
        '''
        Get additional direct dependencies
        
        Yields
        ------
        Task
            tasks that must be finished in addition to the parent task before this task can start
        '''
        return iter(self._dependencies)
    
    def add_dependency(self, task):
        if task in self.ancestors:
            raise ValueError('Task may not depend on an ancestor')
        if task in self.descendants:
            raise ValueError('Task may not depend on a descendant')
        for dependency in self._dependencies:
            if task in dependency.descendants:
                return
        self._dependencies -= {x for x in self._dependencies if x in task.descendants} 
        self._dependencies.add(task)
        
    def remove_dependency(self, task):
        self._dependencies.remove(task)
    
    @property
    def start_dependencies(self):
        '''
        Get tasks that must be finished before this task can start
        
        Yields
        -------
        Task
            returns the direct dependencies only, i.e. not dependencies of dependencies.
        '''
        if self._parent:
            return chain(self._dependencies, self._parent.start_dependencies)
        else:
            return iter(self._dependencies) 
        
    def __repr__(self):
        return 'Task({!r})'.format(self.name)
    