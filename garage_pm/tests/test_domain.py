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

from PyQt5.QtCore import QObject
import pytest
from garage_pm.domain import Task, Interval, EstimateType, TaskState
from datetime import datetime, timedelta
from itertools import product

@pytest.fixture
def qt_parent():
    return QObject()

class TestTask(object):
    
    @pytest.fixture
    def task(self, qt_parent):
        return Task('name', qt_parent)
        
    @pytest.fixture
    def child1(self, task, qt_parent):
        return Task('child1', qt_parent)
        
    @pytest.fixture
    def child2(self, task, qt_parent):
        return Task('child2', qt_parent)
    
    @pytest.fixture
    def child3(self, task, qt_parent):
        return Task('child3', qt_parent)
    
    @pytest.fixture
    def interval1(self):
        return Interval(datetime.now(), datetime.now() + timedelta(minutes=1))
    
    @pytest.fixture
    def interval2(self, interval1):
        delta = timedelta(minutes=1)
        return Interval(interval1.begin + delta, interval1.end + delta)
    
    @pytest.fixture
    def interval3(self, interval2):
        delta = timedelta(minutes=1)
        return Interval(interval2.begin + delta, interval2.end + delta)
        
    class TestChildren(object):
        
        def test_happy_days(self, task, child1, child2):
            '''
            Test initial value, insert, remove
            '''
            assert task.children == ()
            
            task.insert_children(0, [child1,child2])
            assert task.children == (child1, child2)
            
            task.remove_children(1,2)
            assert task.children == (child1,)
            
            assert child1.parent == task
            assert child2.parent is None
            
        def test_raise_on_reinsert(self, task, child1):
            '''
            When insert child as child again, raise
            '''
            task.insert_children(0, [child1])
            with pytest.raises(ValueError) as ex:
                task.insert_children(0, [child1])
            assert 'already a child' in str(ex.value)
            
        def test_raise_on_insert_non_orphan(self, task, child1, child2):
            '''
            When insert child with parent, raise
            '''
            task.insert_children(0, [child1])
            with pytest.raises(ValueError) as ex:
                child2.insert_children(0, [child1])
            assert 'May only make orphans into children of a task' in str(ex.value)
            
        def test_raise_on_becoming_invalid_non_leaf(self, task, interval1, child1):
            '''
            When inserting in a leaf with actual_effort!=0, raise
            
            Note: test overlaps with TestEffortSpent
            '''
            task.insert_effort_spent(0, [interval1])
            with pytest.raises(ValueError) as ex:
                task.insert_children(0, [child1])
            assert 'Task cannot become a parent as it already has effort spent on it' in str(ex.value)
            
    class TestLeafEffort(object):
        
        '''
        Test effort_estimates in a leaf task
        '''
        
        @pytest.mark.parametrize('estimate_type', EstimateType)
        def test_default_value(self, task, estimate_type):
            assert task.effort_estimates[estimate_type] is None
        
        @pytest.mark.parametrize('estimate_type, value', product(EstimateType, (-1, 0)))
        def test_raise_on_set_invalid_value(self, task, estimate_type, value):
            '''
            When setting negative or 0 effort, raise
            '''
            with pytest.raises(ValueError) as ex:
                task.effort_estimates[estimate_type] = timedelta(minutes=value)
            assert 'estimate must be > timedelta(0)' in str(ex.value)
            
        @pytest.mark.parametrize('estimate_type', EstimateType)
        def test_set_none(self, task, estimate_type):
            '''
            When setting None, set just fine
            '''
            task.effort_estimates[estimate_type] = None
            
        def test_predicted(self, task):
            '''
            Test simple case for predicted_effort
            '''
            assert task.predicted_effort is None
            task.effort_estimates[EstimateType.optimistic] = timedelta(days=6)
            assert task.predicted_effort is None
            task.effort_estimates[EstimateType.likely] = timedelta(hours=12)
            assert task.predicted_effort is None
            task.effort_estimates[EstimateType.pessimistic] = timedelta(minutes=18)
            assert task.predicted_effort == timedelta(days=1, hours=8, minutes=3)
            
        def test_actual_effort(self, task, interval1):
            '''
            Test simple case for actual effort
            '''
            assert task.actual_effort == timedelta()
            task.insert_effort_spent(0, [interval1])
            assert task.actual_effort == interval1.duration

    def test_is_leaf(self, task, child1):
        assert task.is_leaf
        task.insert_children(0, [child1])
        assert not task.is_leaf
        
    class TestState(object):
        
        def test_default(self, task):
            assert task.state == TaskState.planned
            for state in TaskState:
                # may enter any state except finished by default
                if state != TaskState.finished:
                    task.state = state
                    assert task.state == state
            
        def test_cannot_set_leaf_finished(self, task, interval1):
            '''
            Cannot finish leaf when actual_effort==0
            '''
            with pytest.raises(ValueError) as ex:
                task.state = TaskState.finished
            assert 'Cannot finish a task effortlessly' in str(ex.value)
            
            # but can finish with effort
            task.insert_effort_spent(0, [interval1])
            task.state = TaskState.finished
            
        def test_branch(self, task, child1, child2, interval1):
            '''
            Branch tasks take upon the highest priority state of their children
            
            Not to be confused with task priorities (if we decided to implement that)
            
            priorities: planned > not planned > cancelled > finished
            '''
            task.insert_children(0, [child1, child2])
            child1.insert_effort_spent(0, [interval1])
            child2.insert_effort_spent(0, [interval1])
            
            # A branch task may not have its state set
            for state in TaskState: 
                with pytest.raises(ValueError) as ex:
                    task.state = state
                assert 'May not set state on branch task' in str(ex.value)

            # Parent state is that of the highest 'priority' child state
            priorities = Task._task_state_priorities
            for i in range(len(priorities)):
                child1.state = priorities[i]
                for state in priorities[i:]:
                    child2.state = state
                    assert task.state == priorities[i]
                    
    def test_is_active(self, task, interval1):
        task.insert_effort_spent(0, [interval1])
        assert task.is_active
        task.state = TaskState.finished
        assert task.is_active
        task.state = TaskState.cancelled
        assert not task.is_active
        task.state = TaskState.not_planned
        assert not task.is_active

    class TestBranchEffort(object):
        
        @pytest.fixture(params=(TaskState.not_planned, TaskState.cancelled))
        def branch(self, request, qt_parent, child1, child2, child3, interval1, interval2, interval3):
            branch = Task('branch', qt_parent)
            branch.insert_children(0, [child1, child2, child3])
            child1.insert_effort_spent(0, [interval1])
            child2.insert_effort_spent(0, [interval2])
            child3.insert_effort_spent(0, [interval3])
            child3.state = request.param  # make inactive
            return branch
            
        @pytest.mark.parametrize('estimate_type', EstimateType)
        def test_raise_on_set(self, branch, estimate_type):
            with pytest.raises(ValueError) as ex:
                branch.effort_estimates[estimate_type] = timedelta(1)
            assert 'May not set effort estimate on branch task' in str(ex.value)
        
        @pytest.mark.parametrize('estimate_type', EstimateType)    
        def test_get_estimate(self, branch, estimate_type):
            '''
            When get estimate, take sum of active children
            '''
            for i, child in enumerate(branch.children): 
                child.effort_estimates[estimate_type] = timedelta(days=i+1)
            assert branch.effort_estimates[estimate_type] == timedelta(days=1+2)
        
        def test_get_actual_effort(self, branch, child1, child2):
            '''
            When get actual_effort, take sum of active children
            '''
            assert branch.actual_effort == child1.actual_effort + child2.actual_effort
            
        def test_get_predicted_effort(self, branch):
            '''
            When get predicted_effort, take sum of active children; if either is None, so is parent
            '''
            for estimate_type in EstimateType:
                assert branch.predicted_effort is None  # when a child has None as predicted_effort, so has parent
                for i, child in enumerate(branch.children): 
                    child.effort_estimates[estimate_type] = timedelta(days=i+1)
            assert branch.predicted_effort == timedelta(days=1+2)
            
            # unactive children with predicted_effort=None do not affect parent
            branch.children[-1].effort_estimates[EstimateType.likely] = None
            assert branch.predicted_effort is not None
        