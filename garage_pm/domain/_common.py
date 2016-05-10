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

from enum import Enum

class Interval(object):
    
    def __init__(self, begin, end):
        '''
        Parameters
        ----------
        start : datetime.datetime
        end : datetime.datetime
        '''
        assert begin < end 
        self._begin = begin
        self._end = end
        
    @property
    def begin(self):
        return self._begin
    
    @begin.setter
    def begin(self, value):
        self._validate(value, self._end)
        self._begin = value
    
    @property
    def end(self):
        return self._end
    
    @end.setter
    def end(self, value):
        self._validate(self._begin, value)
        self._end = value
        
    def _validate(self, begin, end):
        if begin > end:
            raise ValueError('Interval must begin before it ends')
        if begin == end:
            raise ValueError('Interval must not be empty (i.e. begin != end)')
    
    @property
    def duration(self):
        return self._end - self._begin
    
    def __lt__(self, other):
        if self.begin == other.begin:
            return self.end < other.end
        else:
            return self.begin < other.begin

class PlanningState(Enum):
    not_planned = 'Not planned'
    planned = 'Planned'
    finished = 'Finished'
    cancelled = 'Cancelled'
    
class EstimateType(Enum):
    
    '''
    Type of estimate that can be made
    '''
    
    optimistic = 'Optimistic'
    likely = 'Likely'
    pessimistic = 'Pessimistic'
    
