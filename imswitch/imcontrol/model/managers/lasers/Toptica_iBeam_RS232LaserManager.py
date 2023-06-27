from .LaserManager import LaserManager

import time                                                                                     # --> remove later

class Toptica_iBeam_RS232LaserManager(LaserManager):
    """ LaserManager for controlling Toptica iBeamSmart Lasers

    Manager properties:
    - ``rs232device`` -- name of the defined rs232 communication channel
    through which the communication should take place """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0, isModulated = True)

        time.sleep(2)                 # for testing with Arduino device (otherwise timeout error)  # --> remove later
        
        self.getFirmware() 
        self.enableChannel2()
        # self.setOperatingMode()

    def getFirmware(self):
        """ Gets firmware and sets delimiter to '|', 
            calling '?GFw' uses default delimiter '§', which is not compatible for RS232Manager?,
            after a reset delimiter changes back to default """
        cmd = 'ver'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                                # --> remove later
        return reply

    def getOperatingMode(self):
        """ Returns the selected frequency of the laser. """
        cmd = ''
        return self._rs232manager.query(cmd)

    def setOperatingMode(self, selectMode: str = "a"):                            # uses "a" as default mode (at the moment)
        """ Sets potential operating mode """                                                                       # --> remove later

        if selectMode == "a":
            cmd = 'a'     
        elif selectMode == "b":
            cmd = 'b'
        elif selectMode == "c":
            cmd = 'c'
        else: cmd = ''

        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)                                                                            # --> remove later
        return reply
        
    def enableChannel2(self):  
        """ Enables Channel 2 """
        cmd = 'ch 1 pow 0.0'        # sets Ch1 to Zero 
        self._rs232manager.query(cmd)
        cmd = 'en 2'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later

    # def disableChannel2(self):  
    #     """ disables Channel 2 """
    #     cmd = 'di 2'
    #     reply = self._rs232manager.query(cmd)
    #     print(reply)         

    def setEnabled(self, enabled):
        """ Turn on (n) or off (f) laser emission """
        if enabled:
            value = 'on'
        else:
            value = 'off'
        cmd = 'la ' + value
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later

    def setValue(self, power):    # (setPowerPercent)
        """ Handles output power.
            Sends a RS232 command to the laser specifying the new intensity. """
        value = round(power)         # assuming input value is [0,1023]
        cmd = 'ch 2 pow ' + str(value)
        self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
                                                                                       
    def getPowerPercent(self):
        """ Get set-power in percent of all available levels """
        cmd = 'sh level pow'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later
    
    def setDigitalModulation(self, enabled):
        """ Turn on (n) or off (f) laser emission """
        if enabled:
            value = 'en'
        else:
            value = 'di'
        cmd = value + ' ext' 
        reply = self._rs232manager.query(cmd)
        print(reply)     
    
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
