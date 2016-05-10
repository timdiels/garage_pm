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
from garage_pm.domain import Task, Interval, EstimateType, PlanningState
from garage_pm.domain._branch_task_state import BranchTaskState
from datetime import datetime, timedelta
from itertools import product

@pytest.fixture
def qt_object():
    return QObject()

class TestTask(object):
    
    @pytest.fixture
    def task(self, qt_object):
        return Task('task1', qt_object)
    
    @pytest.fixture
    def task2(self, qt_object):
        return Task('task2', qt_object)
        
    @pytest.fixture
    def child1(self, task, qt_object):
        return Task('child1', qt_object)
        
    @pytest.fixture
    def child2(self, task, qt_object):
        return Task('child2', qt_object)
    
    @pytest.fixture
    def child3(self, task, qt_object):
        return Task('child3', qt_object)
    
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
    
    @pytest.fixture
    def root_task(self, qt_object):
        t1 = Task('1', qt_object)
        t11 = Task('1.1', qt_object)
        t111 = Task('1.1.1', qt_object)
        t12 = Task('1.2', qt_object)
        t1.insert_children(0, [t11, t12])
        t11.insert_children(0, [t111])
        return t1
        
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
            assert 'Leaf task with effort spent on it cannot become a branch task' in str(ex.value)
            
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
            assert task.planning_state == PlanningState.planned
            for planning_state in PlanningState:
                # may enter any planning_state except finished by default
                if planning_state != PlanningState.finished:
                    task.planning_state = planning_state
                    assert task.planning_state == planning_state
            
        def test_cannot_set_leaf_finished(self, task, interval1):
            '''
            Cannot finish leaf when actual_effort==0
            '''
            with pytest.raises(ValueError) as ex:
                task.planning_state = PlanningState.finished
            assert 'Cannot finish a task effortlessly' in str(ex.value)
            
            # but can finish with effort
            task.insert_effort_spent(0, [interval1])
            task.planning_state = PlanningState.finished
            
        def test_branch(self, task, child1, child2, interval1):
            '''
            Branch tasks take upon the highest priority state of their children
            
            Not to be confused with task priorities (if we decided to implement that)
            
            priorities: planned > not planned > cancelled > finished
            '''
            task.insert_children(0, [child1, child2])
            child1.insert_effort_spent(0, [interval1])
            child2.insert_effort_spent(0, [interval1])
            
            # A branch task may not have its planning_state set
            for planning_state in PlanningState: 
                with pytest.raises(ValueError) as ex:
                    task.planning_state = planning_state
                assert "A branch task's state is derived from its child tasks, not set" in str(ex.value)

            # Parent state is that of the highest 'priority' child state
            priorities = BranchTaskState._planning_state_priorities
            for i in range(len(priorities)):
                child1.planning_state = priorities[i]
                for planning_state in priorities[i:]:
                    child2.planning_state = planning_state
                    assert task.planning_state == priorities[i]
                    
    def test_is_active(self, task, interval1):
        task.insert_effort_spent(0, [interval1])
        assert task.is_active
        task.planning_state = PlanningState.finished
        assert task.is_active
        task.planning_state = PlanningState.cancelled
        assert not task.is_active
        task.planning_state = PlanningState.not_planned
        assert not task.is_active

        #TODO rm
#     class TestBranchEffort(object):
#         
#         @pytest.fixture(params=(PlanningState.not_planned, PlanningState.cancelled))
#         def branch(self, request, qt_object, child1, child2, child3, interval1, interval2, interval3):
#             branch = Task('branch', qt_object)
#             branch.insert_children(0, [child1, child2, child3])
#             child1.insert_effort_spent(0, [interval1])
#             child2.insert_effort_spent(0, [interval2])
#             child3.insert_effort_spent(0, [interval3])
#             child3.planning_state = request.param  # make inactive
#             return branch
#             
#         @pytest.mark.parametrize('estimate_type', EstimateType)
#         def test_raise_on_set(self, branch, estimate_type):
#             with pytest.raises(ValueError) as ex:
#                 branch.effort_estimates[estimate_type] = timedelta(1)
#             assert 'May not set effort estimate on branch task' in str(ex.value)
#         
#         @pytest.mark.parametrize('estimate_type', EstimateType)    
#         def test_get_estimate(self, branch, estimate_type):
#             '''
#             When get estimate, take sum of active children
#             '''
#             for i, child in enumerate(branch.children): 
#                 child.effort_estimates[estimate_type] = timedelta(days=i+1)
#             assert branch.effort_estimates[estimate_type] == timedelta(days=1+2)
#         
#         def test_get_actual_effort(self, branch, child1, child2):
#             '''
#             When get actual_effort, take sum of active children
#             '''
#             assert branch.actual_effort == child1.actual_effort + child2.actual_effort
#             
#         def test_get_predicted_effort(self, branch):
#             '''
#             When get predicted_effort, take sum of active children; if either is None, so is parent
#             '''
#             for estimate_type in EstimateType:
#                 assert branch.predicted_effort is None  # when a child has None as predicted_effort, so has parent
#                 for i, child in enumerate(branch.children): 
#                     child.effort_estimates[estimate_type] = timedelta(days=i+1)
#             assert branch.predicted_effort == timedelta(days=1+2)
#             
#             # unactive children with predicted_effort=None do not affect parent
#             branch.children[-1].effort_estimates[EstimateType.likely] = None
#             assert branch.predicted_effort is not None
        
    def test_ancestors(self, root_task):
        assert tuple(root_task.ancestors) == ()
        for child in root_task.children:
            assert tuple(child.ancestors) == (root_task,)
            for grandchild in child.children:
                assert tuple(grandchild.ancestors) == (root_task, child)
    
    def test_descendants(self, root_task):
        assert tuple(root_task.descendants) == (root_task.children[0], root_task.children[0].children[0], root_task.children[1])
        assert tuple(root_task.children[0].descendants) == (root_task.children[0].children[0],)
        assert tuple(root_task.children[0].children[0].descendants) == ()
        assert tuple(root_task.children[1].descendants) == ()
    
    class TestDependencies(object):
        
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
            
        def test_ignore_add_dep_descendant(self, root_task):
            '''
            When adding descendant of a task we already depend on, ignore it
            '''
            root_task.children[1].add_dependency(root_task.children[0])
            root_task.children[1].add_dependency(root_task.children[0].children[0])
            assert tuple(root_task.children[1].dependencies) == (root_task.children[0],)
            
        # Note: adding a dependency of a dependency is not necessarily ignored
        # Note: adding dependencies of the parent aren't necessarily ignored either
            
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
        
        
    def test_direct_non_active(self, task, task2):
        '''
        Direct dependencies to a non-active task do show up
        '''
        task.add_dependency(task2)
        task2.planning_state = PlanningState.cancelled
        assert list(task.dependencies) == [task2]
        assert list(task.start_dependencies) == [task2]
        assert list(task.end_dependencies) == [task2] 
                
# Note: in implementing, you want mixins to keep things separate in their own
# modules, it gets pretty complex already. You want to be able to think of
# things in isolation, i.e. in modules (not python modules).

# TODO

# Make deps, children, planning_state combos solid
#
#
# TODO cannot finish if an end dep is planned (active and not finished).
# TODO cannot add deps on finished task.
# TODO cannot change estimates on finished task.
#
# TODO cannot unfinish (e.g. branch tasks do) if a finished task depends on it (indirectly).
#
# What happens when tasks are reparented? What if adding a new task to a
# finished branch? Just more events that could affect the planning_state of a branch,
# possibly causing a raise.
#
# Check for it up front using a dep graph, and raise? Or add a rollback system.
# Or simply allow breaking the domain. Checking in 3 places should do the trick,
# so far. Those that raise are insert_children and set-planning_state. For the check the
# dependency should be found, which may be indirect, so maybe we do want to
# construct an actual dep graph with networkx
#
# UI will ask user whether to remove the offending deps. Removing the deps would rewrite history (planned start) though...

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





