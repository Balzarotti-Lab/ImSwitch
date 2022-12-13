from qtpy import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QLine

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.view.widgets.StandaPositionerWidget import StandaPositionerWidget

class OpentronsDeckWidget(Widget):
    """ Widget in control of the piezo movement. """
    sigStepUpClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepDownClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigsetSpeedClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.numPositioners = 0
        self.pars = {}
        self.main_grid_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_grid_layout)

        self.__logger = initLogger(self, instanceName="OpentronsDeckWidget")

    def select_labware(self, slot):
        if hasattr(self,"_grid_group_box"):
            self.main_grid_layout.removeWidget(self._grid_group_box)
        self._grid_group_box = QtWidgets.QGroupBox(f"Labware layout: {slot}: {self._labware_dict[slot]}")
        layout = QtWidgets.QGridLayout()

        labware = self._labware_dict[slot]
        # Create dictionary to hold buttons
        self.wells = {}
        # Create grid layout for wells (buttons)
        well_buttons = {}
        rows = len(self._labware_dict[slot].rows())
        columns = len(self._labware_dict[slot].columns())
        for r in list(range(rows)):
            for c in list(range(columns)):
                well = labware.rows()[r][c]
                well_buttons[well.well_name] = (r,c)
        # Create wells (buttons) and add them to the grid layout
        for corrds, pos in well_buttons.items():
            self.wells[corrds] = guitools.BetterPushButton(corrds)  # QtWidgets.QPushButton(corrds)
            self.wells[corrds].setFixedSize(40, 30)
            self.wells[corrds].setStyleSheet("background-color: grey; font-size: 14px")
            # Set style for empty cell
            # self.wells[corrds].setStyleSheet("background-color: none")
            # Add button/label to layout
            layout.addWidget(self.wells[corrds], pos[0], pos[1])
        self._grid_group_box.setLayout(layout)
        self.main_grid_layout.addWidget(self._grid_group_box)
        self.setLayout(self.main_grid_layout)

    def add_home(self, layout):
        self.home = guitools.BetterPushButton(text="HOME")  # QtWidgets.QPushButton(corrds)
        self.home.setFixedSize(50, 30)
        self.home.setStyleSheet("background-color: black; font-size: 14px")
        layout.addWidget(self.home)

    def add_zero(self, layout):
        # self.zero = guitools.BetterPushButton(text="ZERO")  # QtWidgets.QPushButton(corrds)
        # TODO: implement ZERO
        self.zero = QtWidgets.QLabel(text="ZERO")  # QtWidgets.QPushButton(corrds)
        self.zero.setFixedSize(50, 30)
        # self.zero.setStyleSheet("background-color: black; font-size: 14px")
        self.zero.setStyleSheet("background-color: None; font-size: 14px")
        layout.addWidget(self.zero)

    def initialize_opentrons_deck(self, deck_dict, labwares_dict):
        self._deck_dict = deck_dict
        self._labware_dict = labwares_dict

        self._horizontal_group_box = QtWidgets.QGroupBox("Deck layout")
        layout = QtWidgets.QHBoxLayout()

        # Add home and zero buttons
        self.add_home(layout)
        self.add_zero(layout)

        # Create dictionary to hold buttons
        slots = [slot["id"] for slot in deck_dict["locations"]["orderedSlots"]]
        used_slots = list(labwares_dict.keys())
        self.deck_slots = {}

        # Create dictionary to store deck slots names (button texts)
        slots_buttons = {s: (0,i+2) for i,s in enumerate(slots)}
        for corrds, pos in slots_buttons.items():
            if corrds in used_slots:
                # Do button if slot contains labware
                self.deck_slots[corrds] = guitools.BetterPushButton(corrds)  # QtWidgets.QPushButton(corrds)
                self.deck_slots[corrds].setFixedSize(30, 30)
                self.deck_slots[corrds].setStyleSheet("background-color: grey; font-size: 14px")
            else:
                self.deck_slots[corrds] = QtWidgets.QLabel(corrds)  # QtWidgets.QPushButton(corrds)
                self.deck_slots[corrds].setFixedSize(30, 30)
                self.deck_slots[corrds].setStyleSheet("background-color: None; font-size: 14px")
            layout.addWidget(self.deck_slots[corrds])

        self._horizontal_group_box.setLayout(layout)
        self.main_grid_layout.addWidget(self._horizontal_group_box)
        self.setLayout(self.main_grid_layout)

    def addPositioner(self, positionerName, axes, hasSpeed, initial_position, initial_speed ):
        self._positioner_widget = QtWidgets.QGroupBox("Positioners")
        layout = QtWidgets.QGridLayout()
        for i in range(len(axes)):
            axis = axes[i]
            parNameSuffix = self._getParNameSuffix(positionerName, axis)
            label = f'{axis}' if positionerName != axis else positionerName

            self.pars['Label' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{label}</strong>')
            self.pars['Label' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['Position' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{initial_position[axis]:.3f} mm</strong>')
            self.pars['Position' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['UpButton' + parNameSuffix] = guitools.BetterPushButton('+')
            self.pars['DownButton' + parNameSuffix] = guitools.BetterPushButton('-')
            self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('0')
            self.pars['StepUnit' + parNameSuffix] = QtWidgets.QLabel('mm')

            layout.addWidget(self.pars['Label' + parNameSuffix], self.numPositioners, 0)
            layout.addWidget(self.pars['Position' + parNameSuffix], self.numPositioners, 1)
            layout.addWidget(self.pars['UpButton' + parNameSuffix], self.numPositioners, 2)
            layout.addWidget(self.pars['DownButton' + parNameSuffix], self.numPositioners, 3)
            layout.addWidget(QtWidgets.QLabel('Step'), self.numPositioners, 4)
            layout.addWidget(self.pars['StepEdit' + parNameSuffix], self.numPositioners, 5)
            layout.addWidget(self.pars['StepUnit' + parNameSuffix], self.numPositioners, 6)

            # Connect signals
            self.pars['UpButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            )
            self.pars['DownButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepDownClicked.emit(positionerName, axis)
            )

            if hasSpeed:
                self.pars['Speed' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{initial_speed[axis]:.2f} mm/s</strong>')
                self.pars['Speed' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
                self.pars['ButtonSpeedEnter' + parNameSuffix] = guitools.BetterPushButton('Set')
                self.pars['SpeedEdit' + parNameSuffix] = QtWidgets.QLineEdit(f'{initial_speed[axis]}')
                self.pars['SpeedUnit' + parNameSuffix] = QtWidgets.QLabel('mm/s')
                layout.addWidget(self.pars['SpeedEdit' + parNameSuffix], self.numPositioners, 10)
                layout.addWidget(self.pars['SpeedUnit' + parNameSuffix], self.numPositioners, 11)
                layout.addWidget(self.pars['ButtonSpeedEnter' + parNameSuffix], self.numPositioners, 12)
                layout.addWidget(self.pars['Speed' + parNameSuffix], self.numPositioners, 7)


                self.pars['ButtonSpeedEnter'+ parNameSuffix].clicked.connect(
                    lambda *args, axis=axis: self.sigsetSpeedClicked.emit(positionerName, axis)
                )

            self.numPositioners += 1
        self._positioner_widget.setLayout(layout)
        self.main_grid_layout.addWidget(self._positioner_widget)


    def getStepSize(self, positionerName, axis):
        """ Returns the step size of the specified positioner axis in
        milimeters. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['StepEdit' + parNameSuffix].text())

    def setStepSize(self, positionerName, axis, stepSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of milimeters. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['StepEdit' + parNameSuffix].setText(stepSize)

    def getSpeed(self, positionerName, axis):
        """ Returns the step size of the specified positioner axis in
        milimeters. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['SpeedEdit' + parNameSuffix].text())

    def setSpeedSize(self, positionerName, axis, speedSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['SpeedEdit' + parNameSuffix].setText(speedSize)

    def updatePosition(self, positionerName, axis, position):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['Position' + parNameSuffix].setText(f'<strong>{position:.2f} mm</strong>')

    def updateSpeed(self, positionerName, axis, speed):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['Speed' + parNameSuffix].setText(f'<strong>{speed:.2f} mm/s</strong>')

    def _getParNameSuffix(self, positionerName, axis):
        return f'{positionerName}--{axis}'


  

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
