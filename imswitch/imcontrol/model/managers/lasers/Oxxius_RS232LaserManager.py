from .LaserManager import LaserManager

class Oxxius_RS232LaserManager(LaserManager):
    """ LaserManager for controlling Cobolt lasers (DPSS Series)

    Manager properties:
    - ``rs232device`` -- name of the defined rs232 communication channel
    through which the communication should take place """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0, isModulated = True, currentUnits='mA')
        
        self.getFirmware()
        self.setOperatingMode()
        self.setAnalogModulation()
        self.setDigitalModulation()

    def getFirmware(self):
        """ Gets firmware """
        cmd = '?HID'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                                # --> remove later
        return reply

    def setOperatingMode(self, selectMode: str = "APC (analog only)"):                            # uses "a" as default mode (at the moment)
        """ Sets potential operating mode """                                                                       # --> remove later
        if selectMode == "APC (analog only)":
            cmd = 'APC=1'     
        elif selectMode == "ACC":
            cmd = 'ACC=1'
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

    # def setModulationState(self, enabled):
    #     """ Switch from CW to modulated """
    #     if enabled:
    #         value = "1"
    #     else:
    #         value = "0"
    #     cmd = 'CW=' + value
    #     reply = self._rs232manager.query(cmd)
    #     print(cmd)                                                                              # --> remove later
    #     print(reply)       

    def setValue(self, power):    # (setPowerPercent)
        """ Handles output power.
            Sends a RS232 command to the laser specifying the new intensity. """
        value = round(power)     
        cmd = 'P=' + str(value)
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)

    def setCurrent(self, current):    # (setCurrentPercent)
        """ Handles laser current.
            Sends a RS232 command to the laser specifying the new intensity. """
        value = round(current, 2)     
        cmd = 'C=' + str(value)
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                           # --> remove later
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

    def setAnalogModulation(self, enabled: bool = False):
        """ Turn on or off analog modulation """
        if enabled:
            value = "1"
        else:
            value = "0"
        cmd = 'AM=' + value
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)                                                                            # --> remove later
        print("analog worked")
    
    def setDigitalModulation(self, enabled: bool = False):
        """ Turn on or off digital modulation """
        if enabled:
            value = "1"
        else:
            value = "0"
        cmd = 'TTL=' + value
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)     
        print("digital worked")

    


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
