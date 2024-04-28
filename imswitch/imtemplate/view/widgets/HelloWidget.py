import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

# from imswitch.imcommon.view.guitools import pyqtgraphtools
# from imswitch.imcontrol.view import guitools

from .basewidgets import Widget
import logging


class HelloWidget(Widget):

    def __init__(self, *args, **kwargs):
        self.__logger = initLogger(self)
        self.__logger.info('Initializing HelloWidget')
        print('HelloWidget')

        # debug log message
        super().__init__(*args, **kwargs)


        self.showCheck = QtWidgets.QCheckBox("hiiiii")
        self.showCheck.setCheckable(True)

        # Viewbox
        self.widget = pg.GraphicsLayoutWidget()
        self.vb = self.widget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem(axisOrder='row-major')
        self.img.setTransform(self.img.transform().translate(-0.5, -0.5))
        self.vb.addItem(self.img)
        self.b.setAspectLocked (True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.hist.gradient.loadPreset('greyclip')
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)
        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.showCheck, 1, 0, 1, 1)

        # Connect signals
        self.showCheck.toggled.connect(self.sigShowToggled)
        self.layer = None
