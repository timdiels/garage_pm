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

from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtWidgets import QApplication
from chicken_turtle_util import cli
from garage_pm import __version__
from garage_pm.domain import Task, TimeTracker
from garage_pm.controllers import MainWindowController
from garage_pm.views import MainWindow
from datetime import datetime
from math import ceil
import networkx as nx
import sys
import logging

logger = logging.getLogger(__name__)

class Context(cli.DataDirectoryMixin('garage_pm'), cli.BasicsMixin(__version__), cli.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.qt_parent = QObject() #XXX if this ever gives trouble, try finding a better QObject as parent, e.g. the mainwindow. Or stop using qt signals in the domain, only use qt's existing signals.
        
        # Our clock: ticks during the first second of every minute, fitting our granularity of just a minute
        #
        # Note: QTimer never emits early, but it can emit an ms late or much
        # later (especially if the event loop gets clogged with computation
        # (which doesn't belong on the event thread))
        self._minute_timer = QTimer()
        self._minute_timer.timeout.connect(self._on_first_minute_timeout)
        now = datetime.now()
        seconds_until_next_minute = 60 - (now.second + now.microsecond * 1e-6)
        self._minute_timer.start(ceil(seconds_until_next_minute * 1000) + 500)  # + half a second or we likely emit when python time still reports 59 seconds. Double checked the initial start delay is correct. There must be some lack of accuracy in python's datetime.now
        
        self._task_dependency_graph = nx.DiGraph()
        self.effort_intervals = set()
        self._root_task = Task('Root task', self, is_root=True)
        self._time_tracker = TimeTracker(self)
        
    def _on_first_minute_timeout(self):
        self._minute_timer.setInterval(60000)
    
    @property
    def minute_timer(self):
        return self._minute_timer
    
    @property
    def task_dependency_graph(self):
        return self._task_dependency_graph
    
    @property
    def root_task(self):
        return self._root_task
    
    @property
    def time_tracker(self):
        return self._time_tracker

@Context.command()    
def main(context):
    app = QApplication(sys.argv)
    window = MainWindow()
    MainWindowController(context.root_task, window)
    window.show()
    sys.exit(app.exec_())
