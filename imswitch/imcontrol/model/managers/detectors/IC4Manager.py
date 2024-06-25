from typing import Dict
import numpy as np

from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.managers.detectors.DetectorManager import DetectorParameter
from .DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter, DetectorListParameter


class IC4Manager(DetectorManager):
    """ DetectorManager that deals with TheImagingSource cameras and uses the IC4 backend.
    https://www.theimagingsource.com/en-us/documentation/ic4python/index.html

    Manager properties:

    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        self.__logger.debug("IC4Manager.__init__")
        self.__logger.debug(f"detectorInfo: {detectorInfo}")
        self.__logger.debug(f"serial_no: {detectorInfo.managerProperties['IC4']['serial_no']}")

        self._camera = self.getIC4obj(detectorInfo.managerProperties['IC4']['serial_no'])

        self._running = False

        fullShape = (self._camera.get_property('Width'),
                     self._camera.get_property('Height'))

        self.__logger.debug(f"fullShape: {fullShape}")

        self.crop(hpos=0, vpos=0, hsize=fullShape[0], vsize=fullShape[1])

        # Prepare parameters
        parameters = {
            'ExposureTime': DetectorNumberParameter(group='Misc', value=100, valueUnits='ms',
                                                    editable=True),
            'Gain': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.',
                                            editable=True),
            'AcquisitionFrameRate': DetectorNumberParameter(group='Misc', value=10, valueUnits='fps', editable=True),
            'TriggerMode': DetectorListParameter(group='Misc', value="Off", options=["On", "Off"], editable=True),
            # 0 for FrameStart, 1 for ExposureActive
            'TriggerSelector': DetectorListParameter(group='Misc', value='ExposureActive', options=['FrameStart', 'ExposureActive'], editable=True),
        }

        # get the pixel size
        pixel_size = DetectorNumberParameter(
            group='Misc', value=6.5, valueUnits='um', editable=True)

        # Prepare actions
        actions = {
            'More properties (crashing!)': DetectorAction(group='Misc',
                                                          func=self._camera.openPropertiesGUI)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=self._camera.model, parameters=parameters, actions=actions, croppable=True)

        # get the exposure time and AcquisitionFrameRate
        self.__logger.debug(f"ExposureTime: {self.getParameter('ExposureTime')}")
        self.__logger.debug(f"AcquisitionFrameRate: {self.getParameter('AcquisitionFrameRate')}")

    def setParameter(self, name: str, value):
        """ Set a parameter of the detector and returns the new value. """
        self.__logger.debug(f"IC4Manager.setParameter: {name} = {value}")

        super().setParameter(name, value)

        if name not in self._DetectorManager__parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        new_value = self._camera.set_property(name, value)

        if name == "TriggerMode":
            if value == "On":
                self.last_framerate = self._camera.get_property("AcquisitionFrameRate")
                self._camera.set_acq_frame_rate_to_max()
            else:
                self._camera.set_property("AcquisitionFrameRate", self.last_framerate)

        return new_value

    def getParameter(self, name: str):
        """ Get a parameter of the detector. """
        self.__logger.debug(f"IC4Manager.getParameter: {name}")

        # if name not in self._DetectorManager__parameters:
        #     raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self._camera.get_property(name)
        return value

    @property
    def pixelSizeUm(self):
        """ The pixel size in micrometers, in 3D, in the format
        ``[Z, Y, X]``. Non-scanned ``Z`` set to 1. """
        return [1, 1, 1]

    @property
    def scale(self):
        return [1, 1]

    def crop(self, hpos: int, vpos: int, hsize: int, vsize: int) -> None:
        """ Crop the frame read out by the detector. """
        pass

    def getLatestFrame(self) -> np.ndarray:
        """ Returns the frame that represents what the detector currently is
        capturing. The returned object is a numpy array of shape
        (height, width). """
        self.__logger.debug(f"IC4Manager.getLatestFrame with {self._camera.latest_frame.shape}")
        if self._running:
            return self._camera.get_latest_frame()

    def getChunk(self) -> np.ndarray:
        """ Returns the frames captured by the detector since getChunk was last
        called, or since the buffers were last flushed (whichever happened
        last). The returned object is a numpy array of shape
        (numFrames, height, width). """
        if self._camera.frame_queue is not None:
            self._camera.frame_queue.log_status()
            return self._camera.frame_queue.get_frames()
        else:
            return self._camera.get_latest_frame()[np.newaxis, :, :]

    def flushBuffers(self) -> None:
        """ Flushes the detector buffers so that getChunk starts at the last
        frame captured at the time that this function was called. """
        if self._camera.frame_queue is not None:
            self._camera.frame_queue.get_frames()
        else:
            pass

    def startAcquisition(self, whichAcquisition: str = 'continuous'):
        if not self._running:
            self.__logger.debug(f"Starting acquisition: {whichAcquisition}")
            if whichAcquisition == 'continuous':
                self._camera.setup_continuous_acquisition()
            elif whichAcquisition == 'single':
                self._camera.setup_single_acquisition()
            self._camera.start_acquisition()
            self._running = True

    def stopAcquisition(self) -> None:
        """ Stops image acquisition. """

        self.__logger.debug("Stopping acquisition")
        if self._running:
            self._running = False
            self._camera.stop_acquisition()

    def finalize(self) -> None:
        """ Close/cleanup detector. """
        self._camera.finalize()

    def getIC4obj(self, serialNo):
        """ Get the IC4 object. """

        from imswitch.imcontrol.model.interfaces.IC4Camera import IC4Camera
        camera = IC4Camera(serialNo)
        # except ImportError:
        #     self.__logger.warning(f'Failed to initialize IC4 camera {serialNo}, loading mocker')
        #     from imswitch.imcontrol.model.interfaces.tiscamera_mock import MockCameraTIS
        #     camera = MockCameraTIS()
        self.__logger.info(f'IC4 camera {camera.model} initialized')
        return camera


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
