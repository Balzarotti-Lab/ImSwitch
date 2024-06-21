import numpy as np

import imagingcontrol4 as ic4
from imswitch.imcommon.model import initLogger


class IC4Camera:
    def __init__(self, serial_number=None):


        self.__logger = initLogger(self, tryInheritParent=True)

        self.__logger.debug("IC4camera.__init__")
        ic4.Library.init()

        self.grabber, self.model = self.get_grabber(serial_number)

        # Configure the device to output images in the Mono16 pixel format
        self.grabber.device_property_map.set_value(ic4.PropId.PIXEL_FORMAT, ic4.PixelFormat.Mono16)


    def get_grabber(self, serial_number):
        grabber = ic4.Grabber()

        self.__logger.debug(f"Available devices: {ic4.DeviceEnum.devices()}")

        for device_info in ic4.DeviceEnum.devices():
            if device_info.serial == serial_number:
                model = device_info.model_name
                grabber.device_open(device_info)
                return grabber, model

    def get_property(self, property_name):
        return self.grabber.device_property_map.find(property_name).value

    def set_property(self, property_name, value):
        self.grabber.device_property_map.find(property_name).value = value

    def openPropertiesGUI(self):
        # ic4.Dialogs.grabber_device_properties(self.grabber)
        pass

    def finalize(self):
        # check whether cam is streaming
        if self.grabber.is_streaming():
            self.grabber.stream_stop()
        self.grabber.device_close()
        ic4.Library.exit()

