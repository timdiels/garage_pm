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
from garage_pm.domain import Task, Interval
from datetime import datetime, timedelta

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
    def interval(self):
        return Interval(datetime.now(), datetime.now() + timedelta(minutes=1))
        
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
            
        def test_raise_on_becoming_invalid_non_leaf(self, task, interval, child1):
            '''
            When inserting in a leaf with actual_effort!=0, raise
            
            Note: test overlaps with TestEffortSpent
            '''
            task.insert_effort_spent(0, [interval])
            with pytest.raises(ValueError) as ex:
                task.insert_children(0, [child1])
            assert 'Task cannot become a parent as it already has effort spent on it' in str(ex.value)
