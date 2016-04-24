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

from PyQt5.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout, QGridLayout, QPushButton, QLabel, QWidget, QAbstractButton,
    QTreeView, QFormLayout, QLineEdit, QTextEdit, QDateTimeEdit, QDateEdit,
    QTimeEdit, QCheckBox, QSpinBox, QAbstractItemView, QTableView
)
from datetime import timedelta

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
            
class DurationEdit(QWidget):
    
    duration_changed = pyqtSignal([timedelta])
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._days_label = QLabel('days')
        self._days_edit = QSpinBox()
        self._days_edit.setMinimum(0)
        
        self._hours_label = QLabel('hours')
        self._hours_edit = QSpinBox()
        self._hours_edit.setMinimum(0)
        self._hours_edit.setMaximum(23)
        
        self._minutes_label = QLabel('minutes')
        self._minutes_edit = QSpinBox()
        self._minutes_edit.setMinimum(0)
        self._minutes_edit.setMaximum(59)
        
        layout = QHBoxLayout()
        layout.addWidget(self._days_edit)
        layout.addWidget(self._days_label)
        layout.addWidget(self._hours_edit)
        layout.addWidget(self._hours_label)
        layout.addWidget(self._minutes_edit)
        layout.addWidget(self._minutes_label)
        
        self.setLayout(layout)
        
        self._days_edit.valueChanged.connect(self._on_value_changed)
        self._hours_edit.valueChanged.connect(self._on_value_changed)
        self._minutes_edit.valueChanged.connect(self._on_value_changed)
        
    def _on_value_changed(self):
        self.duration_changed.emit(self.duration)
        
    @property
    def duration(self):
        '''
        Returns
        -------
        domain.Duration
        '''
        return timedelta(days=self._days_edit.value(), hours=self._hours_edit.value(), minutes=self._minutes_edit.value())
    
    @duration.setter
    def duration(self, value):
        self._days_edit.setValue(value.days)
        minutes = value.seconds // 60
        hours, minutes = divmod(minutes, 60)
        self._hours_edit.setValue(hours)
        self._minutes_edit.setValue(minutes)
        
    set_duration = duration.fset
    
    def setReadOnly(self, value):
        self._days_edit.setReadOnly(value)
        self._hours_edit.setReadOnly(value)
        self._minutes_edit.setReadOnly(value)
            
class TaskDetailsView(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.name_label = QLabel('Name')
        self.name_edit = QLineEdit()
        
        self.description_label = QLabel('Description')
        self.description_edit = QTextEdit()
        
        self.start_date_planned_label = QLabel('Start date (planned)')
        self.start_date_planned_edit = QDateTimeEdit()
        
        self.end_date_planned_label = QLabel('End date (planned)')
        self.end_date_planned_edit = QDateTimeEdit()
        self.end_date_planned_edit.setReadOnly(True)
        
        self.start_date_expected_label = QLabel('Start date (expected)')
        self.start_date_expected_edit = QDateTimeEdit()
        self.start_date_expected_edit.setReadOnly(True)
        
        self.end_date_expected_label = QLabel('End date (expected)')
        self.end_date_expected_edit = QDateTimeEdit()
        self.end_date_expected_edit.setReadOnly(True)
        
        self.finished_edit = QCheckBox('Finished')
        self.milestone_edit = QCheckBox('Milestone')
        
        self.effort_optimistic_label = QLabel('Effort (optimistic)')
        self.effort_optimistic_edit = DurationEdit()
        
        self.effort_likely_label = QLabel('Effort (likely)')
        self.effort_likely_edit = DurationEdit()
        
        self.effort_pessimistic_label = QLabel('Effort (pessimistic)')
        self.effort_pessimistic_edit = DurationEdit()
        
        self.effort_estimated_label = QLabel('Effort (estimated)')
        self.effort_estimated_edit = DurationEdit()
        self.effort_estimated_edit.setReadOnly(True)
        
        self.effort_actual_label = QLabel('Effort (actual)')
        self.effort_actual_edit = DurationEdit()
        self.effort_actual_edit.setReadOnly(True)
        
        layout = QFormLayout()
        layout.addRow(self.name_label, self.name_edit)
        layout.addRow(self.description_label, self.description_edit)
        layout.addRow(self.start_date_planned_label, self.start_date_planned_edit)
        layout.addRow(self.end_date_planned_label, self.end_date_planned_edit)
        layout.addRow(self.start_date_expected_label, self.start_date_expected_edit)
        layout.addRow(self.end_date_expected_label, self.end_date_expected_edit)
        layout.addRow(QLabel('Various'), self.finished_edit)
        layout.addRow(None, self.milestone_edit)
        layout.addRow(self.effort_optimistic_label, self.effort_optimistic_edit)
        layout.addRow(self.effort_likely_label, self.effort_likely_edit)
        layout.addRow(self.effort_pessimistic_label, self.effort_pessimistic_edit)
        layout.addRow(self.effort_estimated_label, self.effort_estimated_edit)
        layout.addRow(self.effort_actual_label, self.effort_actual_edit)
        
        self.setLayout(layout)

class MainWindow(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.Window)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setWindowTitle('Garage PM')
        self.resize(1800, 900)
        
        #
        self.task_tree_view = TreeView()
        self.task_tree_view.setWordWrap(True)
        self.task_tree_view.setHeaderHidden(True)
        
        #
        self.task_details_view = TaskDetailsView()
        
        # Grid layout
        layout = QGridLayout()
        layout.addWidget(self.task_tree_view, 0, 0)
        layout.addWidget(self.task_details_view, 0, 1)
        
        # Finish window
        self.setLayout(layout)
        
        
    