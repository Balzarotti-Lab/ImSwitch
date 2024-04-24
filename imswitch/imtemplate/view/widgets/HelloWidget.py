import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

# from imswitch.imcommon.view.guitools import pyqtgraphtools
# from imswitch.imcontrol.view import guitools

from .basewidgets import Widget


class HelloWidget(Widget):

    def __init__(self, *args, **kwargs):
        # debug log message
        super().__init__(*args, **kwargs)
        print('HelloWidget.__init__')
        self.__logger.debug('Initializing')
        self.label = QtWidgets.QLabel('Hello, World!')
        self.showCheck = QtWidgets.QCheckbox('show')
        self.showCheck.setChecked(True)
        # self.setLayout(QtWidgets.QVBoxLayout())
        # self.layout().addWidget(self.label)
