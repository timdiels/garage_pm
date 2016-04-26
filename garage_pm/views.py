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
    QHBoxLayout, QGridLayout, QPushButton, QLabel, QWidget,
    QTreeView, QFormLayout, QLineEdit, QTextEdit, QDateTimeEdit,
    QCheckBox, QSpinBox, QAbstractItemView, QTableView,
    QHeaderView, QStyledItemDelegate, QRadioButton
)
from datetime import timedelta
from garage_pm import config
from garage_pm.domain import TaskState

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
        elif event.modifiers() == Qt.NoModifier and event.key() == Qt.Key_Delete:
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
        
class DateTimeItemDelegate(QStyledItemDelegate):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def createEditor(self, parent, option, index):
        edit = QDateTimeEdit(parent)
        edit.setFrame(False)
        edit.setDisplayFormat(config.qt_date_time_format)
        edit.setCalendarPopup(True)
        return edit
    
    def setEditorData(self, editor, index):
        editor.setDateTime(index.data(Qt.EditRole))
        
    def setModelData(self, editor, model, index):
        model.setData(index, editor.dateTime().toPyDateTime())
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect);
            
class EffortSpentTableView(QTableView):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.NoModifier and event.key() == Qt.Key_Delete:
            rows = sorted((index.row() for index in self.selectedIndexes()), reverse=True)
            for row in rows:
                self.model().removeRow(row)
        else:
            super().keyPressEvent(event)
                    
class TaskDetailsView(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.name_label = QLabel('Name')
        self.name_edit = QLineEdit()
        
        self.description_label = QLabel('Description')
        self.description_edit = QTextEdit()
        
        self.start_date_planned_label = QLabel('Start date (planned)')
        self.start_date_planned_edit = QDateTimeEdit()
        self.start_date_planned_edit.setCalendarPopup(True)
        self.start_date_planned_edit.setDisplayFormat(config.qt_date_time_format)
        
        self.end_date_planned_label = QLabel('End date (planned)')
        self.end_date_planned_edit = QDateTimeEdit()
        self.end_date_planned_edit.setReadOnly(True)
        self.end_date_planned_edit.setCalendarPopup(True)
        self.end_date_planned_edit.setDisplayFormat(config.qt_date_time_format)
        
        self.start_date_expected_label = QLabel('Start date (expected)')
        self.start_date_expected_edit = QDateTimeEdit()
        self.start_date_expected_edit.setReadOnly(True)
        self.start_date_expected_edit.setCalendarPopup(True)
        self.start_date_expected_edit.setDisplayFormat(config.qt_date_time_format)
        
        self.end_date_expected_label = QLabel('End date (expected)')
        self.end_date_expected_edit = QDateTimeEdit()
        self.end_date_expected_edit.setReadOnly(True)
        self.end_date_expected_edit.setCalendarPopup(True)
        self.end_date_expected_edit.setDisplayFormat(config.qt_date_time_format)
        
        task_radios_layout = QHBoxLayout()
        self.task_state_radios = set()
        for state in TaskState:
            radio = QRadioButton(state.value)
            self.task_state_radios.add(radio)
            task_radios_layout.addWidget(radio)
        
        self.milestone_edit = QCheckBox('Milestone')
        
        self.optimistic_effort_label = QLabel('Effort (optimistic)')
        self.optimistic_effort_edit = DurationEdit()
        
        self.likely_effort_label = QLabel('Effort (likely)')
        self.likely_effort_edit = DurationEdit()
        
        self.pessimistic_effort_label = QLabel('Effort (pessimistic)')
        self.pessimistic_effort_edit = DurationEdit()
        
        self.predicted_effort_label = QLabel('Effort (predicted)')
        self.predicted_effort_edit = DurationEdit()
        self.predicted_effort_edit.setReadOnly(True)
        
        self.actual_effort_label = QLabel('Effort (actual)')
        self.actual_effort_edit = DurationEdit()
        self.actual_effort_edit.setReadOnly(True)
        
        effort_spent_layout = self._create_effort_spent_layout()
        
        layout = QFormLayout()
        layout.addRow(self.name_label, self.name_edit)
        layout.addRow(self.description_label, self.description_edit)
        layout.addRow(self.start_date_planned_label, self.start_date_planned_edit)
        layout.addRow(self.end_date_planned_label, self.end_date_planned_edit)
        layout.addRow(self.start_date_expected_label, self.start_date_expected_edit)
        layout.addRow(self.end_date_expected_label, self.end_date_expected_edit)
        layout.addRow(QLabel('State'), task_radios_layout)
        layout.addRow(None, self.milestone_edit)
        layout.addRow(self.optimistic_effort_label, self.optimistic_effort_edit)
        layout.addRow(self.likely_effort_label, self.likely_effort_edit)
        layout.addRow(self.pessimistic_effort_label, self.pessimistic_effort_edit)
        layout.addRow(self.predicted_effort_label, self.predicted_effort_edit)
        layout.addRow(self.actual_effort_label, self.actual_effort_edit)
        layout.addRow(None, effort_spent_layout)
        
        self.setLayout(layout)

    def _create_effort_spent_layout(self):
        self.effort_spent_table = EffortSpentTableView()
        self.effort_spent_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.effort_spent_table.setSortingEnabled(True)
        self.effort_spent_table.setItemDelegate(DateTimeItemDelegate())
        self.effort_spent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.track_effort_button = QPushButton('Start')
        self.add_effort_spent_button = QPushButton('Add')
        
        layout = QGridLayout()
        layout.addWidget(self.effort_spent_table, 0, 0, 1, 2)
        layout.addWidget(self.track_effort_button, 1, 0)
        layout.addWidget(self.add_effort_spent_button, 1, 1)
        
        return layout

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
        
        
    