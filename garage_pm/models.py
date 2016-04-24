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
Qt models
'''

from PyQt5.QtCore import QAbstractItemModel, Qt, QModelIndex
from garage_pm.domain import Task

# About QAbstractItemModel: the root is QModelIndex()

class TaskTreeModel(QAbstractItemModel):
    
    _header = ['name']
    
    def __init__(self, root_task, parent):
        super().__init__(parent)
        
        # Test data
        root_task = Task('root 1')
        child1 = Task('child 1.1')
        child1._parent = root_task
        child2 = Task('child 1.2')
        child2._parent = root_task
        root_task._children = [child1, child2]
        
        child11 = Task('child 1.1.1')
        child11._parent = child1
        child12 = Task('child 1.1.2')
        child12._parent = child1
        child1._children = [child11, child12]
        ######
        
        self._root_task = root_task
        
    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
    
    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid():
            try:
                task = parent.internalPointer()
                return self.createIndex(row, column, task.children[row])
            except IndexError:
                return QModelIndex()
        else:  # root
            if row == 0:
                return self.createIndex(0, column, self._root_task)
            else:
                return QModelIndex()
        
    def parent(self, index):
        if index.isValid():
            task = index.internalPointer()
            parent = task.parent
            if parent:
                if parent.parent:
                    row = parent.parent.children.index(parent)
                else:
                    row = 0  # root is at row 0
                return self.createIndex(row, index.column(), parent)
            else:
                return QModelIndex()
        else:
            return QModelIndex()
    
    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return len(parent.internalPointer().children)
        else:  # root
            return 1
        
    def columnCount(self, parent=QModelIndex()):
        return 1
        
    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            task = index.internalPointer()
            if role in (Qt.DisplayRole, Qt.EditRole):
                if index.column() == 0:
                    return task.name
            elif role == Qt.ToolTipRole:
                return task.description
        return None
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section < len(self._header):
            return self._header[section]
        else:
            return None
    
    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False
        else:
            index.internalPointer().name = value
            self.dataChanged.emit(index, index)
            return True
    
    def insertRows(self, row, count, parent=QModelIndex()):
        if not parent.isValid():
            return False  # no insert at root
        self.beginInsertRows(parent, row, row + count - 1)
        task = parent.internalPointer()
        task.insert_children(row, [Task('task') for _ in range(count)])
        self.endInsertRows()
        return True
        
    def removeRows(self, row, count, parent=QModelIndex()):
        if not parent.isValid():
            return False  # no remove the root
        self.beginRemoveRows(parent, row, row + count - 1)
        task = parent.internalPointer()
        task.remove_children(row, row+count)
        self.endRemoveRows()
        return True
    
    def moveRows(self, source_parent_index, source_row, count, destination_parent_index, destination_row):
        if not destination_parent_index.isValid():
            # Disallow moving to the root, we have a single root
            return False
        
        if not self.beginMoveRows(source_parent_index, source_row, source_row + count - 1, destination_parent_index, destination_row):
            # When trying to move a task to its descendant
            # or when violating "if sourceParent and destinationParent are the same, you must ensure that the destinationChild is not within the range of sourceFirst and sourceLast + 1"
            # http://doc.qt.io/qt-5/qabstractitemmodel.html#beginMoveRows
            print("No. Just, no.")
            return False
        
        source_parent = source_parent_index.internalPointer()
        destination_parent = destination_parent_index.internalPointer()
        source_tasks = source_parent.children[source_row:source_row+count]        
        source_parent.remove_children(source_row, source_row + count)
        if source_parent == destination_parent and destination_row > source_row:
            destination_row -= count
        destination_parent.insert_children(destination_row, source_tasks)
        self.endMoveRows()
        return True
    
    
    