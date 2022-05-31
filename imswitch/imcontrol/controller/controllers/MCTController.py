import json
import os

import numpy as np
import time 
import tifffile as tif
import threading



from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
import pyqtgraph.ptime as ptime

from ..basecontrollers import LiveUpdatedController

#import NanoImagingPack as nip

class MCTController(LiveUpdatedController):
    """Linked to MCTWidget."""
    
    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        
        # mct parameters
        self.nImages = 0
        self.timePeriod = 60 # seconds
        self.zStackEnabled = False
        self.zStackMin = 0
        self.zStackMax = 0
        self.zStackStep = 0
        
        
        self.Laser1Value = 0
        self.Laser2Value = 0
        self.LEDValue = 0
        self.MCTFilename = ""
        
        self.updateRate=2
        
        if self._setupInfo.mct is None:
            self._widget.replaceWithError('MCT is not configured in your setup file.')
            return

        # Connect MCTWidget signals      
        self._widget.mctStartButton.clicked.connect(self.startMCT)
        self._widget.mctStopButton.clicked.connect(self.stopMCT)
        self._widget.mctShowLastButton.clicked.connect(self.showLast)
        self._widget.mctInitFilterButton.clicked.connect(self.initFilter)

        self._widget.sigSliderLaser1ValueChanged.connect(self.valueLaser1Changed)
        self._widget.sigSliderLaser2ValueChanged.connect(self.valueLaser2Changed)
        self._widget.sigSliderLEDValueChanged.connect(self.valueLEDChanged)
    
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # select lasers
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        self.lasers = []
        self.leds = []
        for iDevice in allLaserNames:
            if iDevice.find("Laser")>=0:
                self.lasers.append(self._master.lasersManager[iDevice])
        self.leds = []
        for iDevice in allLaserNames:
            if iDevice.find("LED")>=0:
                self.leds.append(self._master.lasersManager[iDevice])
        
        self.illu = self._master.LEDMatrixsManager[self._master.LEDMatrixsManager.getAllDeviceNames()[0]]
        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

        self.isMCTrunning = False
        
    def initFilter(self):
        self._widget.setNImages("Initializing filter position...")
        self.lasers[0].initFilter()

    def startMCT(self):
        # initilaze setup
        self.nImages = 0
        self._widget.setNImages("Starting timelapse...")
        self.lasers[0].initFilter()

        # get parameters from GUI
        self.zStackMin, self.zStackax, self.zStackStep, self.zStackEnabled = self._widget.getZStackValues()
        self.timePeriod = self._widget.getTimelapseValues()
        self.MCTFilename = self._widget.getFilename()

        
        # initiliazing the update scheme for pulling pressure measurement values
        self.timer = Timer()
        self.timer.timeout.connect(self.takeTimelapse)
        self.timer.start(self.timePeriod*1000)
        self.startTime = ptime.time()
    
    def stopMCT(self):
        self.isMCTrunning = False
        
        self._widget.setNImages("Stopping timelapse...")

        try:
            del self.timer
        except:
            pass

        try:
            del self.MCTThread
        except:
            pass
        
        self._widget.setNImages("Done wit timelapse...")
    
    def showLast(self):
        pass
    
    def takeTimelapse(self):
        if not self.isMCTrunning:
            try:
                # make sure there is no exisiting thrad 
                del self.MCTThread
            except:
                pass

            # this should decouple the hardware-related actions from the GUI - but it doesn't 
            self.isMCTrunning = True
            self.MCTThread = threading.Thread(target=self.takeTimelapseThread, args=(), daemon=True)
            self.MCTThread.start()
        
    def takeTimelapseThread(self):
        self.__logger.debug("Take image")
        zstackParams = self._widget.getZStackValues()

        if self.Laser1Value>0:
            self.takeImageIllu(illuMode = "Laser1", intensity=self.Laser1Value, zstackParams=zstackParams)
        if self.Laser2Value>0:
            self.takeImageIllu(illuMode = "Laser2", intensity=self.Laser2Value, zstackParams=zstackParams)
        if self.LEDValue>0:
            self.takeImageIllu(illuMode = "Brightfield", intensity=self.LEDValue, zstackParams=zstackParams)
                
        self.nImages += 1
        self._widget.setNImages(self.nImages)

        self.isMCTrunning = False

    def takeImageIllu(self, illuMode, intensity, zstackParams=None):
        self._logger.debug("Take image:" + illuMode + str(intensity))
        fileExtension = 'tif'
        if illuMode == "Laser1":
            try:
                self.lasers[0].setValue(intensity)
                self.lasers[0].setEnabled(True)
            except:
                pass
        if illuMode == "Laser2":
            try:
                self.lasers[1].setValue(intensity)
                self.lasers[1].setEnabled(True)
            except:
                pass
        if illuMode == "Brightfield":
            try:
                if intensity > 255: intensity=255 
                if intensity < 0: intensity=0
                self.leds[0].setValue(intensity)
                self.leds[0].setEnabled(True)
                #self.illu.setAll((intensity,intensity,intensity))
                time.sleep(0.1)
            except:
                pass

        if zstackParams[-1]:
            # perform a z-stack
            stepsCounter = 0
            backlash=0
            self.stages.move(value=zstackParams[0], axis="Z", is_absolute=False, is_blocking=True)
            for iZ in np.arange(zstackParams[0], zstackParams[1], zstackParams[2]):
                stepsCounter += zstackParams[2]
                self.stages.move(value=zstackParams[2], axis="Z", is_absolute=False, is_blocking=True)
                filePath = self.getSaveFilePath(f'{self.MCTFilename}_N_{illuMode}_Z_{stepsCounter}.{fileExtension}')
                time.sleep(0.2) # unshake
                tif.imwrite(filePath, self.detector.getLatestFrame())
            self.stages.move(value=-(zstackParams[1]+backlash), axis="Z", is_absolute=False, is_blocking=True)
        else:
            filePath = self.getSaveFilePath(f'{self.MCTFilename}_{illuMode}.{fileExtension}')
            tif.imwrite(filePath, self.detector.getLatestFrame())

        # switch off all illu sources
        for lasers in self.lasers:
            lasers.setEnabled(False)
            self.lasers[1].setValue(0)
            time.sleep(0.1)
        try:
            self.illu.setAll((0,0,0))
        except:
            pass
        
            
    
    def valueLaser1Changed(self, value):
        self.Laser1Value= value
        #self.lasers[0].setEnabled(True)
        self.lasers[0].setValue(self.Laser1Value)

    def valueLaser2Changed(self, value):
        self.Laser2Value= value
        self.lasers[1].setValue(self.Laser2Value)

    def valueLEDChanged(self, value):
        self.LEDValue= value
        self.lasers[1].setValue(self.LEDValue)

                
    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()
 
 
    def getSaveFilePath(self, path, allowOverwriteDisk=False, allowOverwriteMem=False):
        dirPath  = os.path.join(dirtools.UserFileDirs.Root, 'recordings')
        newPath = os.path.join(dirPath,path)
        numExisting = 0

        def existsFunc(pathToCheck):
            if not allowOverwriteDisk and os.path.exists(pathToCheck):
                return True
            return False

        while existsFunc(newPath):
            numExisting += 1
            pathWithoutExt, pathExt = os.path.splitext(path)
            newPath = f'{pathWithoutExt}_{numExisting}{pathExt}'
        return newPath



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
