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

from PyQt5.QtCore import Qt, QObject, QItemSelectionModel, QSortFilterProxyModel, pyqtSignal
from garage_pm.models import TaskTreeModel, TaskEffortSpentModel
from garage_pm.domain import TaskState
from enum import Enum

def connect(signal, slot, connect_=True):
    if connect_:
        signal.connect(slot)
    else:
        signal.disconnect(slot)

def EnumRadioController(Enum):    
    '''
    Bi-directional bind an enum to a set of QRadioButton
    
    Parameters
    ----------
    Enum
        The enum type
    '''
    
    class _EnumRadioController(QObject):
    
        value_changed = pyqtSignal([Enum])
        
        def __init__(self, radios, parent=None):
            '''
            Parameters
            ----------
            radios : {QRadioButton}
            '''
            super().__init__(parent)
            self._Enum = Enum
            self._radios = radios
            for radio in radios:
                radio.toggled.connect(self._on_radio_toggled)
                
        @property
        def value(self):
            '''
            Returns
            -------
            the passed Enum
            '''
            for radio in self._radios:
                if radio.isChecked():
                    return self._Enum(radio.text())
            return None
            
        @value.setter
        def value(self, value):
            for radio in self._radios:
                radio.setChecked(radio.text() == value.value)
            
        set_value = value.fset
            
        def _on_radio_toggled(self, checked):
            if checked: # only use the toggle on event, and only if we have a setter
                self.value_changed.emit(self.value)
                
    return _EnumRadioController

# TODO separate file for this controller, it's too big.
# TODO better modularity, bundle the binding of each: e.g. a module for binding
# optimistic effort. Interactions between them, should go at a higher level than
# those modules.
class TaskDetailsController(QObject):
    
    def __init__(self, task_details_view):
        super().__init__(task_details_view)
        self._view = task_details_view
        self._task = None
        self._task_state_controller = EnumRadioController(TaskState)(self._view.task_state_radios, parent=self)
        
        self._view.planned_start_override_edit.toggled.connect(self._on_view_planned_start_override_toggled)
            
        # Bind from view to task
        def task_setter(attr):
            def setter(value):
                if self._task:
                    setattr(self._task, attr, value)
            return setter
        
        def set_task_description():
            if self._task:
                self._task.description = self._view.description_edit.toPlainText()
                
        def task_add_effort_spent():
            if self._task:
                self._effort_spent_model.insertRow(self._effort_spent_model.rowCount())
                
        def set_planned_start(value):
            if self._task:
                self._task.planned_start = value.toPyDateTime()
                
        self._view.name_edit.textChanged.connect(task_setter('name'))
        self._view.description_edit.textChanged.connect(set_task_description)
        self._view.optimistic_effort_edit.duration_changed.connect(task_setter('optimistic_effort'))
        self._view.likely_effort_edit.duration_changed.connect(task_setter('likely_effort'))
        self._view.pessimistic_effort_edit.duration_changed.connect(task_setter('pessimistic_effort'))
        self._view.add_effort_spent_button.clicked.connect(task_add_effort_spent)
        self._task_state_controller.value_changed.connect(task_setter('state'))
        self._view.planned_start_edit.dateTimeChanged.connect(set_planned_start)
        
    @property
    def task(self):
        '''
        Task which is data bound to the view
        
        Returns
        -------
        Task or None
        '''
        return self._task
    
    @task.setter
    def task(self, value):
        '''
        Task to bind, can be None
        '''
        if self._task == value:
            return
        
        self._connect(False)
        self._task = value
        self._connect(True)
            
    def _connect(self, connect_=True):
        if not self._task:
            return
        
        connect(self._task.name_changed, self._view.name_edit.setText, connect_)
        connect(self._task.description_changed, self._view.description_edit.setPlainText, connect_)
        connect(self._task.optimistic_effort_changed, self._view.optimistic_effort_edit.set_duration, connect_)
        connect(self._task.likely_effort_changed, self._view.likely_effort_edit.set_duration, connect_)
        connect(self._task.pessimistic_effort_changed, self._view.pessimistic_effort_edit.set_duration, connect_)
        connect(self._task.predicted_effort_changed, self._view.predicted_effort_edit.set_duration, connect_)
        connect(self._task.actual_effort_changed, self._view.actual_effort_edit.set_duration, connect_)
        connect(self._task.planned_start_changed, self._on_task_planned_start_changed, connect_)
        connect(self._task.planned_end_changed, self._on_task_planned_end_changed, connect_)
        connect(self._task.predicted_start_changed, self._on_task_predicted_start_changed, connect_)
        connect(self._task.predicted_end_changed, self._on_task_predicted_end_changed, connect_)
        connect(self._task.state_changed, self._task_state_controller.set_value, connect_)
        
        if connect_:
            self._effort_spent_model = TaskEffortSpentModel(self._task, self)
            proxy_model = QSortFilterProxyModel();
            proxy_model.setSourceModel(self._effort_spent_model)
            self._view.effort_spent_table.setModel(proxy_model)
            self._view.effort_spent_table.sortByColumn(0, Qt.AscendingOrder)
            
            # Fake events to init
            self._view.name_edit.setText(self._task.name)
            self._view.description_edit.setText(self._task.description)
            self._view.optimistic_effort_edit.duration = self._task.optimistic_effort
            self._view.likely_effort_edit.duration = self._task.likely_effort
            self._view.pessimistic_effort_edit.duration = self._task.pessimistic_effort
            self._view.predicted_effort_edit.duration = self._task.predicted_effort
            self._view.actual_effort_edit.duration = self._task.actual_effort
            self._on_task_planned_start_changed(self._task.planned_start)
            self._on_task_planned_end_changed(self._task.planned_end)
            self._on_task_predicted_start_changed(self._task.predicted_start)
            self._on_task_predicted_end_changed(self._task.predicted_end)
            self._task_state_controller.value = self._task.state
            self._view.planned_start_override_edit.setChecked(self._task.planned_start is not None)
        else:
            self._effort_spent_model = None
            self._view.effort_spent_table.setModel(None)
            
    def _on_task_start_end_changed(self, date_time_edit, date_time):
        if date_time:
            date_time_edit.setEnabled(True)
            date_time_edit.setDateTime(date_time)
        else:
            date_time_edit.setEnabled(False)
            
    def _on_task_planned_start_changed(self, date_time):
        self._on_start_end_changed(self._view.planned_start_edit, date_time)
        
    def _on_task_planned_end_changed(self, date_time):
        self._on_start_end_changed(self._view.planned_end_edit, date_time)
        
    def _on_task_predicted_start_changed(self, date_time):
        self._on_start_end_changed(self._view.predicted_start_edit, date_time)
        
    def _on_task_predicted_end_changed(self, date_time):
        self._on_start_end_changed(self._view.predicted_end_edit, date_time)
        
    def _on_view_planned_start_override_toggled(self, checked):
        if checked:
            self._task.planned_start = self._view.planned_start_edit.dateTime().toPyDateTime()
        else:
            self._task.planned_start = None
        
class TaskTreeViewController(QObject):
    
    # Note: most of the control code went into the TaskTreeView because we
    # needed key events which aren't available as signals
    
    def __init__(self, task_tree_model, task_tree_view):
        super().__init__(task_tree_view)
        self._model = task_tree_model
        self._view = task_tree_view
        self._view.setModel(self._model)
        
class MainWindowController(QObject):
    
    def __init__(self, root_task, window):
        super().__init__(window)
        self._window = window
        tree_view = window.task_tree_view
        self._task_tree_model = TaskTreeModel(root_task, window)
        self._task_tree_view_controller = TaskTreeViewController(self._task_tree_model, tree_view)
        self._task_details_controller = TaskDetailsController(window.task_details_view)
        
        # Bind selected task in tree to task details view
        tree_view.selectionModel().selectionChanged.connect(self._on_tree_view_selection_changed)
        
        # Fake events to initialise
        tree_view.selectionModel().select(tree_view.model().index(0, 0), QItemSelectionModel.Select)  # select root

    def _on_tree_view_selection_changed(self, selected, deselected):
        indices = selected.indexes()
        if indices:
            task = self._window.task_tree_view.model().task(indices[0])
        else:
            task = None
        self._task_details_controller.task = task
