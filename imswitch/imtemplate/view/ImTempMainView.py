from dataclasses import dataclass

from pyqtgraph.dockarea import Dock, DockArea
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.model import initLogger
from imswitch.imcommon.view import PickDatasetsDialog
from . import widgets
# from .PickSetupDialog import PickSetupDialog


class ImTempMainView(QtWidgets.QMainWindow):
    sigClosing = QtCore.Signal()

    def __init__(self, options, viewSetupInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Hello, World! Idioto!')

        # # Widget factory
        # self.factory = widgets.WidgetFactory(options)
        self.docks = {}
        self.widgets = {}
        self.shortcuts = {}

        layout = QtWidgets.QHBoxLayout()


        rightDockInfos = {
            'Hello': _DockInfo(name='Hello', yPosition=0)
        }

        leftDockInfos = {}

        allDockKeys = list(rightDockInfos.keys()) + list(leftDockInfos.keys())

        dockArea = DockArea()
        enabledDockKeys = viewSetupInfo.availableWidgets
        if enabledDockKeys is False:
            enabledDockKeys = []
        elif enabledDockKeys is True:
            enabledDockKeys = allDockKeys

        rightDocks = self._addDocks(
            {k: v for k, v in rightDockInfos.items() if k in enabledDockKeys},
            dockArea, 'right'
        )

        if 'Image' in enabledDockKeys:
            dockArea.addDock(self.docks['Image'], 'left')

        self._addDocks(
            {k: v for k, v in leftDockInfos.items() if k in enabledDockKeys},
            dockArea, 'left'
        )

        # Add dock area to layout
        layout.addWidget(dockArea)

        # Maximize window
        self.showMaximized()
        self.hide()  # Minimize time the window is displayed while loading multi module window

        # Adjust dock sizes (the window has to be maximized first for this to work properly)
        if 'Settings' in self.docks:
            self.docks['Settings'].setStretch(1, 10)
            self.docks['Settings'].container().setStretch(3, 1)
        if len(rightDocks) > 0:
            rightDocks[-1].setStretch(1, 10)
        if 'Image' in self.docks:
            self.docks['Image'].setStretch(10, 1)

    def _addDocks(self, dockInfoDict, dockArea, position):
        docks = []

        prevDock = None
        prevDockYPosition = -1
        for widgetKey, dockInfo in dockInfoDict.items():
            self.widgets[widgetKey] = self.factory.createWidget(
                getattr(widgets, f'{widgetKey}Widget')
            )
            self.docks[widgetKey] = Dock(dockInfo.name, size=(1, 1))
            self.docks[widgetKey].addWidget(self.widgets[widgetKey])
            if prevDock is None:
                dockArea.addDock(self.docks[widgetKey], position)
            elif dockInfo.yPosition > prevDockYPosition:
                dockArea.addDock(self.docks[widgetKey], 'bottom', prevDock)
            else:
                dockArea.addDock(self.docks[widgetKey], 'above', prevDock)
            prevDock = self.docks[widgetKey]
            prevDockYPosition = dockInfo.yPosition
            docks.append(prevDock)

        return docks

    def closeEvent(self, event):
        self.sigClosing.emit()
        event.accept()

@dataclass
class _DockInfo:
    name: str
    yPosition: int


# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
