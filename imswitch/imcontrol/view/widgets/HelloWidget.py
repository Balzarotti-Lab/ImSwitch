import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from .basewidgets import Widget

class HelloWidget(Widget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.showCheck = QtWidgets.QCheckBox("Heeyyyyy!")
        self.showCheck.setCheckable(True)

        # Grid layout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.showCheck, 1, 0, 1, 1)

        self.layer = None