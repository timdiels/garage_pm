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

import pytest
from chicken_turtle_util.exceptions import InvalidOperationError
from garage_pm.domain import Task, Interval, EstimateType, PlanningState
from datetime import datetime, timedelta
from itertools import product

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
def root_task(context):
    task = context.root_task
    t1 = task.append_new_task('task1')
    t11 = task.append_new_task('task11')
    task.append_new_task('task2')
    t11.move(t1, 0)
    return task

@pytest.fixture
def task1(root_task):
    return root_task.children[0]

@pytest.fixture
def task11(task1):
    return task1.children[0]

@pytest.fixture
def task111(task11):
    task111 = task11.append_new_task('task111')
    task111.move(task11, 0)
    return task111

@pytest.fixture
def task112(task111):
    task112 = task111.append_new_task('task112')
    return task112

@pytest.fixture
def task2(root_task):
    return root_task.children[1]

@pytest.fixture
def dep_graph(context):
    return context.task_dependency_graph
    
class TestTaskTreeStructure(object):
    
    '''
    Test task creation, reparenting (move) and removal
    '''
    
    def test_default(self, context):
        assert context.root_task.children == ()
        
    def test_append_new_task(self, context):
        # When append on root task, inserts new task at the end
        root = context.root_task
        t1 = root.append_new_task('t1')
        t2 = root.append_new_task('t2')
        assert root.children == (t1, t2)
        
        # When append on any other task, inserts a new task after it
        t3 = t1.append_new_task()
        t4 = t2.append_new_task()
        assert root.children == (t1, t3, t2, t4)
        
    def test_move(self, context):
        root = context.root_task
        t1 = root.append_new_task()
        
        with pytest.raises(InvalidOperationError) as ex:
            root.move(t1, 0)
        assert 'Cannot move the root task' in str(ex.value)
        
        with pytest.raises(ValueError) as ex:
            t1.move(t1, 0)
        assert 'Cannot move task to itself' in str(ex.value)
        
        # Can move to current parent
        t2 = root.append_new_task()
        t1.move(root, 1)
        assert root.children == (t2, t1)
        t1.move(root, 0)
        assert root.children == (t1, t2)
        
        # Can move to new parent
        t11 = t1.append_new_task()
        t11.move(t1, 0)
        assert root.children == (t1, t2)
        assert t1.children == (t11,)
        
        #
        with pytest.raises(ValueError) as ex:
            t1.move(t11, 0)
        assert 'Cannot move task to one of its descendants' in str(ex.value)
        
        # Moving to other parent with non-zero index works fine too
        t11.move(root, 1)
        assert root.children == (t1, t11, t2)
        
    def test_dispose(self, root_task, task2, task1, task11):
        # when disposing a leaf, it is removed from the tree
        task2.dispose()
        assert root_task.children == (task1,)
        
        # when disposing a branch, the whole branch is disposed
        task1.dispose()
        assert root_task.children == ()

def test_is_leaf(root_task, task2):
    assert not root_task.is_leaf
    assert task2.is_leaf
    
def test_root_is_always_branch(context):
    '''Even with no children, the root task is a branch'''
    assert not context.root_task.is_leaf

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
    def test_default_value(self, task2, estimate_type):
        assert task2.effort_estimates[estimate_type] is None
    
    @pytest.mark.parametrize('estimate_type, value', product(EstimateType, (-1, 0)))
    def test_raise_on_set_invalid_value(self, task2, estimate_type, value):
        '''
        When setting negative or 0 effort, raise
        '''
        with pytest.raises(ValueError) as ex:
            task2.effort_estimates[estimate_type] = timedelta(minutes=value)
        assert 'estimate must be > timedelta(0)' in str(ex.value)
        
    @pytest.mark.parametrize('estimate_type', EstimateType)
    def test_set_none(self, task2, estimate_type):
        '''
        When setting None, set just fine
        '''
        task2.effort_estimates[estimate_type] = None
        
    def test_predicted(self, task2):
        '''
        Test simple case for predicted_effort
        '''
        assert task2.predicted_effort is None
        task2.effort_estimates[EstimateType.optimistic] = timedelta(days=6)
        assert task2.predicted_effort is None
        task2.effort_estimates[EstimateType.likely] = timedelta(hours=12)
        assert task2.predicted_effort is None
        task2.effort_estimates[EstimateType.pessimistic] = timedelta(minutes=18)
        assert task2.predicted_effort == timedelta(days=1, hours=8, minutes=3)
        
    def test_actual_effort(self, task2, interval1):
        '''
        Test simple case for actual effort
        '''
        assert task2.actual_effort == timedelta()
        task2.insert_effort_spent(0, [interval1])
        assert task2.actual_effort == interval1.duration
        
    class TestEvents(object):
        
        def test_effort_estimate_events(self, task2, mocker):
            one_day = timedelta(days=1)
            for estimate_type in EstimateType:
                estimate_changed = mocker.Mock()
                task2.effort_estimates.changed[estimate_type].connect(estimate_changed)
                
                task2.effort_estimates[estimate_type] = one_day
                estimate_changed.assert_called_with(task2)
                assert task2.effort_estimates[estimate_type] == one_day
                estimate_changed.reset_mock()
                
                task2.effort_estimates[estimate_type] = one_day
                estimate_changed.assert_not_called()
        
        def test_predicted_effort_changed_event(self, task2, mocker):
            predicted_changed = mocker.Mock()
            task2.events.predicted_effort_changed.connect(predicted_changed)
            
            for estimate_type in EstimateType:
                task2.effort_estimates[estimate_type] = timedelta(days=1)
            predicted_changed.assert_called_once_with(task2)
            assert task2.predicted_effort == timedelta(days=1)
            predicted_changed.reset_mock()
             
            task2.effort_estimates[EstimateType.optimistic] = None
            predicted_changed.assert_called_once_with(task2)
            assert task2.predicted_effort is None
            predicted_changed.reset_mock()
              
            task2.effort_estimates[EstimateType.likely] = None
            predicted_changed.assert_not_called()
                
        def test_actual_effort_changed_event(self, task2, interval1, mocker):
            actual_changed = mocker.Mock()
            task2.events.actual_effort_changed.connect(actual_changed)
            
            task2.insert_effort_spent(0, [interval1])
            actual_changed.assert_called_once_with(task2)
            assert task2.actual_effort == interval1.duration
            actual_changed.reset_mock()
        
    def test_cannot_move_task_to_effort_spent_task(self, task2, task11, interval1):
        '''
        When inserting in a leaf with actual_effort!=0, raise
        '''
        task2.insert_effort_spent(0, [interval1])
        with pytest.raises(InvalidOperationError) as ex:
            task11.move(task2, 0)
        assert 'Leaf task with effort spent on it cannot become a branch task' in str(ex.value)
        
class TestDelegated(object):
    
    def test_leaf(self, task2, task11, interval1):
        # effort task is not delegated
        assert not task2.delegated
        
        # switch to delegated
        task2.delegated = True
        assert task2.delegated
        
        # delegated task cannot have children
        with pytest.raises(InvalidOperationError):
            task11.move(task2, task11)
            
        # duration
        assert task2.duration is None
        task2.duration = timedelta(days=1)
        assert task2.duration == timedelta(days=1)
            
        # switching back to effort task
        task2.delegated = False
        assert task2.actual_effort == timedelta()  # is an effort task again
        
        # cannot delegate task with effort spent
        task2.insert_effort_spent(0, [interval1])
        with pytest.raises(ValueError):
            task2.delegated = True
        
    def test_branch(self, task1):
        '''
        Branch cannot be delegated
        '''
        assert not task1.delegated
        with pytest.raises(ValueError):
            task1.delegated = True
            
class TestPlanningState(object):
    
    '''
    Test planning state on any kind of task
    '''
    
    @pytest.fixture
    def planning_state_changed(self, task2, mocker):
        planning_state_changed = mocker.Mock()
        task2.events.planning_state_changed.connect(planning_state_changed)
        return planning_state_changed
        
    def test_effort_task(self, task2, interval1):
        '''
        Test happy days default, setting and getting
        '''
        assert task2.planning_state == PlanningState.planned
        for planning_state in PlanningState:
            # may enter any planning_state except finished by default
            if planning_state != PlanningState.finished:
                task2.planning_state = planning_state
                assert task2.planning_state == planning_state
        
        # cannot finish without effort
        with pytest.raises(ValueError) as ex:
            task2.planning_state = PlanningState.finished
        assert 'Cannot finish a task effortlessly' in str(ex.value)
        
        # can finish with effort
        task2.insert_effort_spent(0, [interval1])
        task2.planning_state = PlanningState.finished
    
    def test_delegated_task(self, task2):
        '''
        Test happy days default, setting and getting
        '''
        assert task2.planning_state == PlanningState.planned
        task2.delegated = True
        for planning_state in PlanningState:
            task2.planning_state = planning_state
            assert task2.planning_state == planning_state
                
    @pytest.mark.parametrize('delegated', (True,False))
    def test_leaf_change_event(self, task2, delegated, planning_state_changed):
        '''
        When planning state changes, emit event
        '''
        task2.delegated = delegated
        
        task2.planning_state = PlanningState.not_planned
        planning_state_changed.assert_called_once_with(task2)
        assert task2.planning_state == PlanningState.not_planned
        planning_state_changed.reset_mock()
        
        task2.planning_state = PlanningState.not_planned
        planning_state_changed.assert_not_called()
        
    def test_branch(self, task11, task111, task112, planning_state_changed):
        '''
        Branch tasks are planned if any child is planned, else they are finished
        '''
        task111.delegated = True  # to be able to set finished
        task112.delegated = True
        
        # A branch task may not have its planning_state set
        for planning_state in PlanningState:
            with pytest.raises(InvalidOperationError) as ex:
                task11.planning_state = planning_state
            assert "A branch task's state is derived from its child tasks, not set" in str(ex.value)

        # If any child is planned, so is the parent
        task111.planning_state = PlanningState.planned
        for planning_state in PlanningState:
            task112.planning_state = planning_state
            assert task11.planning_state == PlanningState.planned
            
        # If no child is planned, the parent is finished
        for planning_state1 in PlanningState:
            if planning_state1 == PlanningState.planned:
                continue
            task111.planning_state = planning_state1
            for planning_state2 in PlanningState:
                if planning_state2 == PlanningState.planned:
                    continue
                task112.planning_state = planning_state
                assert task11.planning_state == PlanningState.finished
                
    def test_branch_change_event(self, task2, task111, task112, planning_state_changed):
        '''
        Test branch planning state change events
        
        Also test planning state changes due to branch <--> effort transitions 
        '''
        # task switches from planned to finished as the added child is not planned
        task111.planning_state = PlanningState.cancelled
        task111.move(task2, 0)
        planning_state_changed.assert_called_once_with(task2)
        assert task2.planning_state == PlanningState.finished
        planning_state_changed.reset_mock()
        
        # task switches from finished to planned as we add a planned child
        task112.move(task2, 0)
        planning_state_changed.assert_called_once_with(task2)
        assert task2.planning_state == PlanningState.planned
        planning_state_changed.reset_mock()
        
        # task switches from planned to finished as child2 changes to cancelled
        task112.planning_state = PlanningState.cancelled
        planning_state_changed.assert_called_once_with(task2)
        assert task2.planning_state == PlanningState.finished
        planning_state_changed.reset_mock()
        
        # removing all the children, we become a planned effort task (finished would be wrong as there is no effort spent)
        task111.dispose()
        task112.dispose()
        planning_state_changed.assert_called_once_with(task2)
        assert task2.planning_state == PlanningState.planned
        planning_state_changed.reset_mock()
        
    def test_effort_delegated_switch(self, task2):
        '''
        When switching between delegated and effort task, maintain planning state
        '''
        for planning_state in PlanningState:
            if planning_state == PlanningState.finished:
                continue
            task2.planning_state = planning_state
            task2.delegated = True
            assert task2.planning_state == planning_state
            task2.delegated = False
            assert task2.planning_state == planning_state
        
    class TestFinishedIsFairlyImmutable(object):
        
        '''
        When a task is finished it should generally not be edited without first
        'reopening' it
        
        Name, description and children can still be edited though.
        '''
        
        def test_effort_task(self, task2, interval1):
            task2.insert_effort_spent(0, [interval1])
            task2.planning_state = PlanningState.finished
            with pytest.raises(InvalidOperationError):
                task2.effort_estimates[EstimateType.likely] = None
            with pytest.raises(InvalidOperationError):
                task2.insert_effort_spent(0, [interval1])
            with pytest.raises(InvalidOperationError):
                task2.remove_effort_spent(0, 1)
            with pytest.raises(InvalidOperationError):
                task2.delegated = True
                
        def test_delegated_task(self, task2):
            task2.delegated = True
            task2.planning_state = PlanningState.finished
            with pytest.raises(InvalidOperationError):
                task2.duration = timedelta(days=1)
            with pytest.raises(InvalidOperationError):
                task2.delegated = False
                
def test_is_active(task2, interval1):
    task2.insert_effort_spent(0, [interval1])
    assert task2.is_active
    task2.planning_state = PlanningState.finished
    assert task2.is_active
    task2.planning_state = PlanningState.cancelled
    assert not task2.is_active
    task2.planning_state = PlanningState.not_planned
    assert not task2.is_active

class TestDependencies(object):
    
    '''
    Test task dependencies
    
    A task can only be started when its start dependencies have finished. A task
    can only finish when its end dependencies have finished.
    
    Lingo: structural dependencies: the ones introduced by test_structure
    '''
    
    def test_structure(self, dep_graph, root_task, task1, task11, task2):
        '''
        Test dependencies originating from the task tree structure:
        
        - parent end node depends on each child end node
        - child start node depends on parent start node
        - leaf end node depends on leaf start node
        '''
        task11.delegated = True  # easier to set finished later
        
        # Check root_task for above mentioned properties
        def assert_structure():
            assert not dep_graph[root_task.start_node]
            assert dep_graph[task1.start_node] == {root_task.start_node: {'active': True}}
            assert dep_graph[task11.start_node] == {task1.start_node: {'active': True}}
            assert dep_graph[task11.end_node] == {task11.start_node: {'active': True}}
            assert dep_graph[task1.end_node] == {task11.end_node: {'active': True}}
            assert dep_graph[task2.start_node] == {root_task.start_node: {'active': True}}
            assert dep_graph[task2.end_node] == {task2.start_node: {'active': True}}
            assert dep_graph[root_task.end_node] == {task1.end_node: {'active': True}, task2.end_node: {'active': True}}
        assert_structure()
        
        # When setting a task inactive, parent-start <-- child-start is marked inactive
        task11.planning_state = PlanningState.cancelled
        assert dep_graph[task1.end_node] == {task11.end_node: {'active': False}}
        
        # When making it active again, parent-start <-- child-start is marked active (deps are marked active by default)
        task11.planning_state = PlanningState.finished
        assert_structure()  # back to what it originally was
        
        # When start depending on the end of a non-active non-child, the edge is
        # remains marked active. Edge activity implies whether the dependency is
        # active, not whether its attached task is active. Inactive edges will be
        # ignored by the scheduler (but not by dependency cycle detection).
        task11.planning_state = PlanningState.cancelled
        task2.add_dependency(task11)
        assert dep_graph[task2.start_node] == {task11.end_node: {'active': True}, root_task.start_node: {'active': True}}
        
    def test_dispose(self, dep_graph, task1, task11):
        '''
        When task is disposed, it is also removed from the dependency graph
        '''
        task1.dispose()
        assert task1.start_node not in dep_graph
        assert task1.end_node not in dep_graph
        assert task11.start_node not in dep_graph
        assert task11.end_node not in dep_graph
        
    class TestAddRemoveStartDependency(object):
        
        '''
        Test add_start_dependency, remove_start_dependency
        '''
        
        def test_basics(self, dep_graph, root_task, task1, task2):
            task1_start_deps = dep_graph[task1.start_node].copy()
            task1_end_deps = dep_graph[task1.end_node].copy()
            task2_start_deps = dep_graph[task2.start_node].copy()
            task2_end_deps = dep_graph[task2.end_node].copy()
            
            # Additional dependencies can be added from your start node to end nodes of other tasks
            task2.start_node
            task1.add_dependency(task2)
            assert dep_graph[task1.start_node] == {task2.end_node: {'active': True}, root_task.start_node: {'active': True}}
            assert dep_graph[task1.end_node] == task1_end_deps
            assert dep_graph[task2.start_node] == task2_start_deps
            assert dep_graph[task2.end_node] == task2_end_deps
            
            # They can also be removed again
            task1.remove_dependency(task2)
            assert dep_graph[task1.start_node] == task1_start_deps
            assert dep_graph[task1.end_node] == task1_end_deps
            assert dep_graph[task2.start_node] == task2_start_deps
            assert dep_graph[task2.end_node] == task2_end_deps
            
        # Note: add/remove_start_dependency cannot add remove structural
        # dependencies as it only adds start-->end deps, which aren't
        # structural.
        
        def test_ignore_add_existing(self, dep_graph, root_task, task1, task2):
            '''
            When the dependency corresponding to add_dependency already exists, ignore the call
            '''
            task1.add_dependency(task2)
            task1.add_dependency(task2)
            assert dep_graph[task1.start_node] == {task2.end_node: {'active': True}, root_task.start_node: {'active': True}}

        class TestCannotMutateIfFinished(object):
            
            def test_effort_task(self, task1, task2, interval1):
                task2.insert_effort_spent(0, [interval1])
                task2.planning_state = PlanningState.finished
                with pytest.raises(InvalidOperationError):
                    task2.add_dependency(task1)
                with pytest.raises(InvalidOperationError):
                    task2.remove_dependency(task1)
                    
            def test_delegated_task(self, task1, task2):
                task2.delegated = True
                task2.planning_state = PlanningState.finished
                with pytest.raises(InvalidOperationError):
                    task2.add_dependency(task1)
                with pytest.raises(InvalidOperationError):
                    task2.remove_dependency(task1)
                
            def test_branch_task(self, task1, task11, task2):
                task11.delegated = True
                task11.planning_state = PlanningState.finished
                with pytest.raises(InvalidOperationError):
                    task1.add_dependency(task2)
                with pytest.raises(InvalidOperationError):
                    task1.remove_dependency(task2)
            
    class TestCircularDependencies(object):
        
        '''
        If an operation would create a dependency cycle, raise
        
        Dependencies on inactive children need to be included in the search for
        cycles.
        '''
        
        _states = (
            PlanningState.planned,  # active 
            PlanningState.cancelled  # non-active
        )
        
        def test_self_cycle(self, task2):
            with pytest.raises(ValueError) as ex:
                task2.add_dependency(task2)
            assert "Depending on 'task2' would cause a dependency cycle: " in str(ex.value)  # t2.s -> t2.e -> t2.s
            
        def test_simple_leafs(self, task111, task112):
            task111.add_dependency(task112)
            with pytest.raises(ValueError) as ex:
                task112.add_dependency(task111)
            assert "Depending on 'task111' would cause a dependency cycle: " in str(ex.value)  # t111.s -> t112.e -> t112.s -> t111.e -> t111.s
        
        @pytest.mark.parametrize('planning_state', _states)    
        def test_via_descendant(self, root_task, task1, task11, task111, planning_state):
            task11.append_new_task()  # make task1 planned so that we can modify its dependencies
            task111.planning_state = planning_state
            with pytest.raises(ValueError) as ex:
                task1.add_dependency(task111)
            assert "Depending on 'task111' would cause a dependency cycle: " in str(ex.value)  # t111.s -> t11.s -> t1.s -> t111.e -> t111.s
            
            # test same conflict by moving a task
            task111.move(root_task, -1)
            task1.add_dependency(task111)
            with pytest.raises(ValueError) as ex:
                task111.move(task11, 0)
            assert "Moving to 'task11' would cause a dependency cycle: " in str(ex.value)
        
        @pytest.mark.parametrize('planning_state', _states)
        def test_via_ancestor(self, root_task, task1, task11, task111, planning_state):
            task111.planning_state = planning_state
            with pytest.raises(ValueError) as ex:
                task111.add_dependency(task1)
            assert "Depending on 'task1' would cause a dependency cycle: " in str(ex.value)  # t111.s -> t1.e -> t11.e -> t111.e -> t111.s
            
            # test same conflict by moving a task
            task111.move(root_task, -1)
            task111.add_dependency(task1)
            with pytest.raises(ValueError) as ex:
                task111.move(task11, 0)
            assert "Moving to 'task11' would cause a dependency cycle: " in str(ex.value)
                
        @pytest.mark.parametrize('planning_state', _states)
        def test_branch_and_leaf(self, root_task, task1, task11, task111, task2, planning_state):
            task111.planning_state = planning_state
            task2.add_dependency(task1)
            with pytest.raises(ValueError) as ex:
                task111.add_dependency(task2)
            assert "Depending on 'task2' would cause a dependency cycle: " in str(ex.value)  # t111.s -> t2.e -> t2.s -> t1.e -> t11.e -> t111.e -> t111.s
            
            # test same conflict by moving a task
            task111.move(root_task, -1)
            task111.add_dependency(task2)
            with pytest.raises(ValueError) as ex:
                task111.move(task11, 0)
            assert "Moving to 'task11' would cause a dependency cycle: " in str(ex.value)
        
        @pytest.mark.parametrize('planning_state', _states)
        def test_2_branches(self, root_task, task1, task11, task111, task2, planning_state):
            task111.planning_state = planning_state
            task2.add_dependency(task1)
            task21 = task2.append_new_task()
            task21.name = 'task21'
            task21.move(task2, 0)
            with pytest.raises(ValueError) as ex:
                task111.add_dependency(task21)
            assert "Depending on 'task21' would cause a dependency cycle: " in str(ex.value)  # t2.s -> t1.e -> t11.e -> t111.e -> t111.s -> t21.e -> t21.s -> t2.s
            
            # test same conflict by moving a task
            task111.move(root_task, -1)
            task111.add_dependency(task21)
            with pytest.raises(ValueError) as ex:
                task111.move(task11, 0)
            assert "Moving to 'task11' would cause a dependency cycle: " in str(ex.value)
        
    def test_cannot_finish_if_unfinished_deps(self, task1, task111, task2, interval1):
        '''
        When trying to finish a task before its start node's dependencies, raise
        '''
        task1.add_dependency(task2)
        task111.delegated = True
        
        with pytest.raises(ValueError) as ex:
            task111.planning_state = PlanningState.finished
        assert 'Cannot finish before end_dependencies have finished' in str(ex.value)
        
        task2.insert_effort_spent(0, [interval1])
        task2.planning_state = PlanningState.finished
        task111.planning_state = PlanningState.finished
    
    class TestCannotUnfinishIfHasFinishedDepender(object):
        
        '''
        When a (finished) task is depended on by a finished task, any operation
        that would unfinish the depended task will raise.
        
        Atomicity: After having caught the exception, the task tree is still
        valid; as if the offending call hadn't happened.
        '''
        
        @pytest.mark.parametrize('delegated', (True, False))
        def test_leaf(self, delegated, task111, task112, interval1, interval2):
            '''
            When depending directly on leaf, raise when its planning state changes
            '''
            # setup
            task111.add_dependency(task112)
            if delegated:
                task112.delegated = True
            else:
                task112.insert_effort_spent(0, [interval2])
            task112.planning_state = PlanningState.finished
            task111.insert_effort_spent(0, [interval1])
            task111.planning_state = PlanningState.finished
            
            # test
            for planning_state in PlanningState:
                if planning_state == PlanningState.finished:
                    continue
                ex = task112.validate_set_planning_state(PlanningState.planned)
                assert 'Cannot set task planned as a finished task depends on it (perhaps indirectly)' in str(ex)
                with pytest.raises(ValueError) as ex2:
                    task112.planning_state = PlanningState.planned
                assert ex2.value.args == ex.args
              
        def test_indirect_branch_child_insert(self, root_task, task1, task11, task111, task2, interval1, interval2, interval3):
            '''
            When depending on branch, raise only when it gains a planned
            descendant or when a descendant leaf becomes planned
            '''
            # setup
            task2.add_dependency(task1)
            task111.insert_effort_spent(0, [interval1])
            task111.planning_state = PlanningState.finished
            task2.insert_effort_spent(0, [interval2])
            task2.planning_state = PlanningState.finished
            
            # raise on adding planned child to depended branch
            with pytest.raises(InvalidOperationError) as ex:
                task111.append_new_task()
            assert 'Cannot insert planned task into finished branch which is depended on (perhaps indirectly) by a finished task' in str(ex.value)
            
            # raise on adding via moving
            task112 = task1.append_new_task()
            with pytest.raises(ValueError) as ex:
                task112.move(task11, -1)
            assert 'Cannot insert planned task into finished branch which is depended on (perhaps indirectly) by a finished task' in str(ex.value)
            
            # do allow inserting a child of any other state into a depended branch
            task112.delegated = True
            for planning_state in PlanningState:
                if planning_state == PlanningState.planned:
                    continue
                task112.planning_state = planning_state
                task112.move(task11, 0)
                task112.move(root_task, 0)  # cleanup
            
            # raise on setting a descendant task of the depended branch to planned
            ex = task111.validate_set_planning_state(PlanningState.planned)
            assert 'Cannot set task planned as a finished task depends on it (perhaps indirectly)' in str(ex)
            with pytest.raises(ValueError) as ex2:
                task111.planning_state = PlanningState.planned
            assert ex2.value.args == ex.args
            
            # do allow setting it to anything else
            for planning_state in PlanningState:
                if planning_state == PlanningState.planned:
                    continue
                assert task111.validate_set_planning_state(planning_state) is None
                task111.planning_state = planning_state
            
        
# TODO

# Tests updated to match redesign, simply run and implement!


# Time tracking: only a single task can be worked on at a time. All tasks should
# have access to a Context with an attrib for the currently tracked task, along
# with time at which the tracking started; this should be included by
# actual_effort as an additional effort-spent Interval(started, now). For now,
# do not set a timer to send out actual-effort changed events, just omit those
# events in this case.
#
# It shouldn't be set directly on the context, but on a Time tracking component,
# which is responsible for adding the effort spent interval when stopping.
#
# TODO When spend effort on task, dispose it, spending the same effort elsewhere should be allowed (i.e. no raise due to nonexistant overlap) 

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

# TODO Go round updating raises section on the domain classes 