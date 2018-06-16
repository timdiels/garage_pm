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
from datetime import datetime
    
class EffortTaskState(LeafTaskState):
    
    def __init__(self, common_data):
        super().__init__(common_data)
        self._effort_estimates = _EffortEstimates(self._task, self._context)
        self._events = _EffortTaskStateEvents(self._context.qt_parent)
        
        # predicted effort
        self._predicted_effort = None
        for estimate_type in EstimateType:
            self.effort_estimates.changed[estimate_type].connect(self._update_predicted_effort)

        # effort spent
        self.__effort_spent = []
        self._effort_spent = ()
        self._context.time_tracker.events.current_interval_changed.connect(self._update_effort_spent)
            
        # actual effort
        self._actual_effort = timedelta()
        self._events.effort_spent_changed.connect(self._update_actual_effort)
    
        # planning state
        if self._planning_state == PlanningState.finished:  # we have no effort spent yet, can't be finished, revert to being planned
            self.planning_state = PlanningState.planned
            
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
            self.events.predicted_effort_changed.emit(self._task)
    
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
        self._actual_effort = sum((x.duration for x in self.effort_spent), timedelta())
        if old_value != self._actual_effort:
            self.events.actual_effort_changed.emit(self._task)
    
    @property
    def effort_spent(self):
        '''
        Get list of efforts spent on the task
        
        Returns
        -------
        tuple([Interval])
            Time intervals of effort spent on the task 
        '''
        return self._effort_spent
    
    def _update_effort_spent(self):
        old = self._effort_spent
        self._effort_spent = list(self.__effort_spent)
        time_tracker = self._context.time_tracker
        if time_tracker.current_task == self._task and time_tracker.current_interval:
            self._effort_spent.append(time_tracker.current_interval)
        self._effort_spent = tuple(self._effort_spent)
        if self._effort_spent != old:
            self.events.effort_spent_changed.emit(self._task)
    
    def insert_effort_spent(self, index, effort):
        '''
        Parameters
        ----------
        index : int
        effort : Interval
        '''
        if self._has_unfinished_dependencies:
            raise InvalidOperationError('Cannot spend effort on task before its end_dependencies have finished')
        if self.planning_state == PlanningState.finished:
            raise InvalidOperationError('Cannot insert effort into finished task')
        if effort.end > datetime.now():
            raise ValueError('Effort spent may not lie in the future: {}'.format(effort))
        for interval in self._context.effort_intervals:
            if effort.intersects(interval):
                raise ValueError('Effort intervals may not overlap: {} and {}'.format(interval, effort))
        self.__effort_spent.insert(index, effort)
        self._context.effort_intervals.add(effort)
        self._update_effort_spent()
        
    def remove_effort_spent(self, effort):
        '''
        Parameters
        ----------
        effort : Interval
        '''
        if self.planning_state == PlanningState.finished:
            raise InvalidOperationError('Cannot remove effort from finished task')
        self.__effort_spent.remove(effort)
        self._context.effort_intervals.remove(effort)
        self._update_effort_spent()
        
    def validate_set_planning_state(self, state):
        ex = super().validate_set_planning_state(state)
        if ex:
            return ex
        if state == PlanningState.finished and self.actual_effort == timedelta():
            return ValueError('Cannot finish a task effortlessly')
        else:
            return None
        
    def validate_set_delegated(self, delegated):
        ex = super().validate_set_delegated(delegated)
        if ex:
            return ex
        if self.effort_spent and delegated:
            return ValueError('Cannot delegate task that already has effort spent on it')
        return None
    
    def dispose(self):
        super().dispose()
        self._context.effort_intervals -= set(self.effort_spent)
        self._context.time_tracker.events.current_interval_changed.disconnect(self._update_effort_spent)
            
from ._task import Task

class _EffortEstimates(object):
    
    '''
    Effort estimates given by user
    '''
    
    class _Events(QObject):
        
        optimistic_effort_changed = pyqtSignal(Task)
        likely_effort_changed = pyqtSignal(Task)
        pessimistic_effort_changed = pyqtSignal(Task)
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self._signals = {
                EstimateType.optimistic: self.optimistic_effort_changed,
                EstimateType.likely: self.likely_effort_changed,
                EstimateType.pessimistic: self.pessimistic_effort_changed,
            }
            
        def __getitem__(self, key):
            return self._signals[key]
    
    def __init__(self, task, context):
        self.changed = self._Events(context.qt_parent)
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
            self.changed[key].emit(self._task)
            
class _EffortTaskStateEvents(QObject):
    predicted_effort_changed = pyqtSignal(Task)
    actual_effort_changed = pyqtSignal(Task)
    effort_spent_changed = pyqtSignal(Task) #TODO add a test for time tracking hitting 1 minute, at that point, and every tick from then on, an event should be sent out as effort spent will have changed. If we added a cancel, that affects it too (if >=1min)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        