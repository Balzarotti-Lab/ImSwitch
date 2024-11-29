from qtpy import QtWidgets, QtCore

from .basewidgets import Widget
from imswitch.imcontrol.view import guitools


class PupilSegmentationWidget(Widget):
    """
    PupuilSegmentationWidget allows to specify the desired parameters for the pupil segmentation.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        PupSegTitle = QtWidgets.QLabel(
            "<h2><strong>Pupil Segmentation<h2><strong>")
        PupSegTitle.setTextFormat(QtCore.Qt.RichText)
