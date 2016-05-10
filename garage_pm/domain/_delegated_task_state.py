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

from ._leaf_task_state import LeafTaskState

class DelegatedTaskState(LeafTaskState):

    def __init__(self, common_data):
        super().__init__(common_data)
            
    @property
    def is_child_insertion_disallowed(self):
        return 'Cannot add child tasks to a delegated task'
    
    def validate_set_planning_state(self, state):
        return None
