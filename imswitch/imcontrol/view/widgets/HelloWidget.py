import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
from imswitch.imcommon.view.guitools import naparitools, pyqtgraphtools

from .basewidgets import Widget


class HelloWidget(Widget):

    sigValueChanged = QtCore.Signal(float)  # (value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.showCheck = QtWidgets.QCheckBox("Heeyyyyy!")
        self.showCheck.setCheckable(True)

        # add setpoint element
        self.setPointEdit = QtWidgets.QLineEdit(str(2))
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # add graph
        self.graph = pyqtgraphtools.ProjectionGraph()

        # Grid layout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.graph, 0, 0, 1, 6)
        grid.addWidget(self.showCheck, 1, 0, 2, 1)
        grid.addWidget(self.setPointEdit, 1, 1, 2, 1)

        # connect signals
        self.setPointEdit.returnPressed.connect(
            lambda: self.sigValueChanged.emit(self.getValue())
        )

        self.layer = None

    def updateGraph(self, value):
        self.graph.updateGraph(value)

    def getValue(self):
        return float(self.setPointEdit.text())
