import numpy as np

import imagingcontrol4 as ic4
from imswitch.imcommon.model import initLogger
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel

from time import time
ic4.Library.init()


class QueueListener_AutoPop(ic4.QueueSinkListener):
    prop_map: ic4.PropertyMap

    def __init__(self, prop_map: ic4.PropertyMap, camera=None):
        self.prop_map = prop_map

        self.__logger = initLogger(self, tryInheritParent=True)
        # self.__logger.debug("QueueListener_AutoPop.__init__")

        if camera is not None:
            self.camera = camera
            # self.__logger.debug(f"Camera: {self.camera}")

    def sink_connected(self, sink: ic4.QueueSink, image_type: ic4.ImageType, min_buffers_required: int) -> bool:
        # self.__logger.debug("calling sink connected")
        return True

    def frames_queued(self, sink: ic4.QueueSink):
        # # self.__logger.debug(64*"=")
        # self.__logger.debug("== there are frames in the queue!")
        try:
            buffer = sink.pop_output_buffer()
            image = buffer.numpy_copy()
            self.camera.latest_frame = image

        except ic4.IC4Exception as ex:
            self.__logger.error(
                f"Error trying to request ChunkExposuretime: {ex.code} ({ex.message})")

        # finally:
        #     # Disconnecting is not strictly necessary, but will release the buffer for reuse earlier
        #     self.prop_map.connect_chunkdata(None)
        # # self.__logger.debug(64*"=")

    def sink_disconnected(self, sink: ic4.QueueSink):
        # while there are frames in the queue, pop them
        # self.__logger.debug(
        # f"There are still {sink.queue_sizes().output_queue_length} frames in the queue.")
        while sink.queue_sizes().output_queue_length > 0:
            sink.pop_output_buffer()
        # self.__logger.debug("==Sink disconnected")


class QueueListener_QueuePop(ic4.QueueSinkListener):
    prop_map: ic4.PropertyMap

    def __init__(self, prop_map: ic4.PropertyMap, camera=None, max_queue_size=100):
        self.prop_map = prop_map

        self.__logger = initLogger(self, tryInheritParent=True)
        # self.__logger.debug("QueueListener_QueuePop.__init__")

        if camera is not None:
            self.camera = camera
            self.camera.frame_queue = FrameQueue(
                (self.camera.height, self.camera.width), max_queue_size)
            # self.__logger.debug(f"Camera: {self.camera}")

    def sink_connected(self, sink: ic4.QueueSink, image_type: ic4.ImageType, min_buffers_required: int) -> bool:
        # self.__logger.debug("calling sink connected")
        return True

    def frames_queued(self, sink: ic4.QueueSink):
        # # self.__logger.debug(64*"=")
        # self.__logger.debug("== there are frames in the queue!")
        try:
            buffer = sink.pop_output_buffer()
            image = buffer.numpy_copy()[:, :, 0]
            self.camera.frame_queue.add_frame(image)

        except ic4.IC4Exception as ex:
            self.__logger.error(
                f"Error trying to request ChunkExposuretime: {ex.code} ({ex.message})")

        # finally:
        #     # Disconnecting is not strictly necessary, but will release the buffer for reuse earlier
        #     self.prop_map.connect_chunkdata(None)
        # # self.__logger.debug(64*"=")

    def sink_disconnected(self, sink: ic4.QueueSink):
        # while there are frames in the queue, pop them
        # self.camera.frame_queue.get_timer_report()
        # self.__logger.debug(
        # f"There are still {sink.queue_sizes().output_queue_length} frames in the queue.")
        while sink.queue_sizes().output_queue_length > 0:
            buffer = sink.pop_output_buffer()
            image = buffer.numpy_copy()
            self.camera.frame_queue.add_frame(image)
        # self.__logger.debug("== Sink disconnected")


class IC4Camera:
    def __init__(self, serial_number=None):
        self.__logger = initLogger(self, tryInheritParent=True)
        # self.__logger.debug("IC4camera.__init__")

        self._get_grabber(serial_number)

        # set camera to defalut
        self.grabber.device_property_map.set_value(ic4.PropId.USER_SET_SELECTOR, "Default")

        # Configure the device to output images in the Mono16 pixel format
        self.grabber.device_property_map.set_value(ic4.PropId.PIXEL_FORMAT, ic4.PixelFormat.Mono16)

        # get the width and height of the image
        self.width = self.get_property('Width')
        self.height = self.get_property('Height')

        self.grabber.device_property_map.set_value(ic4.PropId.EXPOSURE_AUTO, "Off")
        self.grabber.device_property_map.set_value(ic4.PropId.EXPOSURE_TIME, 100.0)

        # set framerate to 10fps
        self.grabber.device_property_map.set_value(ic4.PropId.ACQUISITION_FRAME_RATE, 10.0)

        self.latest_frame = np.zeros((self.height, self.width), dtype=np.uint16)

    def _get_grabber(self, serial_number):
        self.grabber = ic4.Grabber()

        # self.__logger.debug(f"Available devices: {ic4.DeviceEnum.devices()}")

        for device_info in ic4.DeviceEnum.devices():
            if device_info.serial == serial_number:
                self.model = device_info.model_name
                self.grabber.device_open(device_info)

    def get_property(self, property_name):
        return self.grabber.device_property_map.find(property_name).value

    def set_property(self, property_name, value):
        if property_name != "TriggerSelector":
            self.grabber.device_property_map.find(property_name).value = value
        elif property_name == "TriggerSelector":
            if value == "FrameStart":
                self.grabber.device_property_map.find(ic4.PropId.TRIGGER_SELECTOR).int_value = 0
            else:
                self.grabber.device_property_map.find(ic4.PropId.TRIGGER_SELECTOR).int_value = 1

    def set_acq_frame_rate_to_max(self):
        # get max frame rate
        max_frame_rate = self.grabber.device_property_map.find(
            ic4.PropId.ACQUISITION_FRAME_RATE).maximum
        self.grabber.device_property_map.set_value(
            ic4.PropId.ACQUISITION_FRAME_RATE, max_frame_rate)
        # self.__logger.debug(f"Max frame rate: {max_frame_rate}")

    def openPropertiesGUI(self):
        class PropertiesDialog(QDialog):
            def __init__(self, parent=None):
                super(PropertiesDialog, self).__init__(parent)
                self.setWindowTitle("Camera Properties")
                self.setGeometry(100, 100, 400, 300)

                label = QLabel("Camera properties go here", self)
                label.move(20, 20)

                # # Get the window handle
                # window_handle = self.winId()

                # # Pass the window handle to the ic4 method
                # self.grabber.device_property_map.set_value(ic4.PropId.WINDOW_HANDLE, window_handle)
        def __init__(self, parent=None):
            super(PropertiesDialog, self).__init__(parent)
            self.setWindowTitle("Camera Properties")
            self.setGeometry(100, 100, 400, 300)

            label = QLabel("Camera properties go here", self)
            label.move(20, 20)
        app = QApplication(sys.argv)
        dialog = PropertiesDialog()
        ic4.Dialogs.grabber_device_properties(self.grabber, dialog.winId())
        # dialog.exec_()
        # sys.exit(app.exec_())

    def finalize(self):
        # check whether cam is streaming
        if self.grabber.is_streaming:
            self.grabber.stream_stop()
        self.grabber.device_close()

    def setup_live_acquisition(self, max_queue_size=10):
        # # self.__logger.debug("Setting up the stream!")
        prop_map = self.grabber.device_property_map
        self.queue_listener = QueueListener_AutoPop(prop_map, self)
        self.sink = ic4.QueueSink(self.queue_listener, max_output_buffers=max_queue_size)
        # self.__logger.debug(f"Sink: {self.sink}")
        self.grabber.stream_setup(self.sink, setup_option=ic4.StreamSetupOption.ACQUISITION_START)

        # self.grabber.stream_setup(queue_sink, setup_option=ic4.StreamSetupOption.DEFER_ACQUISITION_START)

    def setup_continuous_acquisition(self, max_queue_size=100):
        # self.__logger.debug("Setting up the stream!")
        prop_map = self.grabber.device_property_map
        self.queue_listener = QueueListener_QueuePop(prop_map, self, max_queue_size)
        self.sink = ic4.QueueSink(self.queue_listener, max_output_buffers=30)
        # self.__logger.debug(f"Sink: {self.sink}")
        self.grabber.stream_setup(self.sink, setup_option=ic4.StreamSetupOption.ACQUISITION_START)

    def get_latest_frame(self):
        # self.frame_queue.log_status()
        return self.frame_queue.get_latest_and_clear()

    def setup_single_acquisition(self):
        pass

    def start_acquisition(self):
        # self.__logger.debug("Starting the stream!")
        # self.__logger.debug(f"Sink: {self.sink}")
        # self.__logger.debug(f"Queue_listener: {self.queue_listener}")
        pass

    def stop_acquisition(self):
        # self.__logger.debug("Stopping the stream!")
        # self.__logger.debug(f"Sink: {self.sink}")
        # self.__logger.debug(f"Queue_listener: {self.queue_listener}")
        self.grabber.stream_stop()

    def get_property(self, property_name):
        return self.grabber.device_property_map.find(property_name).value


class FrameQueue:
    def __init__(self, frame_shape, max_size=100):
        self.__frame_shape = frame_shape
        self.__max_size = max_size
        self.__queue = np.zeros((max_size, *frame_shape), dtype=np.uint16)
        self.__queue_pointer = 0
        self.overrun = False

        # init logger
        self.__logger = initLogger(self, tryInheritParent=True)

    def add_frame(self, frame):
        self.__queue[self.__queue_pointer] = frame
        self.__queue_pointer += 1
        if self.__queue_pointer == self.__max_size:
            self.__queue_pointer = 0
            self.overrun = True
            self.__logger.warning("FrameQueue is full. Overwriting oldest frame.")

    def get_frames(self):
        t_start = time()
        if self.overrun:
            frames = self.__queue
            frames[0:self.__queue_pointer] = self.__queue[self.__max_size - self.__queue_pointer:]
            frames[self.__queue_pointer:] = self.__queue[:self.__queue_pointer]
        else:
            frames = self.__queue[:self.__queue_pointer]
        self.__queue_pointer = 0
        self.__queue = np.zeros((self.__max_size, *self.__frame_shape), dtype=np.uint16)
        # self.__logger.debug(f"Getting frames took {time()-t_start} seconds")
        return frames

    def get_latest(self):
        self.__queue_pointer -= 1
        return self.__queue[self.__queue_pointer, :, :]

    def get_latest_and_clear(self):
        frame = self.get_latest()
        self.clear()
        return frame

    def log_status(self):
        width = 30  # width of the progress bar
        progress = int(self.__queue_pointer / self.__max_size * width)
        # self.__logger.debug(
        # f"FrameQueue status: [{'='*progress}{' '*(width-progress)}] {self.__queue_pointer}/{self.__max_size}")

    def clear(self):
        self.__queue_pointer = 0
        self.__queue = np.zeros((self.__max_size, *self.__frame_shape), dtype=np.uint16)
        self.overrun = False
