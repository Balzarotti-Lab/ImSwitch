from imswitch.imcommon.model import VFileItem, initLogger

import pkg_resources
        
from imswitch.imcontrol.model import (
    DetectorsManager, LasersManager, MultiManager, PositionersManager,
    RecordingManager, RS232sManager, SLMManager, SIMManager, DPCManager, LEDMatrixsManager, MCTManager, ROIScanManager, MockXXManager, WebRTCManager, HyphaManager,
    ISMManager, UC2ConfigManager, AutofocusManager, HistoScanManager, PixelCalibrationManager, LightsheetManager, NidaqManager, FOVLockManager,
    StandManager, RotatorsManager, JetsonNanoManager, LEDsManager, ScanManagerBase, ScanManagerPointScan, ScanManagerMoNaLISA, FlatfieldManager, 
    FlowStopManager
)


class MasterController:
    """
    This class will handle the communication between software and hardware,
    using the managers for each hardware set.
    """

    def __init__(self, setupInfo, commChannel, moduleCommChannel):
        self.__logger = initLogger(self)
        self.__setupInfo = setupInfo
        self.__commChannel = commChannel
        self.__moduleCommChannel = moduleCommChannel

        # Init managers
        self.rs232sManager = RS232sManager(self.__setupInfo.rs232devices)

        lowLevelManagers = {
            'rs232sManager': self.rs232sManager
        }

        self.detectorsManager = DetectorsManager(self.__setupInfo.detectors,
                                                 updatePeriod=100,
                                                 **lowLevelManagers)
        self.lasersManager = LasersManager(self.__setupInfo.lasers,
                                           **lowLevelManagers)
        self.positionersManager = PositionersManager(self.__setupInfo.positioners,
                                                     self.__commChannel,
                                                     **lowLevelManagers)
        self.LEDMatrixsManager = LEDMatrixsManager(self.__setupInfo.LEDMatrixs,
                                           **lowLevelManagers)
        self.rotatorsManager = RotatorsManager(self.__setupInfo.rotators,
                                            **lowLevelManagers)

        self.LEDsManager = LEDsManager(self.__setupInfo.LEDs)
        #self.scanManager = ScanManager(self.__setupInfo)
        self.recordingManager = RecordingManager(self.detectorsManager)
        self.slmManager = SLMManager(self.__setupInfo.slm)
        self.UC2ConfigManager = UC2ConfigManager(self.__setupInfo.uc2Config, lowLevelManagers)
        self.simManager = SIMManager(self.__setupInfo.sim)
        self.dpcManager = DPCManager(self.__setupInfo.dpc)
        self.mctManager = MCTManager(self.__setupInfo.mct)
        self.nidaqManager = NidaqManager(self.__setupInfo.nidaq)
        self.roiscanManager = ROIScanManager(self.__setupInfo.roiscan)
        self.lightsheetManager = LightsheetManager(self.__setupInfo.lightsheet)
        self.webrtcManager = WebRTCManager(self.__setupInfo.webrtc)
        self.hyphaManager = HyphaManager(self.__setupInfo.hypha)
        self.MockXXManager = MockXXManager(self.__setupInfo.mockxx)
        self.jetsonnanoManager = JetsonNanoManager(self.__setupInfo.jetsonnano)
        self.HistoScanManager = HistoScanManager(self.__setupInfo.HistoScan)
        self.FlowStopManager = FlowStopManager(self.__setupInfo.FlowStop)
        self.FlatfieldManager = FlatfieldManager(self.__setupInfo.Flatfield)
        self.PixelCalibrationManager = PixelCalibrationManager(self.__setupInfo.PixelCalibration)
        self.AutoFocusManager = AutofocusManager(self.__setupInfo.autofocus)
        self.FOVLockManager = FOVLockManager(self.__setupInfo.fovLock)
        self.ismManager = ISMManager(self.__setupInfo.ism)
        # load all implugin-related managers and add them to the class
        # try to get it from the plugins
        # If there is a imswitch_sim_manager, we want to add this as self.imswitch_sim_widget to the 
        # MasterController Class
        try:
            for entry_point in pkg_resources.iter_entry_points(f'imswitch.implugins'):
                if entry_point.name.find("manager")>=0:
                    ManagerClass = entry_point.load()  # Load the manager class
                    self.__setupInfo.add_attribute(attr_name=entry_point.name.split("_manager")[0], attr_value={})
                    manager_setup_info = getattr(self.__setupInfo, entry_point.name.split("_manager")[0], None)
                    
                    # get info from user config dict
                    # sideload the simInfo from the user config dict
                    moduleInfo_dict = self.__setupInfo._catchAll[entry_point.name.split("_manager")[0]]
                    class ModuleInfoClass:
                        def __init__(self, dictionary):
                            for key, value in dictionary.items():
                                setattr(self, key, value)
                    moduleInfo = ModuleInfoClass(moduleInfo_dict) # assign class structure
                    
                    manager = ManagerClass(moduleInfo)  # Initialize the manager
                    setattr(self, entry_point.name, manager)  # Add the manager to the class
        except Exception as e:
            self.__logger.error(e)
            
        if self.__setupInfo.microscopeStand:
            self.standManager = StandManager(self.__setupInfo.microscopeStand,
                                             **lowLevelManagers)

        # Generate scanManager type according to setupInfo
        if self.__setupInfo.scan:
            if self.__setupInfo.scan.scanWidgetType == "PointScan":
                self.scanManager = ScanManagerPointScan(self.__setupInfo)
            elif self.__setupInfo.scan.scanWidgetType == "Base":
                self.scanManager = ScanManagerBase(self.__setupInfo)
            elif self.__setupInfo.scan.scanWidgetType == "MoNaLISA":
                self.scanManager = ScanManagerMoNaLISA(self.__setupInfo)
            else:
                self.__logger.error(
                    'ScanWidgetType in SetupInfo["scan"] not recognized, choose one of the following:'
                    ' ["Base", "PointScan", "MoNaLISA"].'
                )
                return

        # Connect signals
        cc = self.__commChannel

        self.detectorsManager.sigAcquisitionStarted.connect(cc.sigAcquisitionStarted)
        self.detectorsManager.sigAcquisitionStopped.connect(cc.sigAcquisitionStopped)
        self.detectorsManager.sigLiveStarted.connect(cc.sigLiveStarted)
        self.detectorsManager.sigLiveStopped.connect(cc.sigLiveStopped)
        self.detectorsManager.sigDetectorSwitched.connect(cc.sigDetectorSwitched)
        self.detectorsManager.sigImageUpdated.connect(cc.sigUpdateImage)
        self.detectorsManager.sigNewFrame.connect(cc.sigNewFrame)

        self.recordingManager.sigRecordingStarted.connect(cc.sigRecordingStarted)
        self.recordingManager.sigRecordingEnded.connect(cc.sigRecordingEnded)
        self.recordingManager.sigRecordingFrameNumUpdated.connect(cc.sigUpdateRecFrameNum)
        self.recordingManager.sigRecordingTimeUpdated.connect(cc.sigUpdateRecTime)
        self.recordingManager.sigMemorySnapAvailable.connect(cc.sigMemorySnapAvailable)
        self.recordingManager.sigMemoryRecordingAvailable.connect(cc.sigMemoryRecordingAvailable)

        self.recordingManager.sigMemoryRecordingAvailable.connect(self.memoryRecordingAvailable) 
            
        self.slmManager.sigSLMMaskUpdated.connect(cc.sigSLMMaskUpdated)

        self.rotatorsManager.sigRotatorPositionUpdated.connect(cc.sigRotatorPositionUpdated)

    def memoryRecordingAvailable(self, name, file, filePath, savedToDisk):
        self.__moduleCommChannel.memoryRecordings[name] = VFileItem(
            data=file, filePath=filePath, savedToDisk=savedToDisk
        )

    def closeEvent(self):
        self.recordingManager.endRecording(emitSignal=False, wait=True)

        for attrName in dir(self):
            attr = getattr(self, attrName)
            if isinstance(attr, MultiManager):
                attr.finalize()


# Copyright (C) 2020-2023 ImSwitch developers
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
