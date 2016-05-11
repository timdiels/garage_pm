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
from datetime import timedelta
from chicken_turtle_util.exceptions import InvalidOperationError
from ._common import EstimateType, PlanningState
from ._leaf_task_state import LeafTaskState
    
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
        return self._estimates[key]
    
    def __setitem__(self, key, value):
        '''
        Parameters
        ----------
        key : Estimate
        value : datetime.timedelta or None
        '''
        if self._task.planning_state == PlanningState.finished:
            raise InvalidOperationError('Cannot edit effort estimates on finished task')
        if value is not None and value <= timedelta():
            raise ValueError('Effort estimate must be > timedelta(0)')
        if self._estimates[key] != value:
            self._estimates[key] = value
            self.changed[key].emit(value)
            
class _EffortTaskStateEvents(QObject):
    predicted_effort_changed = pyqtSignal(object)
    actual_effort_changed = pyqtSignal(timedelta)
    effort_spent_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
class EffortTaskState(LeafTaskState):
    
    def __init__(self, common_data):
        super().__init__(common_data)
        self._effort_estimates = _EffortEstimates(self._task, self._qt_parent)
        self._effort_spent = []
        self._events = _EffortTaskStateEvents(self._qt_parent)
        
        # predicted effort
        self._predicted_effort = None
        for estimate_type in EstimateType:
            self.effort_estimates.changed[estimate_type].connect(self._update_predicted_effort)

        # actual effort
        self._actual_effort = timedelta()
        self._events.effort_spent_changed.connect(self._update_actual_effort)
    
    @property
    def effort_estimates(self):
        return self._effort_estimates
    
    @property
    def predicted_effort(self):
        '''
        Get predicted required effort
        
        E.g. based on discrepancies between a user's estimates and actual effort spent on tasks
        '''
        return self._predicted_effort
        
    def _update_predicted_effort(self):
        old_value = self._predicted_effort
        if any(self._effort_estimates[x] is None for x in EstimateType):
            self._predicted_effort = None
        else:
            weights = {
                EstimateType.optimistic: 1,
                EstimateType.likely: 4,
                EstimateType.pessimistic: 1,
            }
            self._predicted_effort = sum((weight * self._effort_estimates[estimate_type] for estimate_type, weight in weights.items()), timedelta()) / sum(weights.values())
        if old_value != self._predicted_effort:
            self.events.predicted_effort_changed.emit(self._predicted_effort)
    
    @property
    def actual_effort(self):
        '''
        Get total effort spent on this task
        
        Notes
        -----
        Effort of child tasks is excluded, like the other effort_* attributes.
        '''
        return self._actual_effort
    
    def _update_actual_effort(self):
        old_value = self._actual_effort
        self._actual_effort = sum((x.duration for x in self._effort_spent), timedelta())
        if old_value != self._actual_effort:
            self.events.actual_effort_changed.emit(self._actual_effort)
    
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
    
    def insert_effort_spent(self, index, effort):
        '''
        Parameters
        ----------
        index : int
        effort : [Interval]
        '''
        if self._has_unfinished_end_dependencies:
            raise InvalidOperationError('Cannot spend effort on task before its end_dependencies have finished')
        if self.planning_state == PlanningState.finished:
            raise InvalidOperationError('Cannot insert effort into finished task')
        self._effort_spent[index:index] = effort
        self.events.effort_spent_changed.emit()
        
    def remove_effort_spent(self, begin, end):
        if self.planning_state == PlanningState.finished:
            raise InvalidOperationError('Cannot remove effort from finished task')
        del self._effort_spent[begin:end]
        self.events.effort_spent_changed.emit()
        
    def validate_set_planning_state(self, state):
        ex = super().validate_set_planning_state(state)
        if ex:
            return ex
        if state == PlanningState.finished and self.actual_effort == timedelta():
            return ValueError('Cannot finish a task effortlessly')
        else:
            return None
        