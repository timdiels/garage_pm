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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QScrollBar, QDoubleSpinBox, QGridLayout, QPushButton, QLabel, QWidget, QAbstractButton, QAbstractSpinBox, QSlider
from PyQt5.QtGui import QFont

class MainWindow(QWidget):
    def __init__(self, parent=None, f=Qt.Widget):
        super().__init__(parent, f)
        
        self.setWindowFlags(Qt.Window)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setWindowTitle('Garage PM')
        self.resize(1800, 900)
        
        label = QLabel("Hello world")
        
        # Grid layout
        layout = QGridLayout()
        layout.addWidget(label, 0, 0)
        
        # Finish window
        self.setLayout(layout)
            
    