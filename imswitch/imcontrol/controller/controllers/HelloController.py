import numpy as np
from ..basecontrollers import WidgetController, LiveUpdatedController

from imswitch.imcommon.model import initLogger

class HelloController(LiveUpdatedController):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect widgets signals
        self._widget.sigValueChanged.connect(self.valueChanged)
        self.__logger = initLogger(self)
        self.__logger.debug('Initializing')
        self.vals = np.zeros(100)
        self.__logger.debug(f"vals = {self.vals}")

    def valueChanged(self, value):
        self.vals[:-1] = self.vals[1:]
        self.vals[-1] = value
        self.__logger.debug(f"vals = {self.vals}")
        self.update(self.vals)

    def update(self, value):
        self.__logger.debug(f"value type: {type(value)}")
        self._widget.updateGraph(value)