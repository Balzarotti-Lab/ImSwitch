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
        self._widget.sigValueChanged.connect(self.valueChanged)

        self._commChannel.sigLaserValueChanged.connect(self.handleLaserValueChanged)
        self._commChannel.sigLaserValueChanged.connect(self.handleLaserValueChanged)
        # self._commChannel.sigLaserValueChanged[float].connect(self.debugSignal)


        self.vals = np.zeros(100)
        self.__logger.debug(f"vals = {self.vals}")

    def valueChanged(self, value):
        self.vals[:-1] = self.vals[1:]
        self.vals[-1] = value
        self._commChannel.sigLaserValueChanged.emit(value)

    # def valueChanged(self, value):

    def handleLaserValueChanged(self, lasName, val):
        self.__logger.debug(f"Received new value: {lasName} and {val}")
        self.vals[:-1] = self.vals[1:]
        self.vals[-1] = val
        self.__logger.debug(f"vals = {self.vals}")
        self.update(self.vals)
        # Do something with newValue

    def update(self, value):
        self._widget.updateGraph(value)