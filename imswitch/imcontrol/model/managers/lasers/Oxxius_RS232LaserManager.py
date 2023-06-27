from .LaserManager import LaserManager

# import time                                                                                     # --> remove later

class Oxxius_RS232LaserManager(LaserManager):
    """ LaserManager for controlling Cobolt lasers (DPSS Series)

    Manager properties:
    - ``rs232device`` -- name of the defined rs232 communication channel
    through which the communication should take place """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0, isModulated = True)

        # time.sleep(2)                 # for testing with Arduino device (otherwise timeout error)  # --> remove later
        
        self.getFirmware() 
        

    def getFirmware(self):
        """ Gets firmware and sets delimiter to '|', 
            calling '?GFw' uses default delimiter '§', which is not compatible for RS232Manager?,
            after a reset delimiter changes back to default """
        cmd = '?HID'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                                # --> remove later
        return reply

    def getOperatingMode(self):
        """ Returns the selected frequency of the laser. """
        cmd = ''
        return self._rs232manager.query(cmd)

    def setOperatingMode(self, selectMode: str = "APC"):                            # uses "a" as default mode (at the moment)
        """ Sets potential operating mode """                                                                       # --> remove later

        if selectMode == "a":
            cmd = 'APC=1'     
        elif selectMode == "b":
            cmd = 'ACC=1'
        elif selectMode == "c":
            cmd = 'c'
        else: cmd = ''

        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)                                                                            # --> remove later
        return reply
        
    def setEnabled(self, enabled):
        """ Turn on (n) or off (f) laser emission """
        if enabled:
            value = "1"
        else:
            value = "0"
        cmd = 'L=' + value
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)                                                                            # --> remove later

    def setModulationState(self, enabled):
        """ Switch from CW to modulated """
        if enabled:
            value = "1"
        else:
            value = "0"
        cmd = 'CW=' + value
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)       

    def anaologModulation(self, enabled):
        """ Turn on or off analog modulation """
        if enabled:
            value = "1"
        else:
            value = "0"
        cmd = 'AM=' + value
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)                                                                            # --> remove later
    
    def digitalModulation(self, enabled):
        """ Turn on or off digital modulation """
        if enabled:
            value = "1"
        else:
            value = "0"
        cmd = 'TTL=' + value
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)     

    def setValue(self, power):    # (setPowerPercent)
        """ Handles output power.
            Sends a RS232 command to the laser specifying the new intensity. """
        value = round(power)     
        cmd = 'P=' + value
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)

    def getPowerPercent(self):
        """ Get setted power in percent """
        cmd = '?SP'
        reply = self._rs232manager.query(cmd)
        print(reply)
        return reply            
    
    def readPower(self):                                                                        # --> remove later
        """ Read measured output power """
        cmd = '?P'
        return self._rs232manager.query(cmd)

    def getMaxPower(self):
        """ Returns the maximum power of the laser. """
        cmd = '?MAXLP'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later
        return reply

    def checkBoxOption(self):
        print("Checkbox clicked")                                                               # --> remove later
       

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
