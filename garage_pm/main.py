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

from PyQt5.QtCore import QObject, QItemSelectionModel
from PyQt5.QtWidgets import QApplication
from chicken_turtle_util import cli
from garage_pm import __version__
from garage_pm.views import MainWindow
from garage_pm.models import TaskTreeModel
import sys

class Context(cli.DataDirectoryMixin('garage_pm'), cli.BasicsMixin(__version__), cli.Context):
    pass

def connect(signal, slot, connect_=True):
    if connect_:
        signal.connect(slot)
    else:
        signal.disconnect(slot)

class TaskDetailsController(QObject):
    
    def __init__(self, task_details_view):
        super().__init__(task_details_view)
        self._view = task_details_view
        self._task = None
        
        # Bind from view to task
        def task_setter(attr):
            def setter(value):
                if self._task:
                    setattr(self._task, attr, value)
            return setter
        
        def set_task_description():
            if self._task:
                self._task.description = self._view.description_edit.toPlainText()
                
        self._view.name_edit.textChanged.connect(task_setter('name'))
        self._view.description_edit.textChanged.connect(set_task_description)
        self._view.effort_optimistic_edit.duration_changed.connect(task_setter('effort_optimistic'))
        self._view.effort_likely_edit.duration_changed.connect(task_setter('effort_likely'))
        self._view.effort_pessimistic_edit.duration_changed.connect(task_setter('effort_pessimistic'))
        
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
        
        # Undo previous bindings from task to view
        if self._task:
            self._connect(False)
        
        #
        self._task = value
        
        # Bind new task to view
        if self._task:
            self._connect()
            
            # Fake events to init
            self._view.name_edit.setText(self._task.name)
            self._view.description_edit.setText(self._task.description)
            self._view.effort_optimistic_edit.duration = self._task.effort_optimistic
            self._view.effort_likely_edit.duration = self._task.effort_likely
            self._view.effort_pessimistic_edit.duration = self._task.effort_pessimistic
            self._view.effort_estimated_edit.set_duration(self._task.effort_estimated)
            
    def _connect(self, connect_=True):
        connect(self._task.name_changed, self._view.name_edit.setText, connect_)
        connect(self._task.description_changed, self._view.description_edit.setPlainText, connect_)
        connect(self._task.effort_optimistic_changed, self._view.effort_optimistic_edit.set_duration, connect_)
        connect(self._task.effort_likely_changed, self._view.effort_likely_edit.set_duration, connect_)
        connect(self._task.effort_pessimistic_changed, self._view.effort_pessimistic_edit.set_duration, connect_)
        connect(self._task.effort_estimated_changed, self._view.effort_estimated_edit.set_duration, connect_)
        
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

@Context.command()    
def main(context):
    app = QApplication(sys.argv)
    root_task = None
    window = MainWindow()
    MainWindowController(root_task, window)
    window.show()
    sys.exit(app.exec_())
