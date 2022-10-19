from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
import time

PHYS_FACTOR = 1
class ESP32StageManager(PositionerManager):


    def __init__(self, positionerInfo, name, **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self._rs232manager = lowLevelManagers['rs232sManager'][
            positionerInfo.managerProperties['rs232device']
        ]
        self.__logger = initLogger(self, instanceName=name)

        # calibrated stepsize in steps/µm
        if positionerInfo.managerProperties.get('stepsizeX') is not None:
            self.stepsizeX = positionerInfo.managerProperties['stepsizeX']
        else:
            self.stepsizeX = 1
        # calibrated stepsize
        if positionerInfo.managerProperties.get('stepsizeY') is not None:
            self.stepsizeY = positionerInfo.managerProperties['stepsizeY']
        else:
            self.stepsizeY = 1

        # calibrated stepsize
        if positionerInfo.managerProperties.get('stepsizeZ') is not None:
            self.stepsizeZ = positionerInfo.managerProperties['stepsizeZ']
        else:
            self.stepsizeZ = 1


        # calibrated backlash
        if positionerInfo.managerProperties.get('backlashX') is not None:
            self.backlashX = positionerInfo.managerProperties['backlashX']
        else:
            self.backlashX = 1

        # calibrated backlash
        if positionerInfo.managerProperties.get('backlashY') is not None:
            self.backlashY = positionerInfo.managerProperties['backlashY']
        else:
            self.backlashY = 1

        # calibrated backlash
        if positionerInfo.managerProperties.get ('backlashZ') is not None:
            self.backlashZ = positionerInfo.managerProperties['backlashZ']
        else:
            self.backlashZ = 1

        
        self.is_enabled = False

        # grab motor object
        self._motor = self._rs232manager._esp32.motor

    def move(self, value=0, axis="X", is_absolute=False, is_blocking=False):
        if axis == 'X':
            value *= self.stepsizeX
            self._motor.move_x(value, self.speed["X"], is_absolute=is_absolute, is_enabled=self.is_enabled, is_blocking=is_blocking)
            self._position[axis] = self._position[axis] + value
        elif axis == 'Y':
            value *= self.stepsizeY
            self._motor.move_y(value, self.speed["Y"], is_absolute=is_absolute, is_enabled=self.is_enabled, is_blocking=is_blocking)
            self._position[axis] = self._position[axis] + value
        elif axis == 'Z':
            value *= self.stepsizeZ
            self._motor.move_z(value, self.speed["Z"], is_absolute=is_absolute, is_enabled=self.is_enabled, is_blocking=is_blocking)
            self._position[axis] = self._position[axis] + value
        elif axis == 'XYZ':
            value *= (self.stepsizeX, self.stepsizeY, self.stepsizeZ)
            self._motor.move_xyz(value, self.speed, is_absolute=is_absolute, is_enabled=self.is_enabled, is_blocking=is_blocking)
            self._position["X"] = self._position["X"] + value[0]
            self._position["Y"] = self._position["Y"] + value[1]
            self._position["Z"] = self._position["Z"] + value[2]
        else:
            print('Wrong axis, has to be "X" "Y" or "Z".')
            return

    def setStepsize(self, stepsize, axis):
        if axis == "X":
            self.stepsizeX = stepsize
        if axis == "Y":
            self.stepsizeY = stepsize
        if axis == "Z":
            self.stepsizeZ = stepsize

    
    def measure(self, sensorID=0, NAvg=100):
        return self._motor.read_sensor(sensorID=sensorID, NAvg=NAvg)

    def setupPIDcontroller(self, PIDactive=1, Kp=100, Ki=10, Kd=1, target=500, PID_updaterate=200):
        return self._motor.set_pidcontroller(PIDactive=PIDactive, Kp=Kp, Ki=Ki, Kd=Kd, target=target, PID_updaterate=PID_updaterate)

    def moveForever(self, speed=(0,0,0), is_stop=False):
        self._motor.move_forever(speed=speed, is_stop=is_stop)
        
    def setEnabled(self, is_enabled):
        self.is_enabled = is_enabled

    def setSpeed(self, speed, axis=None):
        #TODO: Map that to the JSON!
        if type(speed)==int and axis == None:
            self._speed["X"] = speed
            self._speed["Y"] = speed
            self._speed["Z"] = speed
        else:
            self._speed[axis] = speed

    def setPosition(self, value, axis):
        if value: value+=1 # TODO: Firmware weirdness
        self._motor.set_position(axis=axis, position=value)
        self._position[axis] = value

    def closeEvent(self):
        pass

    def get_abs(self, axis=1):
        abspos = self._motor.get_position(axis=axis)
        return abspos





# Copyright (C) 2020, 2021 The imswitch developers
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
