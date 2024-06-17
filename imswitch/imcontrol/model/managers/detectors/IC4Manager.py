import numpy as np

from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter

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

        fullShape = (self._camera.get_property('Width'),
                     self._camera.get_property('Height'))

        self.__logger.debug(f"fullShape: {fullShape}")

        self.crop(hpos=0, vpos=0, hsize=fullShape[0], vsize=fullShape[1])

        # Prepare parameters
        parameters = {
            'exposure': DetectorNumberParameter(group='Misc', value=100, valueUnits='ms',
                                                editable=True),
            'gain': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.',
                                            editable=True),
            'brightness': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.',
                                                  editable=True),
            'frame_rate': DetectorNumberParameter(group='Misc', value=10, valueUnits='fps', editable=True),
        }

                # Prepare actions
        actions = {
            'More properties': DetectorAction(group='Misc',
                                              func=self._camera.openPropertiesGUI)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                    model=self._camera.model, parameters=parameters, actions=actions, croppable=True)

    def pixelSizeUm(self):
        """ The pixel size in micrometers, in 3D, in the format
        ``[Z, Y, X]``. Non-scanned ``Z`` set to 1. """
        pass

    def crop(self, hpos: int, vpos: int, hsize: int, vsize: int) -> None:
        """ Crop the frame read out by the detector. """
        pass

    def getLatestFrame(self) -> np.ndarray:
        """ Returns the frame that represents what the detector currently is
        capturing. The returned object is a numpy array of shape
        (height, width). """
        pass

    def getChunk(self) -> np.ndarray:
        """ Returns the frames captured by the detector since getChunk was last
        called, or since the buffers were last flushed (whichever happened
        last). The returned object is a numpy array of shape
        (numFrames, height, width). """
        pass

    def flushBuffers(self) -> None:
        """ Flushes the detector buffers so that getChunk starts at the last
        frame captured at the time that this function was called. """
        pass

    def startAcquisition(self) -> None:
        """ Starts image acquisition. """
        pass

    def stopAcquisition(self) -> None:
        """ Stops image acquisition. """
        pass

    def finalize(self) -> None:
        """ Close/cleanup detector. """
        pass

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
