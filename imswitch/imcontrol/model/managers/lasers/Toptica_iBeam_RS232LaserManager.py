from .LaserManager import LaserManager


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

        self.getFirmware()
        self.powerLevel = 0.0
        self.channel1Status = True
        self.setAnalogModulation(False)
        self.setDigitalModulation(False)
       
    def getFirmware(self):
        """ Gets firmware """
        cmd = 'ver'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                                # --> remove later
        return reply
        
    def enableChannel2(self):  
        """ Enables Channel 2 """
        cmd = 'ch 1 pow 0.0'        # sets Ch1 to Zero 
        self._rs232manager.query(cmd)
        cmd = 'en 2'
        reply = self._rs232manager.query(cmd)
        print(reply)      
        
    # def toggleChannel(self, channel):  
    #     """ toogle Channel """
    #     cmd = 'ch 1 pow 0.0'        # sets Ch1 to Zero 
    #     self._rs232manager.query(cmd)
    #     cmd = 'en 2'
    #     reply = self._rs232manager.query(cmd)
    #     print(reply)                                                                        # --> remove later

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
        if self.channel1Status == True:
            cmd = 'ch 1 pow ' + str(value)
            self._rs232manager.query(cmd)
        self.powerLevel = value
        print(cmd)                                                                              # --> remove later

    def setCurrent(self, current):    # (setCurrentPercent)
        pass
           
    def getPowerPercent(self):
        """ Get set-power in percent of all available levels """
        cmd = 'sh level pow'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later

    def setAnalogModulation(self, enabled):
        """ Turn on (n) or off (f) laser emission """
        if enabled:
            self.channel1Status = False
            self._rs232manager.query('ch 1 pow 0.0')                                           # sets Ch1 to Zero 
            self._rs232manager.query('en 2')
        else:
            self.channel1Status = True
            self._rs232manager.query('di 2')
            self._rs232manager.query('ch 1 pow '+ str(self.powerLevel))
        print("analog changed")
    
    def setDigitalModulation(self, enabled):
        """ Turn on (n) or off (f) laser emission """
        if enabled:
            value = 'en'
        else:
            value = 'di'
        cmd = value + ' ext' 
        reply = self._rs232manager.query(cmd)
        print(reply)
        print("digital changed")     
        # reply = self._rs232manager.query('sh level pow')
        # print(reply)


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
