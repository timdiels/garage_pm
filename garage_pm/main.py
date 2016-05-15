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

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication
from chicken_turtle_util import cli
from garage_pm import __version__
from garage_pm.domain import Task
from garage_pm.controllers import MainWindowController
from garage_pm.views import MainWindow
import networkx as nx
import sys

class Context(cli.DataDirectoryMixin('garage_pm'), cli.BasicsMixin(__version__), cli.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.qt_parent = QObject() #XXX if this ever gives trouble, try finding a better QObject as parent, e.g. the mainwindow. Or stop using qt signals in the domain, only use qt's existing signals.
        self._task_dependency_graph = nx.DiGraph()
        self._root_task = Task('Root task', self, is_root=True)
    
    @property
    def task_dependency_graph(self):
        return self._task_dependency_graph
        
    @property
    def root_task(self):
        return self._root_task

@Context.command()    
def main(context):
    app = QApplication(sys.argv)
    window = MainWindow()
    MainWindowController(context.root_task, window)
    window.show()
    sys.exit(app.exec_())
