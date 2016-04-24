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

from PyQt5.QtWidgets import QApplication
from chicken_turtle_util import cli
from garage_pm import __version__
from garage_pm.views import MainWindow
from garage_pm.models import TaskTreeModel
import sys

class Context(cli.DataDirectoryMixin('garage_pm'), cli.BasicsMixin(__version__), cli.Context):
    pass

class TaskTreeController(object):
    
    def __init__(self, root_task, tree_view):
        self._model = TaskTreeModel(root_task, tree_view)
        tree_view.setModel(self._model)
#         tree_view

@Context.command()    
def main(context):
    app = QApplication(sys.argv)
    root_task = None
    window = MainWindow()
    TaskTreeController(root_task, window.task_tree_view)
    window.show()
    sys.exit(app.exec_())
