import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QLabel
from PyQt5.QtGui import QPixmap
from UHS_SLMManager import *

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'UHS-SLM'
        self.left = 10
        self.top = 10
        self.width = 700
        self.height = 600
        self.initUI()
        print(bit_depth)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        button1 = QPushButton('Open Dialog', self)
        button1.setToolTip('Open Dialog')
        button1.move(100, 100)
        button1.clicked.connect(self.openFileNameDialog)

        button2 = QPushButton('Upload', self)
        button2.setToolTip('Not Defined Function')
        button2.move(300, 100)
        button2.clicked.connect(self.notDefinedFunction)

        button3 = QPushButton('Close', self)
        button3.setToolTip('Close')
        button3.move(500, 100)
        button3.clicked.connect(self.close)

        self.label = QLabel(self)
        self.label.setGeometry(150, 150, 400, 400)

        self.show()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        # fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)

        if fileName:
            pixmap = QPixmap(fileName)
            pixmap = pixmap.scaled(400, 400)
            self.label.setPixmap(pixmap)

    def notDefinedFunction(self):
       pass



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())