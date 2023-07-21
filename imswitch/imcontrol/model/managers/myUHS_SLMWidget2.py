import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QLabel
from PyQt5.QtGui import QPixmap,QImage
import numpy
from ctypes import *
from time import sleep
# from PIL import Image

# Load the DLL
# Blink_C_wrapper.dll, Blink_SDK.dll, ImageGen.dll, FreeImage.dll and wdapi1021.dll
# should all be located in the same directory as the program referencing the
# library
cdll.LoadLibrary("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\Blink_C_wrapper")
slm_lib = CDLL("Blink_C_wrapper")

# Open the image generation library
cdll.LoadLibrary("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\ImageGen")
image_lib = CDLL("ImageGen")

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
} 
QPushButton:hover {
    background-color: #54687a;
}"""

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'UHS-SLM'
        self.left = 100
        self.top = 100
        self.width = 700
        self.height = 600
        self.upload_img = self.blankBitmap()
        self.initUI()
        

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setStyleSheet("background-color: #19232d")

        button1 = QPushButton('Load Mask', self)
        button1.setToolTip('Open Dialog')
        button1.move(100, 100)
        button1.setStyleSheet(GLOBAL_STYLE)
        button1.clicked.connect(self.openFileNameDialog)
        

        button2 = QPushButton('Upload', self)
        button2.setToolTip('Uploads the selected Mask to the SLM')
        button2.move(300, 100)
        button2.setStyleSheet(GLOBAL_STYLE)
        button2.clicked.connect(self.notDefinedFunction)

        button3 = QPushButton('Close', self)
        button3.setToolTip('Closes the program')
        button3.move(500, 100)
        button3.setStyleSheet(GLOBAL_STYLE)
        button3.clicked.connect(self.close)

        self.label = QLabel(self)
        self.label.setGeometry(150, 150, 400, 400)
        self.label.setPixmap(self.upload_img)

        self.show()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        img, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","PNG File (*.png);;Bitmap File (*.bmp)", options=options)
        
        if img:
            pixmap = QPixmap(img)
            pixmap = pixmap.toImage().convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap(pixmap)
            self.upload_img = pixmap.scaled(1024, 1024)
            self.label.setPixmap(self.upload_img)
            # return self.upload
        
    def blankBitmap(self):
        image = QImage(1024, 1024, QImage.Format_RGB32)
        image.fill(0x000000)
        image = QPixmap(image)
        return image

    def notDefinedFunction(self):
        print(type(self.upload_img))

    # def convert_png_to_gray_bitmap(image_path):
    # image = QImage(image_path)
    # if image.format() == QImage.Format_RGB32:
    #     pixmap = QPixmap(image_path)
    #     gray_pixmap = pixmap.toImage().convertToFormat(QImage.Format_Grayscale8)
    #     return gray_pixmap
    # else:
    #     return None


    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())