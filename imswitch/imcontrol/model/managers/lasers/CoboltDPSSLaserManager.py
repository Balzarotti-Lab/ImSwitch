from lantz import Q_

from imswitch.imcommon.model import initLogger
from .LantzLaserManager import LantzLaserManager

class CoboltDPSSLaserManager(LantzLaserManager):
    """ LaserManager for Cobolt DPSS lasers. Uses digital modulation mode when
    scanning. Does currently not support DPL type lasers.

    Manager properties:

    - ``digitalPorts`` -- a string array containing the COM ports to connect
      to, e.g. ``["COM4"]``
    """

    def __init__(self, laserInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0,
                         driver='cobolt.coboltDPSS.CoboltDPSS', **_lowLevelManagers)

        self._laser.enabled = False
        self._laser.autostart = False

    def setEnabled(self, enabled):
        self._laser.enabled = enabled

    def setValue(self, power):
        power = int(power)
        self._setBasicPower(power * Q_(1, 'mW'))                # <-- instead of next 4 lines

    def _setBasicPower(self, power):
        self._laser.power_sp = power / self._numLasers


    def setOperatingMode(self, selectMode: str = "a"):                            # uses "a" as default mode (at the moment)
        """ Sets operating mode"""
        self._laser.ctl_mode = selectMode
        print(selectMode)                                                                              # --> remove later
        return 



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
