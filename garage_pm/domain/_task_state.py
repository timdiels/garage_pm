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
from ._common import PlanningState, TaskNodeType, DependencyCycleError
from ._task import Task
import networkx as nx

class _Events(QObject):
    
    name_changed = pyqtSignal(Task)
    description_changed = pyqtSignal(Task)
    planning_state_changed = pyqtSignal(Task)
    set_planning_state_validity_changed = pyqtSignal([Task, PlanningState])
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self._task = task
        
    def __getattr__(self, attr):
        return getattr(self._task._state._events, attr)

class TaskStateData(object):
    
    def __init__(self, name, task, context, is_root):
        self.context = context
        self.events = _Events(task, context.qt_parent)
        self.task = task
        self.name = name
        self.description = ''
        self.parent = None
        if is_root:
            self.planning_state = PlanningState.finished
        else:
            self.planning_state = PlanningState.planned
        self.is_root = is_root

class TaskState(object):
    
    def __init__(self, task_state_data):
        self._common = task_state_data
        self._events = QObject(self._context.qt_parent)
    
    @property
    def _is_root(self):
        return self._common.is_root
    
    @property
    def _dependency_graph(self):
        return self._common.context.task_dependency_graph
    
    @property
    def _task(self):
        return self._common.task
    
    @property
    def _context(self):
        return self._common.context
    
    @property
    def _planning_state(self):
        return self._common.planning_state
    
    @_planning_state.setter
    def _planning_state(self, value):
        self._common.planning_state = value
        
    @property
    def _parent(self):
        return self._common.parent
    
    @_parent.setter
    def _parent(self, value):
        self._common.parent = value
    
    @property
    def start_node(self):
        '''
        Returns
        -------
        (self :: Task, TaskNodeType)
        '''
        return (self._task, TaskNodeType.start)
    
    @property
    def end_node(self):
        '''
        Returns
        -------
        (self :: Task, TaskNodeType)
        '''
        return (self._task, TaskNodeType.end)
    
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
            self.events.name_changed.emit(self._task)
            
    @property
    def description(self):
        return self._common.description
    
    @description.setter
    def description(self, value):
        if self._common.description != value:
            self._common.description = value
            self.events.description_changed.emit(self._task)
        
    @property
    def is_active(self):
        return self.planning_state in (PlanningState.planned, PlanningState.finished)
    
    @property
    def parent(self):
        return self._parent
    
    def append_new_task(self, name='Task'):
        '''
        Insert new task after current.
        
        If current task is the root task, insert new child at the bottom instead.
        
        Returns
        -------
        Task
            The new task
        '''
        task = Task(name, self._context)
        try:
            try:
                if self._is_root:
                    self._insert_child(len(self.children), task)
                else:
                    self.parent._insert_child(self.parent.children.index(self._task)+1, task)
                return task
            except ValueError as ex:
                raise InvalidOperationError(*ex.args)
        except Exception:
            task.dispose()
            raise
    
    def move(self, parent, index):
        '''
        Move task from current parent to new one and insert at given index
        
        Parameters
        ----------
        parent : Task
            Parent to move to, the new parent
        index : int
            Index at which to insert task as child under `new_parent`, after it has
            been removed from the current parent (the latter is important when
            moving to the same parent).
        '''
        if self._is_root:
            raise InvalidOperationError('Cannot move the root task')
        if parent is self._task:
            raise ValueError('Cannot move task to itself')
        if self._task in parent.ancestors:
            raise ValueError('Cannot move task to one of its descendants')
        
        # Try move (if it fails, some events may have been emitted, but none will have shown an invalid state)
        old_parent = self.parent
        old_index = self.parent.children.index(self._task)
        self.parent._remove_child(self._task)
        try:
            try:
                parent._insert_child(index, self._task)
            except DependencyCycleError as ex:
                cycles = ex.args[0]
                raise ValueError("Moving to '{}' would cause a dependency cycle: {}".format(parent.name, cycles))
        except Exception:
            old_parent._insert_child(old_index, self._task)  # rollback
            raise
    
    def dispose(self):
        '''
        Remove task from the task tree.
        
        If the task has children, they are disposed as well.
        
        Once disposed, a task should no longer be used.
        '''
        if self._is_root:
            raise InvalidOperationError('Cannot dispose the root task')
        
        # dispose children
        for child in self.children:
            child.dispose()
            
        # remove from parent
        if self.parent:
            self.parent._remove_child(self._task)
        
        # remove from dep graph
        self._dependency_graph.remove_nodes_from([self.start_node, self.end_node])
    
    def _insert_child(self, index, child):
        '''
        Raises
        ------
        ValueError
            Only when inserting a planned task into a branch depended on by a finished task
        DependencyCycleError
            When insertion would cause a cycle in dependency graph
        '''
        raise NotImplementedError()
    
    def _validate_insert_child(self, index, child): #TODO maybe keep as priv, make public variant for validate_move and validate_append_new_task
        '''
        Get whether may call _insert_child with given args
        
        Returns
        -------
        Exception or None
            the exception that would be thrown if called with these args,
            ``None`` otherwise. However, `DependencyCycleError`\ s may still be
            thrown
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
        return iter(self._dependencies)
    
    def add_dependency(self, task):
        if self.planning_state == PlanningState.finished:
            raise InvalidOperationError('Cannot add dependency to finished task')
        self._dependency_graph.add_edge(self.start_node, task.end_node, {'active': True})
        
        cycles = self._dependency_cycles
        if cycles:
            # rollback
            self.remove_dependency(task)
            raise ValueError("Depending on '{}' would cause a dependency cycle: {}".format(task.name, cycles))
        
    def remove_dependency(self, task):
        if self.planning_state == PlanningState.finished:
            raise InvalidOperationError('Cannot remove dependency from finished task')
        self._dependency_graph.remove_edge(self.start_node, task.end_node)
        
    @property
    def _dependency_cycles(self):
        cycles = list(nx.simple_cycles(self._dependency_graph))
        if cycles:
            cycles = ', '.join(' -> '.join('{}.{}'.format(task.name, node_type.value) for (task, node_type) in cycle) for cycle in cycles)
            return cycles
        else:
            return None
    
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
    def _has_unfinished_dependencies(self):
        for task, node_type in self._dependency_graph[self.start_node]:
            if node_type == TaskNodeType.start:
                if task._has_unfinished_dependencies:
                    return True
            else:
                assert node_type == TaskNodeType.end
                if task.planning_state != PlanningState.finished:
                    return True
        return False

    @property
    def _has_finished_depender(self):
        '''
        Get whether has a finished task whose start depends on our end
        '''
        for (task, node_type), _ in self._dependency_graph.in_edges_iter(self.end_node):
            if node_type == TaskNodeType.start:
                if task.planning_state == PlanningState.finished:
                    return True
            else:
                assert node_type == TaskNodeType.end
                assert task is self.parent
                if task._has_finished_depender:
                    return True
        return False
    
    def _get_delegated(self):
        return False
    
    def _set_delegated(self, value):
        ex = self.validate_set_delegated(value)
        if ex:
            raise ex
        if self.delegated != value:
            if value:
                self._task._become_delegated_task()
            else:
                self._task._become_effort_task()
                
    def validate_set_delegated(self, delegated):
        '''
        Get whether may set delegated to given value
        
        Parameters
        ----------
        delegated : bool
        
        Returns
        -------
        Exception or None
            the exception that would be thrown if called with these args,
            ``None`` otherwise
        '''
        if self.planning_state == PlanningState.finished:
            return InvalidOperationError('Cannot change whether a is delegated when it is already finished')
    
    delegated = property(
        fget=lambda self: self._get_delegated(), 
        fset=lambda self, value: self._set_delegated(value),
        doc='''
        Whether the task is delegated to someone else
        '''
    )
    