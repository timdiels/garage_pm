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

class Task(object):
    
    def __init__(self, name):
        self.name = name
        self.description = ''
        self._parent = None
        self._children = []
    
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
        