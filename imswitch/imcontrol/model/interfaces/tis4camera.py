import numpy as np
import time

from imswitch.imcommon.model import initLogger
import imagingcontrol4 as ic4


class CameraTIS4:
    def __init__(self, cameraNo, pixel_format):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)
        ic4.Library.init(api_log_level=4, log_targets=1)
        self.pixel_formats = {'8bit': ic4.PixelFormat.Mono8,
                              '12bit': ic4.PixelFormat.Mono16,
                              '16bit': ic4.PixelFormat.Mono16}
        ic4.PropertyDialogFlags.ALLOW_STREAM_RESTART
        cam_names = ic4.DeviceEnum.devices()
        self.model = cam_names[cameraNo]
        self.cam = ic4.Grabber()
        self.sink = ic4.SnapSink()

        self.local_init(pixel_format)

    def local_init(self, value):
        self.__logger.info('local init, should run only once')
        if self.cam.is_device_open:
            reinit = True  # flag if pixel format needs to be set
            self.__logger.info('this is a RE-init')
            self.cam.device_close()
        else:
            reinit = False
        self.cam.device_open(self.model)

        # query exposure_time internal unit
        exp = self.cam.device_property_map.find_float(ic4.PropId.EXPOSURE_TIME)
        self.exposure_unit = exp.unit

        if self.exposure_unit == 'ns':
            self.exposure_conv_factor = 1e6
        elif self.exposure_unit == 'us':
            self.exposure_conv_factor = 1000
        elif self.exposure_unit == 'ms':
            self.exposure_conv_factor = 1
        elif self.exposure_unit == 's':
            self.exposure_conv_factor = 0.001
        else:
            self.__logger.warning('Unknown exposure time unit, assuming ms.')
            self.exposure_conv_factor = 1

        # set pixel format, not needed because it gets set in the manager
        if reinit:
            self.setPropertyValue('pixel_format', value)
        # set auto gain off
        self.cam.device_property_map.set_value(
            ic4.PropId.GAIN_AUTO, False
        )
        # set exposure time AUTO false
        self.cam.device_property_map.set_value(
            ic4.PropId.EXPOSURE_AUTO, False
        )
        # Defer acquisition means that, self.cam.start_acquisition needs to be called
        self.cam.stream_setup(self.sink,
                              setup_option=ic4.StreamSetupOption.DEFER_ACQUISITION_START,
                              )
        # print('grabber', self.cam, id(self.cam))
        # print('SINK', self.cam.sink, id(self.cam.sink))

    def start_live(self):
        # Defer acquisition means that, self.cam.start_acquisition needs to be called
        # self.cam.stream_setup(self.sink,
        #                       setup_option=ic4.StreamSetupOption.ACQUISITION_START,
        #                       )
        self.cam.acquisition_start()  # start imaging

    def stop_live(self):
        self.__logger.debug('stop live method called')
        self.cam.acquisition_stop()  # stop imaging

        # Bad attempt to fix RAM issues and stop stream every time
        # does not work and raised issue on is_streaming property bug.
        # self.cam.stream_stop()
        # time.sleep(0.4)
        # print('Streaming?', self.cam.is_streaming)
        # self.cam.stream_setup(self.sink,
        #                       setup_option=ic4.StreamSetupOption.DEFER_ACQUISITION_START,
        #                       )

    def grabFrame(self):
        image = self.sink.snap_single(10000)
        frame = image.numpy_wrap()[:, :, 0]

        # shift bits if necessary, works
        if self.pixel_format == '12bit':
            frame = frame >> 4

        # rotating frame, works, but not for saving snaps to h5
        if self.rotate_frame != 'No':
            frame = self.rotate(frame)
        return frame

    def rotate(self, arr):
        if self.rotate_frame == '90':
            return np.rot90(arr, k=1)
        elif self.rotate_frame == '180':
            return np.rot90(arr, k=2)
        elif self.rotate_frame == '270':
            return np.rot90(arr, k=3)
        else:
            return arr

    def setROI(self, hpos, vpos, hsize, vsize):
        "not implemented"
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 24)  # minimum ROI size
        pass

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.cam.device_property_map.set_value(
                                ic4.PropId.GAIN,
                                property_value)
        elif property_name == "exposure":
            # factor 1000 because camera in us
            self.cam.device_property_map.set_value(
                                ic4.PropId.EXPOSURE_TIME,
                                property_value*self.exposure_conv_factor)
        elif property_name == 'image_height':
            self.cam.device_property_map.set_value(
                                ic4.PropId.HEIGHT,
                                property_value)
        elif property_name == 'image_width':
            self.cam.device_property_map.set_value(
                                ic4.PropId.WIDTH,
                                property_value)
        elif property_name == 'pixel_format':
            self.cam.device_property_map.set_value(
                            ic4.PropId.PIXEL_FORMAT,
                            self.pixel_formats[property_value])
            self.pixel_format = property_value
        elif property_name == 'rotate_frame':
            self.rotate_frame = property_value
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.cam.device_property_map.get_value_float(
                                ic4.PropId.GAIN)
        elif property_name == "exposure":
            property_value = self.cam.device_property_map.get_value_float(
                                ic4.PropId.EXPOSURE_TIME) / self.exposure_conv_factor
        elif property_name == "image_width":
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.WIDTH)
        elif property_name == "image_height":
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.HEIGHT)
        elif property_name == 'pixel_format':
            return self.pixel_format
        elif property_name == 'rotate_frame':
            return self.rotate_frame
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        ic4.Dialogs.grabber_device_properties(self.cam, 43)


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
