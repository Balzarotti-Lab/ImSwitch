from .LaserManager import LaserManager

class OmicronQuixX_RS232LaserManager(LaserManager):
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
        # self.deactAdHocMode()
        # self.setOperatingMode()
        # self.setAnalogImpedance()           # set to 0...1V (could be uncommented and last status of Omicron Control Center will be used)
        # self.setDigitalImpedance()          # set to 0...5V (could be uncommented and last status of Omicron Control Center will be used)

    def getFirmware(self):
        """ Gets firmware and sets delimiter to '|', 
            calling '?GFw' uses default delimiter '§', which is not compatible for RS232Manager?,
            after a reset delimiter changes back to default """
        cmd = '?GFw|'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                                # --> remove later
        return reply

    def getOperatingMode(self):
        """ Returns the selected frequency of the laser. """
        cmd = '?GOM'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                                # --> remove later
        return reply

    def setOperatingMode(self, selectMode: str = "APC (no modulation)"):                            # default mode (at the moment)
        """ Sets operating mode (see table) by using a 16bit-chain as Hex-Code,
            starting with Bit 15 and ending with Bit 0,
            example: 1000 0000 0001 1000 -->in hex: 8018,
            AutoPowerUp enabled, AutoStartUp disabled, USB Ad-hoc disabeld etc... """
        hexa = self.getOperatingMode()
        print("new mode:", selectMode)                                                          # --> remove later
        print(hexa)                                                                             # --> remove later
        if hexa[:4] == "!GOM":                  # verifies correct answer commamnd from laser
            if selectMode == "APC (no modulation)":
                hexaMod = self.modifyHex(hexa[4:], 7, '1')     # Hex, Index (0 - 15), Bit (0 or 1) as string
                print("auf Apc")
            elif selectMode == "ACC":
                hexaMod = self.modifyHex(hexa[4:], 7, '0')
                print("auf Acc")
        else:
            print("Error while checking operating mode")                    # --> remove later or change to an error logger
            return
        cmd = '?SOM' + hexaMod
        reply = self._rs232manager.query(cmd)
        print(cmd)                                                                              # --> remove later
        print(reply)                                                                            # --> remove later
        return reply
        
    def deactAdHocMode(self):  
        """ Disables USB-AdHoc-Mode which causes problems in the communicaton order
            AdHoc Mode is disabled by setting Bit14 to '0' (see table in manual) """
        hexa = self.getOperatingMode()
        if hexa[:4] == "!GOM": 
            hexaMod = self.modifyHex(hexa[4:], 2, '0')      # Hexadecimal, Index:2 is Bit14, Bit (0 or 1) as string
            cmd = '?SOM' + hexaMod
            reply = self._rs232manager.query(cmd)
            print(reply)                                                                            # --> remove later
        return

    def setEnabled(self, enabled):
        """ Turn on (n) or off (f) laser emission """
        if enabled:
            value = "n"
        else:
            value = "f"
        cmd = '?LO' + value
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later

    def setValue(self, power):    # (setPowerPercent)
        """ Handles output power.
            Sends a RS232 command to the laser specifying the new intensity. """
        value = round(power)         # assuming input value is [0,1023]
        cmd = '?SPP' + str(value)
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later
    
    def getPowerPercent(self):
        """ Get power in percent """
        cmd = '?GPP'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later

    def getMaxPower(self):
        """ Returns the maximum power of the laser. """
        cmd = '?GMP'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later
        return reply
    
    def measureTempDiode(self):
        """ Returns the temperature of the diode (<40°C!). """
        cmd = '?MTD'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later
        return reply
    
    def measureTempAmbient(self):
        """ Returns the ambient temperature of the laser. """
        cmd = '?MTA'
        reply = self._rs232manager.query(cmd)
        print(reply)                                                                            # --> remove later
        return reply
                                                          
    def setAnalogModulation(self, enabled):
        hexa = self.getOperatingMode()
        if hexa[:4] == "!GOM":                  # verifies correct answer commamnd from laser
            if enabled:
                hexaMod = self.modifyHex(hexa[4:], 8, '1')      # Hexadecimal, Index:8 is Bit7, Bit (0 or 1) as string (see setOperatingMode)
            else:
                hexaMod = self.modifyHex(hexa[4:], 8, '0')
        else:
            print("Error while checking operating mode")                    # --> remove later or change to an error logger
            return
        cmd = '?SOM' + hexaMod
        reply = self._rs232manager.query(cmd)
        print("analog changed")
        print(reply)                                                                            # --> remove later
        return reply

    def setDigitalModulation(self, enabled):
        hexa = self.getOperatingMode()
        if hexa[:4] == "!GOM":      
            if enabled:
                hexaMod = self.modifyHex(hexa[4:], 10, '1')      # Hexadecimal, Index:10 is Bit5, Bit (0 or 1) as string (see setOperatingMode)
            else:
                hexaMod = self.modifyHex(hexa[4:], 10, '0')
        else:
            print("Error while checking operating mode")                    # --> remove later or change to an error logger
            return
        cmd = '?SOM' + hexaMod
        reply = self._rs232manager.query(cmd)
        print("digital changed")
        print(reply)                                                                            # --> remove later
        return reply
    
    def setAnalogImpedance(self):  
        """ Switches to 0...1V [0] input voltage (alternatve: 0...5V [1]) """
        hexa = self.getOperatingMode()
        if hexa[:4] == "!GOM": 
            print("aImp " + hexa)
            hexaMod = self.modifyHex(hexa[4:], 3, '0')       # Hexadecimal, Index:3 is Bit12, Bit (0 or 1) as string
            cmd = '?SOM' + hexaMod
            reply = self._rs232manager.query(cmd)
            print(cmd)                                                                            # --> remove later
        return
    
    def setDigitalImpedance(self):  
        """ Switches to 0...5V [1] input voltage (alternatve: 0...1V [0]) """
        hexa = self.getOperatingMode()
        if hexa[:4] == "!GOM": 
            print("dImp " + hexa)
            hexaMod = self.modifyHex(hexa[4:], 4, '1')       # Hexadecimal, Index:4 is Bit11, Bit (0 or 1) as string
            cmd = '?SOM' + hexaMod
            reply = self._rs232manager.query(cmd)
            print(cmd)                                                                            # --> remove later
        return
    

    def modifyHex(self, hexa: str, index: int, bit: str):
        """ modifies a single bit of a 4 letter hexadecimal string (16bits) 
            at specified index position """
        binary = bin(int(hexa, 16))[2:].zfill(16)
        binary = binary[:index] + bit + binary[index+1:]
        hexaMod = hex(int(binary, 2))[2:].zfill(4).upper()
        return hexaMod
    

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
