import numpy as np
from ..basecontrollers import WidgetController, LiveUpdatedController
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.model import initLogger

class HelloController(LiveUpdatedController):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self)
        self.__logger.debug('Initializing')
        self.__logger.debug(f"Shared attr: {self._commChannel.sharedAttrs._data}")

        # connect widgets signals
        self._widget.sigValueChanged.connect(self.valueChanged)
        # self._widget.lasValueChanged.connect(self.valueChanged)
        # get the value of the laser controller
        QtCore.Signal(self._commChannel.sharedAttrs._data[('Laser', '365 LED', 'Value')]).sigValueChanged.connect(self.valueChanged)

        self.vals = np.zeros(100)
        self.__logger.debug(f"vals = {self.vals}")

    def valueChanged(self, value):
        self.vals[:-1] = self.vals[1:]
        self.vals[-1] = value
        self.__logger.debug(f"vals = {self.vals}")
        self.update(self.vals)

    def update(self, value):
        self._widget.updateGraph(value)