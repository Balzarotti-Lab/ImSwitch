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

        # get the width and height of the image
        self.width = self.get_property('Width')
        self.height = self.get_property('Height')

        self.grabber.device_property_map.set_value(ic4.PropId.EXPOSURE_TIME, 100.0)

        # set framerate to 10fps
        self.grabber.device_property_map.set_value(ic4.PropId.ACQUISITION_FRAME_RATE, 10.0)

        self.latest_frame = np.zeros((self.height, self.width), dtype=np.uint16)

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

    def setup_continuous_acquisition(self, max_queue_size=5):
        self.__logger.debug("Setting up the stream!")
        prop_map = self.grabber.device_property_map
        self.queue_listener = QueueListener(prop_map)
        self.sink = ic4.QueueSink(self.queue_listener, max_output_buffers=4)
        self.__logger.debug(f"Sink: {self.sink}")
        self.grabber.stream_setup(self.sink, setup_option=ic4.StreamSetupOption.ACQUISITION_START)

        # self.grabber.stream_setup(queue_sink, setup_option=ic4.StreamSetupOption.DEFER_ACQUISITION_START)

    def setup_single_acquisition(self):
        pass

    def start_acquisition(self):
        self.__logger.debug("Starting the stream!")
        self.__logger.debug(f"Sink: {self.sink}")

    def stop_acquisition(self):
        self.grabber.stream_stop()

    def get_property(self, property_name):
        return self.grabber.device_property_map.find(property_name).value


class QueueListener(ic4.QueueSinkListener):
    prop_map: ic4.PropertyMap

    def __init__(self, prop_map: ic4.PropertyMap):
        self.prop_map = prop_map

        self.__logger = initLogger(self, tryInheritParent=True)

        self.__logger.debug("QueueListener.__init__")

    def sink_connected(self, sink: ic4.QueueSink, image_type: ic4.ImageType, min_buffers_required: int) -> bool:
        return True

    def frames_queued(self, sink: ic4.QueueSink):
        self.__logger.debug("there are frames in the queue!")
        try:
            buffer = sink.pop_output_buffer()
            image = buffer.numpy_wrap()

        except ic4.IC4Exception as ex:
            self.__logger.error(f"Error trying to request ChunkExposuretime: {ex.code} ({ex.message})")

        finally:
            # Disconnecting is not strictly necessary, but will release the buffer for reuse earlier
            self.prop_map.connect_chunkdata(None)


    def sink_disconnected(self, sink: ic4.QueueSink):
        self.__logger.debug("Sink disconnected")
        pass