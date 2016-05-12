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
Test garage_pm.domain
'''

# Note: Each test takes into account only the features it introduces and all
# those that appear above it (in case those may cause conflicts).

from PyQt5.QtCore import QObject
import pytest
from chicken_turtle_util.exceptions import InvalidOperationError
from garage_pm.domain import Task, Interval, EstimateType, PlanningState
from garage_pm.domain._branch_task_state import BranchTaskState
from datetime import datetime, timedelta
from itertools import product

@pytest.fixture
def qt_object():
    return QObject()

@pytest.fixture
def task(qt_object):
    return Task('task1', qt_object)

@pytest.fixture
def task2(qt_object):
    return Task('task2', qt_object)
    
@pytest.fixture
def child1(task, qt_object):
    return Task('child1', qt_object)
    
@pytest.fixture
def child2(task, qt_object):
    return Task('child2', qt_object)

@pytest.fixture
def child3(task, qt_object):
    return Task('child3', qt_object)

@pytest.fixture
def interval1():
    return Interval(datetime.now(), datetime.now() + timedelta(minutes=1))

@pytest.fixture
def interval2(interval1):
    delta = timedelta(minutes=1)
    return Interval(interval1.begin + delta, interval1.end + delta)

@pytest.fixture
def interval3(interval2):
    delta = timedelta(minutes=1)
    return Interval(interval2.begin + delta, interval2.end + delta)

@pytest.fixture
def root_task(qt_object):
    t1 = Task('1', qt_object)
    t11 = Task('1.1', qt_object)
    t111 = Task('1.1.1', qt_object)
    t12 = Task('1.2', qt_object)
    t1.insert_children(0, [t11, t12])
    t11.insert_children(0, [t111])
    return t1
    
class TestChildren(object):
    
    '''
    Test child insertion, removal
    '''
    
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
        with pytest.raises(InvalidOperationError) as ex:
            task.insert_children(0, [child1])
        assert 'Leaf task with effort spent on it cannot become a branch task' in str(ex.value)

def test_is_leaf(task, child1):
    assert task.is_leaf
    task.insert_children(0, [child1])
    assert not task.is_leaf

def test_ancestors(root_task):
    assert tuple(root_task.ancestors) == ()
    for child in root_task.children:
        assert tuple(child.ancestors) == (root_task,)
        for grandchild in child.children:
            assert tuple(grandchild.ancestors) == (root_task, child)

def test_descendants(root_task):
    assert tuple(root_task.descendants) == (root_task.children[0], root_task.children[0].children[0], root_task.children[1])
    assert tuple(root_task.children[0].descendants) == (root_task.children[0].children[0],)
    assert tuple(root_task.children[0].children[0].descendants) == ()
    assert tuple(root_task.children[1].descendants) == ()
        
class TestEffort(object):
    
    '''
    Test effort on effort leaf tasks
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
        
    def test_effort_estimate_events(self, task, mocker):
        one_day = timedelta(days=1)
        for estimate_type in EstimateType:
            estimate_changed = mocker.Mock()
            task.effort_estimates.changed[estimate_type].connect(estimate_changed)
            
            task.effort_estimates[estimate_type] = one_day
            estimate_changed.assert_called_with(one_day)
            estimate_changed.reset_mock()
            
            task.effort_estimates[estimate_type] = one_day
            estimate_changed.assert_not_called()
    
    def test_predicted_effort_changed_event(self, task, mocker):
        predicted_changed = mocker.Mock()
        task.events.predicted_effort_changed.connect(predicted_changed)
        
        for estimate_type in EstimateType:
            task.effort_estimates[estimate_type] = timedelta(days=1)
        predicted_changed.assert_called_once_with(timedelta(days=1))
        predicted_changed.reset_mock()
         
        task.effort_estimates[EstimateType.optimistic] = None
        predicted_changed.assert_called_once_with(None)
        predicted_changed.reset_mock()
          
        task.effort_estimates[EstimateType.likely] = None
        predicted_changed.assert_not_called()
            
    def test_actual_effort_changed_event(self, task, interval1, mocker):
        actual_changed = mocker.Mock()
        task.events.actual_effort_changed.connect(actual_changed)
        
        task.insert_effort_spent(0, [interval1])
        actual_changed.assert_called_once_with(interval1.duration)
        actual_changed.reset_mock()
        
class TestDelegated(object):
    
    def test_leaf(self, task):
        # effort task is not delegated
        assert not task.delegated
        
        # switch to delegated
        task.delegated = True
        assert task.delegated
        
        # duration
        assert task.duration is None
        task.duration = timedelta(days=1)
        assert task.duration == timedelta(days=1)
        
        # cannot insert children
        with pytest.raises(InvalidOperationError):
            task.insert_children(0, [child1])
            
        # switching back to effort task
        task.delegated = False
        assert task.actual_effort == timedelta()  # is an effort task again
        
    def test_branch(self, task, child1):
        '''
        Branch cannot be delegated
        '''
        task.insert_children(0, [child1])
        assert not task.delegated
        with pytest.raises(ValueError):
            task.delegated = True
            
    def test_cannot_delegate_task_with_effort_spent(self, task, interval1):
        '''
        When delegating a task with effort spent, raise
        '''
        task.insert_effort_spent(0, [interval1])
        with pytest.raises(ValueError):
            task.delegated = True
        
class TestPlanningState(object):
    
    '''
    Test planning state on any kind of task
    '''
    
    @pytest.fixture
    def planning_state_changed(self, task, mocker):
        planning_state_changed = mocker.Mock()
        task.events.planning_state_changed.connect(planning_state_changed)
        return planning_state_changed
        
    def test_effort_task(self, task, interval1):
        '''
        Test happy days default, setting and getting
        '''
        assert task.planning_state == PlanningState.planned
        for planning_state in PlanningState:
            # may enter any planning_state except finished by default
            if planning_state != PlanningState.finished:
                task.planning_state = planning_state
                assert task.planning_state == planning_state
        
        # cannot finish without effort
        with pytest.raises(ValueError) as ex:
            task.planning_state = PlanningState.finished
        assert 'Cannot finish a task effortlessly' in str(ex.value)
        
        # can finish with effort
        task.insert_effort_spent(0, [interval1])
        task.planning_state = PlanningState.finished
    
    def test_delegated_task(self, task):
        '''
        Test happy days default, setting and getting
        '''
        assert task.planning_state == PlanningState.planned
        task.delegated = True
        for planning_state in PlanningState:
            task.planning_state = planning_state
            assert task.planning_state == planning_state
                
    @pytest.mark.parametrize('delegated', (True,False))
    def test_leaf_change_event(self, task, delegated, planning_state_changed):
        '''
        When planning state changes, emit event
        '''
        task.delegated = delegated
        
        task.planning_state = PlanningState.not_planned
        planning_state_changed.assert_called_once_with(PlanningState.not_planned)
        planning_state_changed.reset_mock()
        
        task.planning_state = PlanningState.not_planned
        planning_state_changed.assert_not_called()
        
    def test_branch(self, task, child1, child2, interval1, planning_state_changed):
        '''
        Branch tasks take upon the highest priority state of their children
        
        Not to be confused with task priorities (if we decided to implement that)
        
        priorities: planned > not planned > cancelled > finished
        
        Also test for planning state change events
        '''
        task.insert_children(0, [child1, child2])
        child1.insert_effort_spent(0, [interval1])
        child2.insert_effort_spent(0, [interval1])
        
        # A branch task may not have its planning_state set
        for planning_state in PlanningState:
            with pytest.raises(InvalidOperationError) as ex:
                task.planning_state = planning_state
            assert "A branch task's state is derived from its child tasks, not set" in str(ex.value)

        # Parent state is that of the highest 'priority' child state
        priorities = BranchTaskState._planning_state_priorities
        for i in range(len(priorities)):
            child1.planning_state = priorities[i]
            for planning_state in priorities[i:]:
                child2.planning_state = planning_state
                assert task.planning_state == priorities[i]
                
    def test_branch_change_event(self, task, child1, child2, planning_state_changed):
        # task switches from planned to cancelled
        child1.planning_state = PlanningState.cancelled
        task.insert_children(0, [child1])
        planning_state_changed.assert_called_once_with(PlanningState.cancelled)
        planning_state_changed.reset_mock()
        
        # task switches from cancelled to planned as we add a planned child
        task.insert_children(0, [child2])
        planning_state_changed.assert_called_once_with(PlanningState.planned)
        planning_state_changed.reset_mock()
        
        # task switches from planned to cancelled as child2 changes to cancelled
        child2.planning_state = PlanningState.cancelled
        planning_state_changed.assert_called_once_with(PlanningState.cancelled)
        planning_state_changed.reset_mock()
        
    def test_effort_delegated_switch(self, task):
        '''
        When switching between delegated and effort task, maintain planning state
        '''
        for planning_state in PlanningState:
            if planning_state == PlanningState.finished:
                continue
            task.planning_state = planning_state
            task.delegated = True
            assert task.planning_state == planning_state
            task.delegated = False
            assert task.planning_state == planning_state
        
    class TestFinishedIsFairlyImmutable(object):
        
        '''
        When a task is finished it should generally not be edited without first
        'reopening' it
        
        Name, description and children can still be edited though.
        '''
        
        def test_effort_task(self, task, interval1):
            task.insert_effort_spent(0, [interval1])
            task.planning_state = PlanningState.finished
            with pytest.raises(InvalidOperationError):
                task.effort_estimates[EstimateType.likely] = None
            with pytest.raises(InvalidOperationError):
                task.insert_effort_spent(0, [interval1])
            with pytest.raises(InvalidOperationError):
                task.remove_effort_spent(0, 1)
            with pytest.raises(InvalidOperationError):
                task.delegated = True
                
        def test_delegated_task(self, task):
            task.delegated = True
            task.planning_state = PlanningState.finished
            with pytest.raises(InvalidOperationError):
                task.duration = timedelta(days=1)
            with pytest.raises(InvalidOperationError):
                task.delegated = False
                
def test_is_active(task, interval1):
    task.insert_effort_spent(0, [interval1])
    assert task.is_active
    task.planning_state = PlanningState.finished
    assert task.is_active
    task.planning_state = PlanningState.cancelled
    assert not task.is_active
    task.planning_state = PlanningState.not_planned
    assert not task.is_active

class TestDependencies(object):
    
    '''
    Test task.dependencies, add_dependency, remove_dependency
    '''
    
    def test_happy_days(self, root_task):
        assert tuple(root_task.dependencies) == ()
        task11 = root_task.children[0]
        task12 = root_task.children[1]
        task11.add_dependency(task12)
        assert tuple(task11.dependencies) == (task12,)
        assert tuple(task12.dependencies) == ()
        
        task11.remove_dependency(task12)
        assert tuple(task11.dependencies) == ()
        
    def test_add_ancestor_or_descendant_raises(self, root_task):
        '''
        When adding ancestor or descendant as dependency, raise
        ''' 
        task11 = root_task.children[0]
        task111 = task11.children[0]
        for ancestor, task in ((root_task, task11), (root_task, task111)):
            with pytest.raises(ValueError) as ex:
                task.add_dependency(ancestor)
            assert 'Task may not depend on an ancestor' in str(ex.value)
            
            with pytest.raises(ValueError) as ex:
                ancestor.add_dependency(task)
            assert 'Task may not depend on a descendant' in str(ex.value)
            
    def test_add_removes_dep_children(self, root_task):
        '''
        When adding a task whose descendant is already depended on, remove that
        descendant from the dependencies
        '''
        root_task.children[1].add_dependency(root_task.children[0].children[0])
        root_task.children[1].add_dependency(root_task.children[0])
        assert tuple(root_task.children[1].dependencies) == (root_task.children[0],)
        
        # when removing, like adding, it's like removing an entire task subtree
        root_task.children[1].remove_dependency(root_task.children[0])
        assert tuple(root_task.children[1].dependencies) == ()
        
    def test_ignore_readd(self, root_task):
        '''
        When adding the same task twice, ignore silently
        '''
        root_task.children[0].add_dependency(root_task.children[1])
        root_task.children[0].add_dependency(root_task.children[1])
        assert tuple(root_task.children[0].dependencies) == (root_task.children[1],)
        
    def test_ignore_add_descendant_of_dep(self, root_task):
        '''
        When adding descendant of a task we already depend on, ignore it
        '''
        root_task.children[1].add_dependency(root_task.children[0])
        root_task.children[1].add_dependency(root_task.children[0].children[0])
        assert tuple(root_task.children[1].dependencies) == (root_task.children[0],)
        
    #TODO what if reparenting tasks?
    # Note: adding a dependency of a dependency is not necessarily ignored
    # Note: adding dependencies of the parent aren't necessarily ignored either
    
    class TestCannotMutateIfFinished(object):
        
        '''
        When a task is finished cannot add/remove dependencies
        '''
        
        def test_effort_task(self, task, task2, interval1):
            task.insert_effort_spent(0, [interval1])
            task.planning_state = PlanningState.finished
            with pytest.raises(InvalidOperationError):
                task.add_dependency(task2)
            with pytest.raises(InvalidOperationError):
                task.remove_dependency(task2)
                
        def test_delegated_task(self, task, task2):
            task.delegated = True
            task.planning_state = PlanningState.finished
            with pytest.raises(InvalidOperationError):
                task.add_dependency(task2)
            with pytest.raises(InvalidOperationError):
                task.remove_dependency(task2)
            
        def test_branch_task(self, task, task2, child1):
            child1.delegated = True
            child1.planning_state = PlanningState.finished
            task.insert_children(0, [child1])
            with pytest.raises(InvalidOperationError):
                task.add_dependency(task2)
            with pytest.raises(InvalidOperationError):
                task.remove_dependency(task2)

class TestStartEndDependencies(object):
    
    def test_start_dependencies(self, root_task):
        '''
        Like dependencies, but includes (start) dependencies of the parent
        '''
        task11 = root_task.children[0]
        task12 = root_task.children[1]
        task11.add_dependency(task12)
        assert tuple(root_task.start_dependencies) == ()
        assert tuple(task11.start_dependencies) == (task12,)
        assert tuple(task11.children[0].start_dependencies) == (task12,)
        assert tuple(task12.start_dependencies) == ()
            
    def test_end_dependencies(self, root_task, task, task2):
        '''
        end_deps = start dependencies + active children
        '''
        task11 = root_task.children[0]
        task111 = task11.children[0]
        task12 = root_task.children[1]
        
        # include active children, but not their deps (unless those are our active children)
        task111.add_dependency(task12)
        assert set(task111.end_dependencies) == {task12}
        assert set(task11.end_dependencies) == {task111}
        assert set(task12.end_dependencies) == set()
        assert set(root_task.end_dependencies) == {task11, task12}
        
        # leaf tasks always have the same start and end deps
        assert set(task111.start_dependencies) == set(task111.end_dependencies)
        assert set(task12.start_dependencies) == set(task12.end_dependencies)
        
        # also include regular dependencies
        def assert_():
            assert set(root_task.start_dependencies) == set()
            assert set(task11.start_dependencies) == {task}
            assert set(task111.start_dependencies) == {task, task12}
            assert set(task111.end_dependencies) == {task, task12}
            assert set(task11.end_dependencies) == {task, task111}
            assert set(task12.start_dependencies) == set()
            assert set(task12.end_dependencies) == set()
            assert set(root_task.end_dependencies) == {task11, task12}
        task11.add_dependency(task)
        assert_()
        
        # and ignore inactive children
        task11.insert_children(0, [task2])
        task2.planning_state = PlanningState.cancelled
        assert_()
        
    def test_show_non_active_dependencies(self, task, task2):
        '''
        Direct dependencies to a non-active task do show up
        '''
        task.add_dependency(task2)
        task2.planning_state = PlanningState.cancelled
        assert list(task.dependencies) == [task2]
        assert list(task.start_dependencies) == [task2]
        assert list(task.end_dependencies) == [task2] 
    
    def test_cannot_spend_effort_if_unfinished_end_dep(self, task, task2, interval1, interval2):
        '''
        When trying to spend effort on a task before its dependencies have finished, raise
        '''
        task.add_dependency(task2)
        
        with pytest.raises(InvalidOperationError) as ex:
            task.insert_effort_spent(0, [interval1])
        assert 'Cannot spend effort on task before its end_dependencies have finished' in str(ex.value)
        
        task2.insert_effort_spent(0, [interval2])
        task2.planning_state = PlanningState.finished
        task.insert_effort_spent(0, [interval1])
        
    def test_cannot_finish_if_unfinished_end_dep(self, task, task2, interval1, interval2):
        '''
        When trying to finish a task before its dependencies, raise
        '''
        task.add_dependency(task2)
        
        with pytest.raises(ValueError) as ex:
            task.planning_state = PlanningState.finished
        assert 'Cannot finish before end_dependencies have finished' in str(ex.value)
        
        task2.insert_effort_spent(0, [interval2])
        task2.planning_state = PlanningState.finished
        task.insert_effort_spent(0, [interval1])
        task.planning_state = PlanningState.finished
    
    class TestCannotUnfinishIfHasFinishedDepender(object):
        
        '''
        When a finished task depends on a (finished) task, any operation that
        may unfinish the depended task will raise
        
        Atomicity: After having caught the exception, the task tree is still
        valid; as if the offending call hadn't happened.
        '''
        
        @pytest.mark.parametrize('delegated', (True, False))
        def test_leaf(self, delegated, task, task2, interval1, interval2):
            '''
            When depending directly on leaf, raise when its planning state changes
            '''
            # setup
            task.add_dependency(task2)
            if delegated:
                task2.delegated = True
            else:
                task2.insert_effort_spent(0, [interval2])
            task2.planning_state = PlanningState.finished
            task.insert_effort_spent(0, [interval1])
            task.planning_state = PlanningState.finished
            
            # test
            ex = task2.validate_set_planning_state(PlanningState.planned)
            assert 'Cannot unfinish task as a finished task depends on it (perhaps indirectly)' in str(ex)
            with pytest.raises(ValueError) as ex2:
                task2.planning_state = PlanningState.planned
            assert ex2.value.args == ex.args
              
        def test_indirect_branch_child_insert(self, qt_object, interval1, interval2, interval3, task):
            '''
            When depending on branch, raise when it gains a descendant that
            causes branch to unfinish or when a descendant's leaf is assigned an
            unfinished planning state
            '''
            # setup
            t1 = Task('1', qt_object)
            t11 = Task('1.1', qt_object)
            t111 = Task('1.1.1', qt_object)
            t1111 = Task('1.1.1.1', qt_object)
            t12 = Task('1.2', qt_object)
            t1.insert_children(0, [t11, t12])
            t11.insert_children(0, [t111])
            t111.insert_children(0, [t1111])
            
            t12.add_dependency(t11)
            t1111.insert_effort_spent(0, [interval1])
            t1111.planning_state = PlanningState.finished
            t12.insert_effort_spent(0, [interval2])
            t12.planning_state = PlanningState.finished
            
            # raise on adding unfinished child to depended branch
            ex = t111.validate_insert_children(0, [task])
            assert 'Cannot insert unfinished task into finished branch which is depended on (perhaps indirectly) by a finished task' in str(ex)
            with pytest.raises(ValueError) as ex2:
                t111.insert_children(0, [task])
            assert ex2.value.args == ex.args
            
            # do allow inserting a finished child into a depended branch
            task.insert_effort_spent(0, [interval3])
            task.planning_state = PlanningState.finished
            assert t111.validate_insert_children(0, [task]) is None
            t111.insert_children(0, [task])
            
            # raise on unfinishing a descendant leaf task of the depended branch
            ex = t1111.validate_set_planning_state(PlanningState.planned)
            assert 'Cannot unfinish task as a finished task depends on it (perhaps indirectly)' in str(ex)
            with pytest.raises(ValueError) as ex2:
                t1111.planning_state = PlanningState.planned
            assert ex2.value.args == ex.args
            
        # Note: a finished leaf cannot become an (unfinished) branch without first becoming an unfinished leaf
                
# Note: in implementing, you want mixins to keep things separate in their own
# modules, it gets pretty complex already. You want to be able to think of
# things in isolation, i.e. in modules (not python modules).

# TODO

# The reparenting tasks and deps TODO above

# Time tracking: only a single task can be worked on at a time. All tasks should
# have access to a Context with an attrib for the currently tracked task, along
# with time at which the tracking started; this should be included by
# actual_effort as an additional effort-spent Interval(started, now). For now,
# do not set a timer to send out actual-effort changed events, just omit those
# events in this case.
#
# It shouldn't be set directly on the context, but on a Time tracking component,
# which is responsible for adding the effort spent interval when stopping.

# Instead of planned start/end on tasks, an optional deadline. No slack time yet.

# Take into actual effort: schedule a max duration of predicted_effort -
# actual_effort; if negative, schedule 30 min. Or rather, let predicted_effort
# always return those 30 additional min if original prediction was wrong.

# simple schedule(tasks_to_finish, work_intervals) -> {Task => [Interval]} func, does not include dependencies, does not reorder, schedules them simply

# schedule(tasks_to_finish, work_intervals) -> {Task => [Interval]}, produce intervals to spend effort, (can be multiple) for
# each task (e.g. a dict). context.schedules {name :: str => Schedule}
#
# Should recalculate every x time (not in some cases though, e.g. when not even
# in a work interval, or when already working on it, unless exceeding planned
# time). Qt prolly has a timer.
#
# Schedules have a unique name. The work hours ical's task names reference a
# schedule name in order to assign time to them.
#
# A task may not be part of multiple schedules, that would schedule it twice in
# the global calendar, thus giving a more pessimist view. Be careful with
# dependencies, a task entails more that it and its children, it's all the end
# dependencies and their indirect dependencies. Any change leading to a task
# being part of multiple schedules (also indirectly) must be disallowed. These
# tasks practically always are separate projects, but we won't make the
# distinction.
# -> context has schedules, make sure not to overlap tasks in schedules there 
#
#
# Making parallel tasks sequential when scheduling:
#
# Order should be deterministic, e.g. serialise by task id
# serialise them by their task id: the task id could be an id assigned to each
# task, a number, simply something unique that doesn't change as you change the
# task
#
# First order tasks by slack. Slack is relative to the deadline though (so don't
# add a Task.slack). First pick the deadline with the least slack if we were to
# direct all our effort to it. Then direct all effort to that deadline, ordering
# by slack relative to that deadline.
# (low prio, skip until other things are done)
#
# As the highest ordering override, allow overriding the default order on tasks
# with no dependency through drag and drop in a list or, ideally, calendar view.
# Implement as setting a fake start dependency on the task it should appear
# directly after, and adding a start dependency to it on the task that should
# come after it.
# As changes are made to tasks, this should be kept in order. The idea is to
# keep the task in between 2 other tasks, though some events perhaps may be
# responded to by forgetting this ordering override
#(low priority, skip until other is done, workaround by letting user add dependencies)

# A deadline overview, along with slack (like the milestone overview we planned).

# Milestones: describe what it is, the deliverable. Add/rm tasks to it that
# contribute to it. Optionally set a deadline for it, + show slack time. Also
# show the predicted delivery date on it.

# design of how we'd undo, save/load
'''
Set checkpoints. Can move to older checkpoints to undo, move to newer again to
redo. Creating a new checkpoint, deletes all checkpoints to the right of our
current point in history.

The checkpoints are snapshots. I.e. copies of the whole task tree. When
restoring, the views will need to reattach to a copy of a checkpoint. Any
registered listeners in the tree need to be intact when restored later, yet
changes in the current tree should not affect a checkpoint. These task signals
may be connected to views.

We will need code to save/load the task tree. When adding view state to that, we
already have a checkpoint-like undo system, granted we allow multiple saves.
So, how save/load?

pickle? Can't pickle any qt stuff. What if their internals change? Boom, broken.
Can pickle our stuff if we first separate out qt stuff (and replace qt signals with
Python event stuff). Even so, we'd need to be careful with any internal changes
to future garage-pm. Unless we fully detach into some format that we will not change,
e.g. dicts, near json. In which case we might as well pretty print dump json.

A save contains:
- raw task-tree data
- GUI state data

We then reconstruct the actual tree model, not by replaying, but by using custom
load() on each task state to restore listener configuration.
'''

# GUI todos
#
# when unable to unfinish due to depender, GUI will ask user whether to remove the offending deps. Removing the deps would rewrite history (planned start) though...