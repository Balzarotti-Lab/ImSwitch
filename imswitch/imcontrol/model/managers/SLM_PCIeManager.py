import enum
import glob
import math
import os
import time
from time import perf_counter

import numpy as np
from PIL import Image
from scipy import signal as sg
import h5py
from datetime import datetime


from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger

# myAdd
from ctypes import *
from imswitch.imcommon.model.dirtools import _baseDataFilesDir


# Basic parameters for calling Create_SDK
bit_depth = c_uint(12)
num_boards_found = c_uint(0)
constructed_okay = c_uint(-1)
is_nematic_type = c_bool(1)
RAM_write_enable = c_bool(1)
use_GPU = c_bool(1)
max_transients = c_uint(20)
board_number = c_uint(1)
wait_For_Trigger = c_uint(0)
flip_immediate = c_uint(0)  # only supported on the 1024
timeout_ms = c_uint(5000)

# Both pulse options can be false, but only one can be true. You either generate a pulse when the new image begins loading to the SLM
# or every 1.184 ms on SLM refresh boundaries, or if both are false no output pulse is generated.
OutputPulseImageFlip = c_uint(0)
OutputPulseImageRefresh = c_uint(0)  # only supported on 1920x1152, FW rev 1.8.

# ---------------------------------------------------------------


class SLM_PCIeManager(SignalInterface):
    sigSLMMaskUpdated = Signal(object)  # (maskCombined)

    def __init__(self, slm_PCIeInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.__logger.info("SLM PCIe Manager initializing")
        self.__logger.debug(f"SLM PCIe Info: {slm_PCIeInfo}")

        if slm_PCIeInfo is None:
            return

        self.__slm_PCIeInfo = slm_PCIeInfo
        self.__wavelength = self.__slm_PCIeInfo.wavelength
        self.__pixelsize = self.__slm_PCIeInfo.pixelSize
        self.__slmSize = (self.__slm_PCIeInfo.width, self.__slm_PCIeInfo.height)
        self.__correctionPatternsDir = self.__slm_PCIeInfo.correctionPatternsDir

        # Load the DLL with the SLM controller
        cdll.LoadLibrary(_baseDataFilesDir + "\\libs\\slm_PCIe\\Blink_C_wrapper")
        self.slm_lib = CDLL("Blink_C_wrapper")

        cdll.LoadLibrary(_baseDataFilesDir + "\\libs\\slm_PCIe\\ImageGen")
        self.deleteLaterimage_lib = CDLL("ImageGen")

        # create the masks for left and right side of the SLM
        self.__maskLeft = Mask(self.__slmSize[1], int(self.__slmSize[0] / 2), self.__wavelength)
        self.__maskRight = Mask(self.__slmSize[1], int(self.__slmSize[0] / 2), self.__wavelength)
        self.__masks = [self.__maskLeft, self.__maskRight]

# myAdd
        # SLM controller initialization
        self.constructed_okay = False
        self.init_SLMController()
        self.img_bit_depth = 8
# ------------------------------------------------

        # tilt and aberration masks
        # self.initCorrectionMask()
        self.__logger.debug("Init tilt mask")
        self.initTiltMask()
        self.__logger.debug("Init aberration mask")
        self.initAberrationMask()
        self.__logger.debug("Init scan mask")
        self.initScanMask()
        self.__logger.debug("Masks in the __init__ method initialized")

        self.__masksAber = [self.__maskAberLeft, self.__maskAberRight]
        self.__masksTilt = [self.__maskTiltLeft, self.__maskTiltRight]
        self.__masksScan = [self.__maskScanLeft, self.__maskScanRight]

        self.update(maskChange=True, tiltChange=True, aberChange=True)

        # angles = np.linspace(0, 0.2, 10)
        # self.scan_stack = self.create_scan_stack(angles, scan_part=0)

# myAdd

    def init_SLMController(self):

        # constatns for Create_SDK
        self.bit_depth = c_uint(12)
        num_boards_found = c_uint(0)
        constructed_okay = c_uint(-1)
        is_nematic_type = c_bool(1)
        RAM_write_enable = c_bool(1)
        self.use_GPU = c_bool(1)
        self.max_transients = c_uint(20)
        self.board_number = c_uint(1)
        self.wait_For_Trigger = c_uint(0)
        self.flip_immediate = c_uint(0)  # only supported on the 1024
        self.timeout_ms = c_uint(500)

        self.OutputPulseImageFlip = c_uint(0)
        self.OutputPulseImageRefresh = c_uint(0)  # only supported on 1920x1152, FW rev 1.8.

        self.slm_lib.Create_SDK(self.bit_depth, byref(num_boards_found), byref(constructed_okay),
                                is_nematic_type, RAM_write_enable, self.use_GPU, self.max_transients, 0)

        if not constructed_okay.value == 0:
            self.constructed_okay = True

        if self.constructed_okay:
            if num_boards_found.value == 1:
                self.__logger.info("Blink SDK was successfully constructed")
                self.__logger.info(f"Found {num_boards_found.value} SLM controller(s)")

                self.board_number = c_uint(1)
                self.height_ = c_uint(self.slm_lib.Get_image_height(self.board_number))
                self.width_ = c_uint(self.slm_lib.Get_image_width(self.board_number))
                self.depth_ = c_uint(self.slm_lib.Get_image_depth(
                    self.board_number))  # Bits per pixel
                self.bytes = c_uint(self.depth_.value//8)
                self.center_x = c_uint(self.width_.value//2)
                self.center_y = c_uint(self.height_.value//2)
                self.__logger.debug(f"SLM image size: {self.width_.value}x{self.height_.value}")
                self.__logger.debug(f"SLM image depth: {self.depth_.value} bits")
                self.__logger.debug(f"SLM image bytes: {self.bytes.value}")
                self.__logger.debug(f"SLM center: {self.center_x.value}, {self.center_y.value}")

                # load the LUT
                self.slm_lib.Load_LUT_file(self.board_number, self.__slm_PCIeInfo.LUTfile)

                # TODO load the wFC
                self.WFCarray = np.zeros([self.width_.value*self.height_.value], np.uint8, 'C')

                # Create a vector to hold values for a SLM image
                self.blank_img = np.zeros(
                    [self.width_.value*self.height_.value*self.bytes.value], np.uint8, 'C')

                # Writes a blank pattern to the SLM
                retVal = self.slm_lib.Write_image(self.board_number, self.blank_img.ctypes.data_as(POINTER(c_ubyte)),
                                                  self.height_.value*self.width_.value*self.bytes.value, self.wait_For_Trigger,
                                                  self.flip_immediate, self.OutputPulseImageFlip, self.OutputPulseImageRefresh, self.timeout_ms)
                if (retVal == -1):
                    self.__logger.error("Upload/Communication to SLM failed")
                    self.slm_lib.Delete_SDK()
            else:
                self.__logger.error("Board number is not equal to 1 ")
                self.slm_lib.Delete_SDK()
        else:
            self.__logger.error("Blink SDK did not construct successfully")
            self.slm_lib.Delete_SDK()

    def create_scan_stack(self, scan_angles, scan_part=0, save_stack = True):
        self.maskDouble = self.__masks[0].concat(self.__masks[1])
        self.maskTilt = self.__masksTilt[0].concat(self.__masksTilt[1])
        self.maskAber = self.__masksAber[0].concat(self.__masksAber[1])
        self.maskCombined = self.maskDouble + self.maskAber + self.maskTilt

        scan_stack = np.zeros((len(scan_angles), self.height_.value,
                              self.width_.value), dtype=np.uint8)

        if scan_part == 0:
            for idx, scan_angle in enumerate(scan_angles):
                self.__maskScanLeft.setTiltAngle(scan_angle, 1)
                self.__maskScanLeft.setTilt(self.__pixelsize)
                self.maskScan = self.__maskScanLeft.concat(self.__maskScanRight)
                self.maskCombined = self.maskCombined + self.maskScan
                scan_stack[idx] = self.maskCombined.image()
        elif scan_part == 1:
            for idx, scan_angle in enumerate(scan_angles):
                self.__maskScanRight.setTiltAngle(scan_angle, 1)
                self.maskScan = self.__maskScanLeft.concat(self.__maskScanRight)
                self.maskCombined = self.maskCombined + self.maskScan
                scan_stack[idx] = self.maskCombined.image()
        self.__logger.debug(f"Scan stack created with shape: {scan_stack.shape}")
        if save_stack:
            with h5py.File("scan_stack.h5", "w") as f:
                date_time = datetime.now().strftime("%Y%m%d-%H%M%S")
                dataset_name = f"scan_stack_{date_time}"
                f.create_dataset(dataset_name, data=scan_stack)
        return scan_stack

    def upload_stack(self, stack, trigger=False, time_interval=10):
        """Uploads a stack of images to the SLM with a time interval between each image

        Args:
            stack (np.array): 3D array containing the images to be uploaded
            time_interval (int, optional): Time interval between each image in ms. Defaults to 10.

        """
        self.__logger.debug("Uploading stack")
        self.__logger.debug(f"Stack shape: {stack.shape}")

        if trigger:
            self.wait_For_Trigger = c_uint(1)
        else:
            self.wait_For_Trigger = c_uint(0)

        # check the stack is the right size
        if stack.shape[1] != self.height_.value or stack.shape[2] != self.width_.value:
            self.__logger.error("Stack is not the right size")
            return
        elif stack.shape[0] > 752:
            # check that the length is smaller than 752
            self.__logger.error("Stack is too long")
            return
        else:
            list_len = c_uint(stack.shape[0])
            self.stack_length = int(stack.shape[0])
            st = stack.flatten()
            retVal = self.slm_lib.Load_sequence(self.board_number, st.ctypes.data_as(POINTER(c_ubyte)), self.height_.value*self.width_.value * self.bytes.value, list_len, self.flip_immediate, self.OutputPulseImageFlip, self.OutputPulseImageRefresh, self.timeout_ms)
            self.stackUploaded = True


        self.wait_For_Trigger = c_uint(0)

    def upload_img(self, arr):
        # arr = arr[:, :, 0]              # takes just the first entry (R) of RGB
        arr = arr.flatten()
        if self.constructed_okay:
            retVal = self.slm_lib.Write_image(self.board_number, arr.ctypes.data_as(POINTER(c_ubyte)),
                                              self.height_.value*self.width_.value*self.bytes.value, self.wait_For_Trigger,
                                              self.flip_immediate, self.OutputPulseImageFlip, self.OutputPulseImageRefresh, self.timeout_ms)

            if (retVal == -1):
                self.__logger.error("Upload/Communication to SLM failed. Deleting SDK")
                self.slm_lib.Delete_SDK()
            else:
                self.__logger.debug("Uploading")
                # check the buffer is ready to receive the next image
                retVal = self.slm_lib.ImageWriteComplete(self.board_number, self.timeout_ms)
                if (retVal == -1):
                    self.__logger.error("ImageWriteComplete failed, trigger never received?")
                    self.slm_lib.Delete_SDK()

    def iterate_scan_stack(self, trigger=0):
        self.__logger.debug("Iterating through scan stack")
        if self.stackUploaded:
            if trigger==1:
                timeout_ms = c_uint(500)
            else:
                timeout_ms = self.timeout_ms
            trigger = c_uint(trigger)
            for idx in range(self.stack_length):
                strart = perf_counter()
                retVal = self.slm_lib.Select_image(self.board_number, c_uint(idx), trigger, self.flip_immediate, self.OutputPulseImageFlip, self.OutputPulseImageRefresh, timeout_ms)
                # self.__logger.debug(f"Selecting image {idx}")
                img_selected = perf_counter()
                if (retVal == -1):
                    self.__logger.debug(f"Execution of Select_image took {1e3*(img_selected-strart):.3f} ms")
                    self.__logger.error("Select_image failed")
                else:
                    retVal = self.slm_lib.ImageWriteComplete(self.board_number, self.timeout_ms)
                    img_written = perf_counter()
                    self.__logger.debug(f"Execution of image selection took {1e3*(img_written-strart):.3f} ms")
                    self.__logger.debug(f"The whole process took {1e3*(img_written-strart):.3f} ms")
                    if (retVal == -1):
                        self.__logger.error("ImageWriteComplete failed")
                # sleep for 0.5 s
                # time.sleep(0.5)
        else:
            self.__logger.error("No stack uploaded")

    def closeEvent(self):
        slm_lib.Write_image(self.board_number, self.blank_img.ctypes.data_as(POINTER(c_ubyte)),                                        # not working at the moment
                            self.height_.value*self.width_.value*self.bytes.value, self.wait_For_Trigger,
                            self.flip_immediate, self.OutputPulseImageFlip, self.OutputPulseImageRefresh, self.timeout_ms)
        self.slm_lib.ImageWriteComplete(self.board_number, self.timeout_ms)
        self.slm_lib.Delete_SDK()
# ----------------------------------------------------------------

    def saveState(self, state_general=None, state_pos=None, state_aber=None):
        if state_general is not None:
            self.state_general = state_general
        if state_pos is not None:
            self.state_pos = state_pos
        if state_aber is not None:
            self.state_aber = state_aber

    # def initCorrectionMask(self):
    #     # Add correction mask with correction pattern
    #     self.__maskCorrection = Mask(self.__slmSize[1], int(self.__slmSize[0]), self.__wavelength)
    #     bmpsCorrection = glob.glob(os.path.join(self.__correctionPatternsDir, "*.bmp"))
    #     load = "CAL_LSH0701153_" + "str(wavelengthCorrectionLoad)" + "nm", self.__correctionPatternsDir
    #     self.__logger.debug(f"Attribute to the loadBMP: \n {load}")

    #     if len(bmpsCorrection) < 1:
    #         self.__logger.error(
    #             'No BMP files found in correction patterns directory, cannot initialize correction mask.'
    #         )
    #         return

    #     wavelengthCorrection = [int(x[-9: -6]) for x in bmpsCorrection]
    #     # Find the closest correction pattern within the list of patterns available
    #     wavelengthCorrectionLoad = min(wavelengthCorrection,
    #                                    key=lambda x: abs(x - self.__wavelength))
    #     self.__maskCorrection.loadBMP("1024black.bmp",
    #                                   self.__correctionPatternsDir)

    def initTiltMask(self):
        # Add blazed grating tilting mask

        # defalut tilt freq
        self.defalut_tilt_freq = 0.5

        self.__maskTiltLeft = Mask(self.__slmSize[1], int(self.__slmSize[0] / 2),
                                   self.img_bit_depth, self.__wavelength)
        self.__maskTiltLeft.setTilt(self.__pixelsize)
        self.__maskTiltRight = Mask(self.__slmSize[1], int(self.__slmSize[0] / 2),
                                    self.img_bit_depth, self.__wavelength)
        self.__maskTiltRight.setTilt(self.__pixelsize)

    def initAberrationMask(self):
        # Add blazed grating tilting mask
        self.__maskAberLeft = Mask(self.__slmSize[1], int(self.__slmSize[0] / 2),
                                   self.img_bit_depth, self.__wavelength)
        self.__maskAberLeft.setBlack()
        self.__maskAberRight = Mask(self.__slmSize[1], int(self.__slmSize[0] / 2),
                                    self.img_bit_depth, self.__wavelength)
        self.__maskAberRight.setBlack()

    def initScanMask(self):
        # Add scan mask
        self.__maskScanLeft = Mask(self.__slmSize[1], int(
            self.__slmSize[0]/2), self.img_bit_depth, self.__wavelength)
        self.__maskScanRight = Mask(self.__slmSize[1], int(
            self.__slmSize[0]/2), self.img_bit_depth, self.__wavelength)

        self.__maskScanLeft.setBlack()
        self.__maskScanRight.setBlack()
        self.__logger.debug(f"self.bit_depth at the end of scanMask init: {self.img_bit_depth}")

    def setMask(self, mask, maskMode):
        if self.__masks[mask].mask_type == MaskMode.Black and maskMode != MaskMode.Black:
            self.__masksTilt[mask].setTilt(self.__pixelsize)
        if maskMode == maskMode.Donut:
            self.__masks[mask].setDonut()
        elif maskMode == maskMode.Tophat:
            self.__masks[mask].setTophat()
        elif maskMode == maskMode.Half:
            self.__masks[mask].setHalf()
        elif maskMode == maskMode.Gauss:
            self.__masks[mask].setGauss()
        elif maskMode == maskMode.Hex:
            self.__masks[mask].setHex()
        elif maskMode == maskMode.Quad:
            self.__masks[mask].setQuad()
        elif maskMode == maskMode.Split:
            self.__masks[mask].setSplit()
        elif maskMode == maskMode.Black:
            self.__masks[mask].setBlack()
            self.__masksTilt[mask].setBlack()
            self.__masksAber[mask].setBlack()

    def moveMask(self, mask, direction, amount):
        if direction == direction.Up:
            move_v = np.array([-1, 0]) * amount
        elif direction == direction.Down:
            move_v = np.array([1, 0]) * amount
        elif direction == direction.Left:
            move_v = np.array([0, -1]) * amount
        elif direction == direction.Right:
            move_v = np.array([0, 1]) * amount

        self.__masks[mask].moveCenter(move_v)
        self.__masksTilt[mask].moveCenter(move_v)
        self.__masksAber[mask].moveCenter(move_v)

    def getCenters(self):
        centerCoords = {"left": self.__masks[0].getCenter(),
                        "right": self.__masks[1].getCenter()}
        return centerCoords

    def setCenters(self, centerCoords):
        for idx, (mask, masktilt, maskaber, maskscan) in enumerate(zip(self.__masks, self.__masksTilt,
                                                             self.__masksAber, self.__masksScan)):
            if idx == 0:
                center = (centerCoords["left"]["xcenter"], centerCoords["left"]["ycenter"])
            elif idx == 1:
                center = (centerCoords["right"]["xcenter"], centerCoords["right"]["ycenter"])
            mask.setCenter(center)
            masktilt.setCenter(center)
            maskaber.setCenter(center)
            maskscan.setCenter(center)

    def setGeneral(self, general_info):
        self.setRadius(general_info["radius"])
        self.setSigma(general_info["sigma"])
        self.setRotationAngle(general_info["rotationAngle"])
        self.setTiltAngle(general_info["tiltAngle"])

    def setAberrationFactors(self, aber_info):
        lAberFactors = aber_info["left"]
        self.__masksAber[0].setAberrationFactors(lAberFactors)
        rAberFactors = aber_info["right"]
        self.__masksAber[1].setAberrationFactors(rAberFactors)

    def setAberrations(self, aber_info, mask):
        if mask == 0 or mask == None:
            lAberFactors = aber_info["left"]
            self.__masksAber[0].setAberrationFactors(lAberFactors)
            self.__masksAber[0].setAberrations()
        if mask == 1 or mask == None:
            rAberFactors = aber_info["right"]
            self.__masksAber[1].setAberrationFactors(rAberFactors)
            self.__masksAber[1].setAberrations()

    def setRadius(self, radius):
        for mask, masktilt, maskaber in zip(self.__masks, self.__masksTilt, self.__masksAber):
            mask.setRadius(radius)
            masktilt.setRadius(radius)
            maskaber.setRadius(radius)

    def setSigma(self, sigma):
        for mask in self.__masks:
            mask.setSigma(sigma)

    def setRotationAngle(self, rotation_angle):
        for mask in self.__masks:
            mask.setRotationAngle(rotation_angle)

    def setTiltAngle(self, tilt_angle):
        inverts = [1, -1]
        for idx, mask in enumerate(self.__masksTilt):
            mask.setTiltAngle(tilt_angle, inverts[idx])

    def update(self, maskChange=False, tiltChange=False, aberChange=False):
        if maskChange:
            self.maskDouble = self.__masks[0].concat(self.__masks[1])
        if tiltChange:
            self.maskTilt = self.__masksTilt[0].concat(self.__masksTilt[1])
        if aberChange:
            self.maskAber = self.__masksAber[0].concat(self.__masksAber[1])
        self.maskCombined = self.maskDouble + self.maskAber + self.maskTilt  # + self.__maskCorrection
        self.sigSLMMaskUpdated.emit(self.maskCombined)

        returnmask = self.maskDouble + self.maskAber
        self.__logger.debug(f"Mask updated: {returnmask}")

        return returnmask.image()


class Mask:
    """Class creating a mask to be displayed by the SLM."""

    def __init__(self, height: int, width: int, bit_depth: int, wavelength: int = 50):
        """initiates the mask as an empty array
        n,m corresponds to the width,height of the created image
        wavelength is the illumination wavelength in nm"""
        self.__logger = initLogger(self, tryInheritParent=True)
        self.__logger.debug(f"Init mask with bit_depth: {bit_depth}")
        self.zeroimg = np.zeros((height, width), dtype=np.uint8)
        self.img = np.zeros((height, width), dtype=np.uint8)
        self.height = height
        self.width = width
        self.value_max = 255
        self.centerx = self.height // 2
        self.centery = self.width // 2
        self.radius = 100
        self.sigma = 35
        self.wavelength = wavelength
        self.mask_type = MaskMode.Black
        self.angle_rotation = 0
        self.angle_tilt = 0
        self.pixelSize = 0
        self.value_max = int(2**bit_depth - 1)
        # if wavelength == 561:
        #     self.value_max = 148
        # elif wavelength == 491:
        #     self.value_max = 129
        # elif wavelength < 780 and wavelength > 800:
        #     # Here we infer the value of the maximum with a linear approximation from the ones
        #     # provided by the manufacturer
        #     # Better ask them in case you need another wavelength
        #     self.value_max = int(wavelength * 0.45 - 105)
        #     self.__logger.warning("Caution: a linear approximation has been made")

    def concat(self, maskOther):
        for mask in [self, maskOther]:
            mask.updateImage()
            mask.setCircular()
        maskCombined = Mask(self.height, self.width * 2, self.wavelength)
        imgCombined = np.concatenate((self.img, maskOther.img), axis=1)
        maskCombined.loadArray(imgCombined)
        return maskCombined

    def loadArray(self, mask):
        self.img = mask

    def image(self):
        return self.img

    def loadBMP(self, filename, path):
        """Loads a .bmp image as the img of the mask."""
        with Image.open(os.path.join(path, filename + ".bmp")) as data:
            imgLoad = np.array(data)
        heightLoad, widthLoad = imgLoad.shape
        if heightLoad > self.height:
            diff = heightLoad - self.height
            imgLoad = imgLoad[(diff // 2): (self.height + diff // 2), :]
        if widthLoad > self.width:
            diff = widthLoad - self.width
            imgLoad = imgLoad[:, diff // 2: self.width + diff // 2]

        if heightLoad <= self.height and widthLoad <= self.width:
            result = np.zeros((self.height, self.width))
            diffx = (self.width - widthLoad) // 2
            diffy = (self.height - heightLoad) // 2
            result[diffy: heightLoad + diffy, diffx: widthLoad + diffx] = imgLoad
            imgLoad = result

        self.height, self.width = imgLoad.shape
        self.img[:, :] = imgLoad[:, :]
        self.scaleToLut()

    def scaleToLut(self):
        """Scales the values of the pixels according to the LUT"""
        self.img = self.img.astype("float")
        self.img *= self.value_max / np.max(self.img)
        self.img = self.img.astype("uint8")

    def pi2uint8(self):
        """Method converting a phase image (values from 0 to 2Pi) into a uint8
        image"""
        # print debug log with max, min value, shape and type of the image
        self.__logger.debug(f"Max value: {np.max(self.img)}")
        self.__logger.debug(f"Min value: {np.min(self.img)}")
        self.__logger.debug(f"Shape: {self.img.shape}")
        self.__logger.debug(f"Type: {self.img.dtype}")
        self.__logger.debug(f"self.value_max: {self.value_max}")
        self.__logger.debug(f"Multiplied by {self.value_max / (2 * math.pi)}")
        self.__logger.debug("--------------------")
        self.img *= self.value_max / (2 * math.pi)
        # print debug log with max, min value, shape and type of the image
        self.__logger.debug(f"Max value: {np.max(self.img)}")
        self.__logger.debug(f"Min value: {np.min(self.img)}")
        self.__logger.debug(f"Shape: {self.img.shape}")
        self.__logger.debug(f"Type: {self.img.dtype}")
        self.__logger.debug("===================================")
        self.img = np.round(self.img).astype(np.uint8)

    def load(self, img):
        """Initiates the mask with an existing image."""
        tp = img.dtype
        if tp != np.uint8:
            max_val = np.max(img)
            self.__logger.warning("Input image is not of format uint8")
            if max_val != 0:
                img = self.value_max * img.astype('float64') / np.max(img)
            img = img.astype('uint8')
        self.img = img
        return

    def setCircular(self):
        """This method sets to 0 all the values within Mask except the ones
        included in a circle centered in (centerx,centery) with a radius r"""
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        mask_bin = x * x + y * y <= self.radius * self.radius
        result = np.zeros((self.height, self.width))
        result[mask_bin] = self.img[mask_bin]
        self.img = result

    def setTilt(self, pixelsize=None):
        """Creates a tilt mask, blazed grating, for off-axis holography."""
        if pixelsize:
            self.pixelSize = pixelsize
        wavelength = self.wavelength * 10 ** -6  # conversion to mm
        # self.__logger.debug(f"Wavelength: {wavelength:.6f} mm")
        # self.__logger.debug(f"Pixel size: {self.pixelSize} mm")
        mask = np.indices((self.height, self.width), dtype="float")[1, :, :]
        # Spatial frequency, round to avoid aliasing
        f_spat = np.round(wavelength / (self.pixelSize * np.sin(self.angle_tilt)))
        if np.absolute(f_spat) < 3:
            self.__logger.debug(f"Spatial frequency: {f_spat} pixels")
        period = 2 * math.pi / f_spat  # period
        mask *= period  # getting a mask that is time along x-axis with a certain period
        tilt = sg.sawtooth(mask) + 1  # creating the blazed grating
        tilt *= self.value_max / 2  # normalizing it to range of [0 value_max]
        tilt = np.round(tilt).astype(np.uint8)  # getting it in np.uint8 type
        self.img = tilt
        self.mask_type = MaskMode.Tilt

    def setAberrationFactors(self, aber_params_info):
        self.aber_params_info = aber_params_info

    def setAberrations(self):
        fTilt = self.aber_params_info["tilt"]
        fTip = self.aber_params_info["tip"]
        fDefoc = self.aber_params_info["defocus"]
        fSph = self.aber_params_info["spherical"]
        fVertComa = self.aber_params_info["verticalComa"]
        fHozComa = self.aber_params_info["horizontalComa"]
        fVertAst = self.aber_params_info["verticalAstigmatism"]
        fOblAst = self.aber_params_info["obliqueAstigmatism"]

        mask = np.fromfunction(lambda i, j: fTilt * 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)
                               * np.sin(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fTip * 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) * np.cos(
            np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fDefoc * np.sqrt(3) * (2 * (((i - self.centerx) / self.radius)
                                ** 2 + ((j - self.centery) / self.radius)**2) - 1), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fSph * np.sqrt(5) * (6 * (((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)
                                ** 4 - 6 * (((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) + 1), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fVertComa * np.sqrt(8) * np.sin(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * (3 * (np.sqrt(((i - self.centerx) / self.radius)
                                ** 2 + ((j - self.centery) / self.radius)**2))**3 - 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fHozComa * np.sqrt(8) * np.cos(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * (3 * (np.sqrt(((i - self.centerx) / self.radius)
                                ** 2 + ((j - self.centery) / self.radius)**2))**3 - 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fVertAst * np.sqrt(6) * np.cos(2 * np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius)))
                                * ((np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**2), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fOblAst * np.sqrt(6) * np.sin(2 * np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * (
            (np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**2), (self.height, self.width), dtype="float")

        mask %= 2 * math.pi
        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Aber

    def getCenter(self):
        return (self.centerx, self.centery)

    def setCenter(self, setCoords):
        self.centerx, self.centery = setCoords

    def setRadius(self, radius):
        self.radius = radius

    def setSigma(self, sigma):
        self.sigma = sigma

    def setRotationAngle(self, rotation_angle):
        self.angle_rotation = rotation_angle

    def setTiltAngle(self, tilt_angle, invert):
        self.angle_tilt = invert * tilt_angle * math.pi / 180

    def moveCenter(self, move_v):
        self.centerx = self.centerx + move_v[0]
        self.centery = self.centery + move_v[1]

    def setBlack(self):
        self.img = self.zeroimg
        self.mask_type = MaskMode.Black

    def setGauss(self):
        self.img = np.ones((self.height, self.width), dtype=np.uint8) * self.value_max // 2
        self.mask_type = MaskMode.Gauss

    def setDonut(self, rotation=True):
        """This function generates a donut mask, with the center defined in the
        mask object."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y)

        mask = theta % (2 * np.pi)
        if rotation:
            mask = np.ones((self.height, self.width), dtype="float") * (2 * np.pi) - mask

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Donut

    def setTophat(self):
        """This function generates a tophat mask with a mid-radius defined by
        sigma, and with the center defined in the mask object."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        d = x ** 2 + y ** 2

        mid_radius = self.sigma * np.sqrt(
            2 * np.log(2 / (1 + np.exp(-self.radius ** 2 / (2 * self.sigma ** 2))))
        )
        tophat_bool = (d > mid_radius ** 2)
        mask[tophat_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Tophat

    def setHalf(self):
        """Sets the current masks to half masks, with the same center,
        for accurate center position determination."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + self.angle_rotation

        half_bool = (abs(theta) < np.pi / 2)
        mask[half_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Half

    def setQuad(self):
        """Transforms the current mask in a quadrant pattern mask for testing
        aberrations."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + self.angle_rotation

        quad_bool = (theta < np.pi) * (theta > np.pi / 2) + (theta < 0) * (theta > -np.pi / 2)
        mask[quad_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Quad

    def setHex(self):
        """Transforms the current mask in a hex pattern mask for testing
        aberrations."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + self.angle_rotation

        hex_bool = ((theta < np.pi / 3) * (theta > 0) +
                    (theta > -2 * np.pi / 3) * (theta < -np.pi / 3) +
                    (theta > 2 * np.pi / 3) * (theta < np.pi))
        mask[hex_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Hex

    def setSplit(self):
        """Transforms the current mask in a split bullseye pattern mask for
        testing aberrations."""
        mask = np.zeros((self.height, self.width), dtype="float")
        mask1 = np.zeros((self.height, self.width), dtype="float")
        mask2 = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + self.angle_rotation

        radius_factor = 0.6
        mid_radius = radius_factor * self.radius
        d = x ** 2 + y ** 2
        ring = (d > mid_radius ** 2)
        mask1[ring] = np.pi
        midLine = (abs(theta) < np.pi / 2)
        mask2[midLine] = np.pi
        mask = (mask1 + mask2) % (2 * np.pi)

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Split

    def updateImage(self):
        if self.mask_type == MaskMode.Black:
            self.setBlack()
        elif self.mask_type == MaskMode.Gauss:
            self.setGauss()
        elif self.mask_type == MaskMode.Donut:
            self.setDonut()
        elif self.mask_type == MaskMode.Tophat:
            self.setTophat()
        elif self.mask_type == MaskMode.Half:
            self.setHalf()
        elif self.mask_type == MaskMode.Quad:
            self.setQuad()
        elif self.mask_type == MaskMode.Hex:
            self.setHex()
        elif self.mask_type == MaskMode.Split:
            self.setSplit()
        elif self.mask_type == MaskMode.Tilt:
            self.setTilt()
        elif self.mask_type == MaskMode.Aber:
            self.setAberrations()

    def __str__(self):
        return "image of the mask"

    def __add__(self, other):
        self.__logger.debug(f"Adding two masks togeather")
        if self.height == other.height and self.width == other.width:
            out = Mask(self.height, self.width, self.wavelength)
            out.load(((self.image() + other.image()) % (self.value_max + 1)).astype(np.uint8))
            return out
        else:
            raise TypeError("Cannot add two masks with different shapes")


class MaskMode(enum.Enum):
    Donut = 1
    Tophat = 2
    Black = 3
    Gauss = 4
    Half = 5
    Hex = 6
    Quad = 7
    Split = 8
    Tilt = 9
    Aber = 10


class Direction(enum.Enum):
    Up = 1
    Down = 2
    Left = 3
    Right = 4


class MaskChoice(enum.Enum):
    Left = 0
    Right = 1


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
