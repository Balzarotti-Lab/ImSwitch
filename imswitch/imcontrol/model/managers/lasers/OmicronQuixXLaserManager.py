from .LaserManager import LaserManager

class OmicronQuixXLaserManager(LaserManager):
    """ LaserManager for controlling Omicron lasers of xX-series (especially QuixX)

    Manager properties:
    - ``rs232device`` -- name of the defined rs232 communication channel
    through which the communication should take place """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0, isModulated = True)

        self.getFirmware() 
        self.deactAdHocMode()

    def getFirmware(self):
        """ Gets firmware and sets delimiter to '|', 
            calling '?GFw' uses default delimiter '§', which is not compatible for RS232Manager?,
            after a reset delimiter changes back to default """
        cmd = '?GFw|'
        self._rs232manager.query(cmd)

    def getOperatingMode(self):
        """ Returns the selected frequency of the laser. """
        cmd = '?GOM'
        reply = self._rs232manager.query(cmd)
        return reply
       
    def setOperatingMode(self):
        """ Sets operating mode (see table) by using a 16bit-chain as Hex-Code """
        cmd = '?SOM8018'                # example
        self._rs232manager.query(cmd)
        
    def deactAdHocMode(self):  
        """ Disables USB-AdHoc-Mode which causes problems in the communicaton order
            AdHoc Mode is disabled by setting Bit14 to '0' (see table in manual) """
        cmd = '?SOM8018'
        self._rs232manager.query(cmd)

    def setEnabled(self, enabled):
        """ Turn on (n) or off (f) laser emission """
        if enabled:
            value = "n"
        else:
            value = "f"
        cmd = '?LO' + value
        self._rs232manager.query(cmd)

    def setValue(self, power):    # (setPowerPercent)
        """ Handles output power.
            Sends a RS232 command to the laser specifying the new intensity. """
        value = round(power)         # assuming input value is [0,1023]
        cmd = '?SPP' + str(value)
        self._rs232manager.query(cmd)
    
    def getPowerPercent(self):
        """ Get power in percent """
        cmd = '?GPP'
        reply = self._rs232manager.query(cmd)
        return reply

    def getMaxPower(self):
        """ Returns the maximum power of the laser. """
        cmd = '?GMP'
        reply = self._rs232manager.query(cmd)
        return reply
    
    def measureTempDiode(self):
        """ Returns the temperature of the diode (<40°C!). """
        cmd = '?MTD'
        reply = self._rs232manager.query(cmd)
        return reply
    
    def measureTempAmbient(self):
        """ Returns the ambient temperature of the laser. """
        cmd = '?MTA'
        reply = self._rs232manager.query(cmd)
        return reply
    

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
