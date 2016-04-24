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
import math

class Duration(object):
    
    def __init__(self, days=0, hours=0, minutes=0):
        '''
        Parameters
        ----------
        days : int
        hours : int
        minutes : int
        '''
        assert hours < 24
        assert minutes < 60
        assert days >= 0
        assert hours >= 0
        assert minutes >= 0
        self._days = days
        self._hours = hours
        self._minutes = minutes
        
    @property
    def days(self):
        return self._days
    
    @property
    def hours(self):
        return self._hours
        
    @property
    def minutes(self):
        return self._minutes
        
    def to_hours(self):
        '''
        Total duration as hours
        
        Returns
        -------
        float
        '''
        return self.days * 24 + self.hours + self.minutes / 60
        
    @staticmethod
    def from_hours(hours):
        '''
        Parameters
        ----------
        hours : float
        '''
        days, hours = divmod(hours, 24)
        minutes, hours = math.modf(hours)
        minutes *= 60
        return Duration(days, hours, minutes)

class Task(QObject):
    
    name_changed = pyqtSignal([str])
    description_changed = pyqtSignal([str])
    effort_optimistic_changed = pyqtSignal([Duration])
    effort_likely_changed = pyqtSignal([Duration])
    effort_pessimistic_changed = pyqtSignal([Duration])
    effort_estimated_changed = pyqtSignal([Duration])
    
    def __init__(self, name, parent):
        super().__init__(parent)
        self._parent = None
        self._children = []
        self._name = name
        self._description = ''
        self._effort_optimistic = Duration()
        self._effort_likely = Duration()
        self._effort_pessimistic = Duration()
        
        self.effort_optimistic_changed.connect(self._on_effort_input_changed)
        self.effort_likely_changed.connect(self._on_effort_input_changed)
        self.effort_pessimistic_changed.connect(self._on_effort_input_changed)
        
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
    def effort_optimistic(self):
        '''
        Get optimistic effort
        
        Returns
        -------
        Duration
        '''
        return self._effort_optimistic
    
    @effort_optimistic.setter
    def effort_optimistic(self, value):
        if self._effort_optimistic != value:
            self._effort_optimistic = value
            self.effort_optimistic_changed.emit(self._effort_optimistic)
            
    @property
    def effort_likely(self):
        return self._effort_likely
    
    @effort_likely.setter
    def effort_likely(self, value):
        if self._effort_likely != value:
            self._effort_likely = value
            self.effort_likely_changed.emit(self._effort_likely)
            
    @property
    def effort_pessimistic(self):
        return self._effort_pessimistic
    
    @effort_pessimistic.setter
    def effort_pessimistic(self, value):
        if self._effort_pessimistic != value:
            self._effort_pessimistic = value
            self.effort_pessimistic_changed.emit(self._effort_pessimistic)
            
    def _on_effort_input_changed(self):
        '''When effort optimistic, likely or pessimistic change'''
        self.effort_estimated_changed.emit(self.effort_estimated)
            
    @property
    def effort_estimated(self):
        return Duration.from_hours((self._effort_optimistic.to_hours() + 4 * self._effort_likely.to_hours() + self._effort_pessimistic.to_hours())/6)
    
    @property
    def children(self):
        '''
        Get children
        
        Do not modify directly.
        
        Returns
        -------
        [Task]
        '''
        return self._children
    
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
        