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
Qt views
'''

from PyQt5.QtCore import Qt, QModelIndex 
from PyQt5.QtWidgets import QHBoxLayout, QGridLayout, QPushButton, QLabel, QWidget, QAbstractButton, QTreeView

class TreeView(QTreeView):

    @property
    def _selected_index(self):
        indices = self.selectedIndexes()
        if indices:
            return indices[0]
        else:
            return QModelIndex()
        
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            index = self._selected_index
            if index.isValid():
                model = self.model()
                parent = index.parent()
                if event.key() == Qt.Key_A:
                    if parent.isValid():
                        # append
                        model.insertRow(index.row()+1, parent)
                    else:  # root
                        # append child
                        model.insertRow(model.rowCount(index), index)
                elif event.key() == Qt.Key_Left:
                    # Move selection up a level
                    if parent.isValid():
                        grand_parent = parent.parent()
                        if grand_parent.isValid():
                            model.moveRow(parent, index.row(), grand_parent, parent.row()+1)
                elif event.key() == Qt.Key_Right:
                    # Move selection down a level
                    if parent.isValid() and index.row() > 0:
                        index_above = index.sibling(index.row()-1, 0)
                        model.moveRow(parent, index.row(), index_above, model.rowCount(index_above))
                elif event.key() == Qt.Key_Up:
                    # Move up a row, unless top row
                    if parent.isValid() and index.row() > 0:
                        model.moveRow(parent, index.row(), parent, index.row()-1)
                elif event.key() == Qt.Key_Down:
                    # Move down a row, unless bottom row
                    if parent.isValid() and model.rowCount(parent)-1 != index.row():
                        model.moveRow(parent, index.row(), parent, index.row()+2)
                else:
                    super().keyPressEvent(event)
        elif event.key() == Qt.Key_Delete:
            index = self._selected_index
            if index.isValid():
                self.model().removeRow(index.row(), index.parent())
        else:
            super().keyPressEvent(event)

class MainWindow(QWidget):
    def __init__(self, parent=None, f=Qt.Widget):
        super().__init__(parent, f)
        
        self.setWindowFlags(Qt.Window)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setWindowTitle('Garage PM')
        self.resize(1800, 900)
        
        #
        self.task_tree_view = TreeView()
        self.task_tree_view.setWordWrap(True)
        self.task_tree_view.setHeaderHidden(True)
        
        # Grid layout
        layout = QGridLayout()
        layout.addWidget(self.task_tree_view, 0, 0)
        
        # Finish window
        self.setLayout(layout)
        
        
    