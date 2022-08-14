from imswitch.imcommon.model import initLogger
from .LEDMatrixManager import LEDMatrixManager
import numpy as np

class ESP32LEDMatrixManager(LEDMatrixManager):
    """ LEDMatrixManager for controlling LEDs and LEDMatrixs connected to an 
    ESP32 exposing a REST API
    Each LEDMatrixManager instance controls one LED.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    - ``channel_index`` -- LEDMatrix channel (A to H)
    """

    def __init__(self, LEDMatrixInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.power = 0
        self.I_max = 255
        self.setEnabled = False
        self.intesnsity=0

        try:
            self.Nx = LEDMatrixInfo.managerProperties['Nx']
            self.Ny = LEDMatrixInfo.managerProperties['Ny']
        except:
            self.Nx = 8
            self.Ny = 8
        
        self.N_leds = self.Nx*self.Ny

        self.pattern = np.array((np.reshape(np.random.randint(0,self.I_max ,self.N_leds),(self.Nx,self.Ny)),
                       np.reshape(np.random.randint(0,self.I_max ,self.N_leds),(self.Nx,self.Ny)),
                       np.reshape(np.random.randint(0,self.I_max ,self.N_leds),(self.Nx,self.Ny))))
        

        self._rs232manager = lowLevelManagers['rs232sManager'][
            LEDMatrixInfo.managerProperties['rs232device']
        ]
            
        self.esp32 = self._rs232manager._esp32
        super().__init__(LEDMatrixInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)

    def setAll(self, intensity=(0,0,0)):
        self.intesnsity=intensity
        self.esp32.send_LEDMatrix_full(intensity=intensity,timeout=1)
    
    def setPattern(self, pattern):
        self.pattern=np.int16(pattern).T
        # assuming flat array
        #if len(self.pattern)!=3:
        #    self.pattern=np.reshape(np.transpose(self.pattern), (3,int(np.sqrt(self.N_leds)),int(np.sqrt(self.N_leds))))
        self.esp32.send_LEDMatrix_array(self.pattern)
    
    def setDimensions(self, Nx, Ny):
        self.esp32.set_LEDMatrix_dimensions(Nx, Ny)
    
    def setEnabled(self, enabled):
        """Turn on (N) or off (F) LEDMatrix emission"""
        self.setEnabled = enabled
        #self.esp32.setLEDMatrixPattern(self.pattern*self.setEnabled)

    def setLEDSingle(self, indexled=0, Nleds=None, intensity=(255,255,255)):
        """Handles output power.
        Sends a RS232 command to the LEDMatrix specifying the new intensity.
        """
        self.esp32.send_LEDMatrix_single(indexled, intensity, Nleds, timeout=1)
        

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
