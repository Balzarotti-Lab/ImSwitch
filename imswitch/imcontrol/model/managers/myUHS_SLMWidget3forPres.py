import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QLabel
from PyQt5.QtGui import QPixmap,QImage
import numpy
from ctypes import *


# Load the DLL
# Blink_C_wrapper.dll, Blink_SDK.dll, ImageGen.dll, FreeImage.dll and wdapi1021.dll
# should all be located in the same directory as the program referencing the
# library
# cdll.LoadLibrary("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\Blink_C_wrapper")
# slm_lib = CDLL("Blink_C_wrapper")

# Open the image generation library
# cdll.LoadLibrary("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\ImageGen")   # not needed at the moment
# image_lib = CDLL("ImageGen")

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
flip_immediate = c_uint(0) #only supported on the 1024
timeout_ms = c_uint(5000)
center_x = c_float(256)
center_y = c_float(256)
VortexCharge = c_uint(3)
fork = c_uint(0)
RGB = c_uint(0)
# Both pulse options can be false, but only one can be true. You either generate a pulse when the new image begins loading to the SLM
# or every 1.184 ms on SLM refresh boundaries, or if both are false no output pulse is generated.
OutputPulseImageFlip = c_uint(0)
OutputPulseImageRefresh = c_uint(0); #only supported on 1920x1152, FW rev 1.8. 

GLOBAL_STYLE = """QPushButton {
    background-color: #455364;
    color: #FFFFFF;
    border-style: outset;
    padding: 2px;
    border-radius: 3px;
    font-size: 8pt;
} 
QPushButton:hover {
    background-color: #54687a;
}"""

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.slm_size = 1024
        self.view_size = 400
        self.view_img = self.blankBitmap()
        # self.init_SLMController()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('UHS-SLM')
        self.setGeometry(100, 100, 0, 0)
        self.setFixedSize(720, 580)
        self.setStyleSheet("background-color: #19232d")

        button1 = QPushButton('Load Mask', self)
        button1.setToolTip('Open Dialog')
        button1.setGeometry(100, 500, 120, 25)
        button1.setStyleSheet(GLOBAL_STYLE)
        button1.clicked.connect(self.openFileNameDialog)

        button2 = QPushButton('Upload', self)
        button2.setToolTip('Uploads the selected Mask to the SLM')
        button2.setGeometry(300, 500, 120, 25)
        button2.setStyleSheet(GLOBAL_STYLE)
        button2.clicked.connect(self.uploadMask)

        button3 = QPushButton('Close', self)
        button3.setToolTip('Closes the program')
        button3.setGeometry(500, 500, 120, 25)
        button3.setStyleSheet(GLOBAL_STYLE)
        button3.clicked.connect(self.close)

        self.label = QLabel(self)
        self.label.setGeometry(160, 50, self.view_size, self.view_size)
        self.label.setPixmap(self.view_img)
        self.show()

    def init_SLMController(self):
        slm_lib.Create_SDK(bit_depth, byref(num_boards_found), byref(constructed_okay),
                           is_nematic_type, RAM_write_enable, use_GPU, max_transients, 0)

        if constructed_okay.value == 0:
            print ("Blink SDK did not construct successfully")
            slm_lib.Delete_SDK()
    
        if num_boards_found.value == 1:                         
            print ("Blink SDK was successfully constructed")
            print ("Found %s SLM controller(s)" % num_boards_found.value)

            self.height_ = c_uint(slm_lib.Get_image_height(board_number))
            self.width_ = c_uint(slm_lib.Get_image_width(board_number))
            self.depth_ = c_uint(slm_lib.Get_image_depth(board_number)) # Bits per pixel
            self.bytes = c_uint(self.depth_.value//8)
            self.center_x = c_uint(self.width_.value//2)
            self.center_y = c_uint(self.height_.value//2)

            # Loading LUTs: Controller keeps last used LUT (at least it was not turned off)
            # slm_lib.Load_LUT_file(board_number, b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\1024x1024_linearVoltage.LUT")     
            # slm_lib.Load_LUT_file(board_number, b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\slm6517_at635_75C.LUT")
            # slm_lib.Load_LUT_file(board_number, b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\slm6517_at635_30C.LUT")
           
            # Create a vector to hold values for a SLM image, and fill the wavefront correction with a blank
            self.upload_img = numpy.zeros([self.width_.value*self.height_.value*self.bytes.value], numpy.uint8, 'C')
            self.WFC = numpy.zeros([self.width_.value*self.height_.value*self.bytes.value], numpy.uint8, 'C')

            # Write a blank pattern to the SLM to get going
            retVal = slm_lib.Write_image(board_number, self.upload_img.ctypes.data_as(POINTER(c_ubyte)),
                                        self.height_.value*self.width_.value*self.bytes.value, wait_For_Trigger,
                                        flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
            if (retVal == -1):
                print ("Upload/Communication to SLM failed")
                slm_lib.Delete_SDK()
        else: 
            print("Board number is not equal to 1 ")
            slm_lib.Delete_SDK()

    def blankBitmap(self):
        image = QImage(self.slm_size, self.slm_size, QImage.Format_RGB32)
        image.fill(0x000000)
        image = QPixmap(image)
        return image
    
    def openFileNameDialog(self):
        img, _ = QFileDialog.getOpenFileName(self,"Select existing mask file", "",'Images (*.png *.bmp)')
        if img:
            image = QImage(img)
            image = image.scaled(self.slm_size, self.slm_size)
            image = image.convertToFormat(QImage.Format_Grayscale8)
            self.upload_img = numpy.array(image.bits().asarray(self.slm_size * self.slm_size))

            image = QPixmap(image)
            self.label.setPixmap(image.scaled(self.view_size, self.view_size))
            
    def uploadMask(self):
        pass
        # #write image returns on DMA complete, ImageWriteComplete returns when the hardware
        # #image buffer is ready to receive the next image. Breaking this into two functions is 
        # #useful for external triggers. It is safe to apply a trigger when Write_image is complete
        # #and it is safe to write a new image when ImageWriteComplete returns
        # retVal = slm_lib.Write_image(board_number, self.upload_img.ctypes.data_as(POINTER(c_ubyte)),
        #                              self.height_.value*self.width_.value*self.bytes.value, wait_For_Trigger,
        #                              flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)

        # if (retVal == -1):
        #     print ("Upload/Communication to SLM failed")
        #     slm_lib.Delete_SDK()
        # else:
        #     #check the buffer is ready to receive the next image
        #     print("upload")                                                                          
        #     retVal = slm_lib.ImageWriteComplete(board_number, timeout_ms)
        #     if(retVal == -1):
        #         print ("ImageWriteComplete failed, trigger never received?")
        #         slm_lib.Delete_SDK()

    def closeEvent(self, event):
        
        self.upload_img = numpy.zeros([self.width_.value*self.height_.value*self.bytes.value], numpy.uint8, 'C')
        slm_lib.Write_image(board_number, self.upload_img.ctypes.data_as(POINTER(c_ubyte)),
                            self.height_.value*self.width_.value*self.bytes.value, wait_For_Trigger,
                            flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
        slm_lib.ImageWriteComplete(board_number, timeout_ms)
        slm_lib.Delete_SDK()
        
        print("closing")
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())