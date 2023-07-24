import numpy
from PyQt5.QtGui import QPixmap,QImage

image = QImage(1024, 1024, QImage.Format_RGB32)
image.fill(0xFFFFFF)
image = image.convertToFormat(QImage.Format_Grayscale8)
image = numpy.array(image.bits().asarray(1024 * 1024))
print(image)
print(image.size)

image2 = numpy.full(1024*1024,255)
print(image2)
print(image2.size)
