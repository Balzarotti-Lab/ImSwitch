import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas
)

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import NapariHybridWidget
from typing import Dict, Tuple

__author__ = "David Palecek", "Jacopo Abramo"
__credits__ = []
__maintainer__ = "David Palecek"
__email__ = "david@stanka.de"


class OptWidget(NapariHybridWidget):
    """ Widget controlling OPT experiments where a rotation stage is triggered
    """
    sigRotStepDone = QtCore.Signal()
    sigRunScanClicked = QtCore.Signal()

    def __post_init__(self, *args, **kwargs):
        """Define qwidgets for the widget. """
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.scanPar = {}

        # widget layout
        self.widgetLayout()
        self.enabled = True
        self.layer = None

    def getRotatorIdx(self) -> int:
        """Returns currently selected rotator for the OPT """
        return self.scanPar['Rotator'].currentIndex()

    def getDetectorIdx(self) -> int:
        """Returns currently selected detector for the OPT """
        return self.scanPar['Detector'].currentIndex()

    def getOptSteps(self) -> int:
        """ Returns the user-input number of OPTsteps. """
        return self.scanPar['OptStepsEdit'].value()

    def setOptSteps(self, value: int) -> None:
        """ Setter for number for OPT steps. """
        self.scanPar['OptStepsEdit'].setValue(value)

    def getHotStd(self) -> float:
        """ Returns the user-input STD cutoff for the hot pixel correction. """
        return self.scanPar['HotPixelsStdEdit'].value()

    def getAverages(self) -> int:
        """ Returns the user-input number of averages for the
        hot pixel correction.
        """
        return self.scanPar['AveragesEdit'].value()

    def getLiveReconIdx(self) -> int:
        """ Returns live reconstruction idex, i.e. line idex of the
        camera frame.

        Returns:
            int: line index to be reconstructed
        """
        return self.scanPar['LiveReconIdxEdit'].value()

    def setLiveReconIdx(self, value: int) -> None:
        """Set reconstruction index. Called in the case that user
        chooses index which is incompatible with the frame shape

        Args:
            value (int): line index value
        """
        self.scanPar['LiveReconIdxEdit'].setValue(int(value))

    def updateHotPixelCount(self, count: int) -> None:
        """ Displays count of the identified hot pixels.

        Args:
            count (int): hot pixel count
        """
        self.scanPar['HotPixelCount'].setText(f'Count: {count:d}')

    def updateHotPixelMean(self, value: float) -> None:
        """Mean intensity of the hot pixels. Used only for display
        (informative) purposes.

        Args:
            value (float): Mean intensity of the hot pixels.
        """
        self.scanPar['HotPixelMean'].setText(f'Hot mean: {value:.3f}')

    def updateNonHotPixelMean(self, value: float) -> None:
        """Mean intensity of non-hot pixels. Used only for display
        (informative) purposes.

        Args:
            value (float): mean intensity of non-hot pixels.
        """
        self.scanPar['NonHotPixelMean'].setText(f'Non-hot mean: {value:.3f}')

    def updateDarkMean(self, value: float) -> None:
        """Mean intensity of the dark field acquisition. Used only for
        display (informative) purposes.

        Args:
            value (float): mean dark field correction intensity.
        """
        self.scanPar['DarkMean'].setText(f'Dark mean: {value:.2f}')

    def updateDarkStd(self, value: float) -> None:
        """Standart deviation of the dark field correction. Used only
        for display (informative) purposes.

        Args:
            value (float): STD of the darkfield correction.
        """
        self.scanPar['DarkStd'].setText(f'Dark STD: {value:.2f}')

    def updateFlatMean(self, value: float) -> None:
        """Mean intensity of the flat (bright) field correction. Used only
        for display (informative) purposes.

        Args:
            value (float): Mean flat-field intensity
        """
        self.scanPar['FlatMean'].setText(f'Flat mean: {value:.2f}')

    def updateFlatStd(self, value: float) -> None:
        """Standard deviation fo the flat/bright field correction. Used only
        for display (informative) purposes.

        Args:
            value (float): STD of the flat field correction.
        """
        self.scanPar['FlatStd'].setText(f'Flat STD: {value:.2f}')

    def updateCurrentStep(self, value: str = '-') -> None:
        """Updates text in the widget of current OPT step counter

        Args:
            value (str, optional): Current step counter. Numbers converted
                to string. Defaults to '-'.
        """
        self.scanPar['CurrentStepLabel'].setText(
            f'Current Step: {value}/{self.getOptSteps()}'
        )

    def updateCurrentReconStep(self, value='-') -> None:
        self.scanPar['CurrentReconStepLabel'].setText(
            f'Current Recon: {value}/{self.getOptSteps()}'
        )

    def setRotStepEnable(self, enabled: bool) -> None:
        """ For inactivating during scanning when ActivateButton pressed
        and waiting for a scan. When scan finishes, enable again.

        Args:
            enabled (bool): boolean for the setter.
        """
        self.scanPar['OptStepsEdit'].setEnabled(enabled)

    def setProgressBarValue(self, value: int) -> None:
        """Update progressbar

        Args:
            value (int): value of frames generated so far.
        """
        self.sinogramProgressBar.setValue(value)

    def setProgressBarVisible(self, visible: bool) -> None:
        """Toggle visibility of the progress Bar.

        Args:
            visible (bool): whether bar visible.
        """
        self.sinogramProgressBar.setVisible(visible)

    def setProgressBarMaximum(self, value: int) -> None:
        """Maximum value of the progress bar.

        Args:
            value (int): number of frames, i.e. OPT steps.
        """
        self.sinogramProgressBar.setMaximum(value)

    def setImage(self, im: np.ndarray, colormap: str = "gray",
                 name: str = "", pixelsize: Tuple[int] = (1, 20, 20),
                 translation: Tuple[int] = (0, 0, 0), step: int = 0):
        """Display image or stack of images in the napari viewer. It
        deal with 2D and 3D arrays. For a 3D array, last added frame will
        displayed using viewer.dims attribute.

        Args:
            im (np.ndarray): image frames
            colormap (str, optional): napari colormap. Defaults to "gray".
            name (str, optional): Name of the layer. Defaults to "".
            pixelsize (Tuple[int], optional): napari pixel size attr.
                Defaults to (1, 20, 20).
            translation (Tuple[int], optional): frame translation, napari attr.
                Defaults to (0, 0, 0).
            step (int, optional): Frame step, in order to display the last one.
                Defaults to 0.
        """
        # handle 2D input
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])

        # create new layer if necessary
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False,
                                               colormap=colormap,
                                               scale=pixelsize,
                                               translate=translation,
                                               name=name,
                                               blending='translucent')

        # add images
        self.layer.data = im
        self.layer.contrast_limits = (np.min(im), np.max(im))

        # display last frame
        try:
            self.viewer.dims.current_step = (step, im.shape[1], im.shape[2])
        except Exception as e:
            print('Except from viewer.dims', e)

    def clearStabilityPlot(self) -> None:
        """ Removes lines from the stability plot before updating the plot. """
        self.intensityPlot.clear()

    def updateStabilityPlot(self, steps: list, intensity: Dict[str, list],
                            ) -> None:
        """Updates widget plot with new stability line plots.

        Args:
            steps (list): x axis of the plot, basically OPT steps
            intensity (Dict[list]): Mean intensity values from 4
                corners of the frame. One list per corner.
        """
        self.intensityPlot.clear()
        self.intensityPlot.addLegend()

        colors = ['w', 'r', 'g', 'b']
        # iterate over
        for i, (key, trace) in enumerate(intensity.items()):
            self.intensityPlot.plot(
                steps,
                trace,
                name=key,
                pen=pg.mkPen(colors[i], width=1.5),
            )

    def plotReport(self, report: dict) -> None:
        """ Opens a secondary dialog displaying the experiment timing
        statistics.

        Args:
            report (dict): report collected from controller.
        """
        self.plotDialog = PlotDialog(self, report)
        self.plotDialog.resize(1500, 700)
        self.plotDialog.show()

    def requestOptStepsConfirmation(self) -> bool:
        """Request confirmation from the user if proceed with acquisition
        since the step size is not integer."""
        text = "Steps per/rev should be divisable by number of OPT steps. \
                You can continue by casting the steps on integers and risk \
                imprecise measured angles. Cast on integers and proceed (Yes) \
                or cancel scan (No)."
        return guitools.askYesNoQuestion(self,
                                         "Motor steps not integer values.",
                                         " ".join(text.split()))

    def requestMockConfirmation(self) -> bool:
        """ Request confirmation from the user if proceed with mock experiment.
        """
        text = "A mock experiment with synthetic generated data has been \
                requested. Confirm?"
        return guitools.askYesNoQuestion(self,
                                         "Mock OPT is about to run.",
                                         " ".join(text.split()))

    def widgetLayout(self):
        """Define widget layout. """
        self.scanPar['GetHotPixels'] = guitools.BetterPushButton('Hot Pixels')
        # tool tip
        self.scanPar['GetHotPixels'].setToolTip(
            'Acquire hot pixels for the current detector. Long exposure'
            ' is desirable.'
            )

        self.scanPar['HotPixelsStdEdit'] = QtWidgets.QDoubleSpinBox()
        self.scanPar['HotPixelsStdEdit'].setRange(1, 100)  # step 1 by default
        self.scanPar['HotPixelsStdEdit'].setValue(5)
        self.scanPar['HotPixelsStdEdit'].setDecimals(1)
        self.scanPar['HotPixelsStdEdit'].setToolTip(
            'Hot pixel is identified as intensity > mean + cutoff * STD.',
            )
        self.scanPar['HotPixelsStdLabel'] = QtWidgets.QLabel('STD cutoff')

        self.scanPar['AveragesEdit'] = QtWidgets.QSpinBox()
        self.scanPar['AveragesEdit'].setRange(1, 1000)  # step is 1 by default
        self.scanPar['AveragesEdit'].setValue(30)
        self.scanPar['AveragesEdit'].setToolTip(
            'Average N frames for Hot pixels aquistion.',
            )
        self.scanPar['AveragesLabel'] = QtWidgets.QLabel('Averages')

        self.scanPar['HotPixelCount'] = QtWidgets.QLabel(f'Count: {0:d}')
        self.scanPar['HotPixelMean'] = QtWidgets.QLabel(f'Hot mean: {0:.2f}')
        self.scanPar['NonHotPixelMean'] = QtWidgets.QLabel(
            f'Non-hot mean: {0:.2f}',
            )

        # darkfield
        self.scanPar['GetDark'] = guitools.BetterPushButton('Dark-field')
        # tool tip
        self.scanPar['GetDark'].setToolTip(
            'Acquire dark field for the current detector. Same exposure'
            ' as used in the experiment is strongly recommended.'
            )
        self.scanPar['DarkMean'] = QtWidgets.QLabel(f'Dark mean: {0:.2f}')
        self.scanPar['DarkStd'] = QtWidgets.QLabel(f'Dark STD: {0:.2f}')

        # brightfield
        self.scanPar['GetFlat'] = guitools.BetterPushButton('Bright-field')
        # tool tip
        self.scanPar['GetFlat'].setToolTip(
            'Acquire bright field for the current detector. Same exposure'
            ' as used in the experiment is strongly recommended.'
            )
        self.scanPar['FlatMean'] = QtWidgets.QLabel(f'Flat mean: {0:.2f}')
        self.scanPar['FlatStd'] = QtWidgets.QLabel(f'Flat STD: {0:.2f}')

        # OPT
        self.scanPar['RotStepsLabel'] = QtWidgets.QLabel('OPT rot. steps')
        self.scanPar['OptStepsEdit'] = QtWidgets.QSpinBox()
        self.scanPar['OptStepsEdit'].setRange(2, 10000)  # step is 1 by default
        self.scanPar['OptStepsEdit'].setValue(200)
        self.scanPar['OptStepsEdit'].setToolTip(
            'Steps taken per revolution of OPT scan',
            )
        self.scanPar['CurrentStepLabel'] = QtWidgets.QLabel(
            f'Current Step: -/{self.getOptSteps()}')

        self.scanPar['Rotator'] = QtWidgets.QComboBox()
        self.scanPar['RotatorLabel'] = QtWidgets.QLabel('Rotator')
        self.scanPar['StepsPerRevLabel'] = QtWidgets.QLabel(f'{0:d} steps/rev')

        self.scanPar['Detector'] = QtWidgets.QComboBox()
        self.scanPar['DetectorLabel'] = QtWidgets.QLabel('Detector')

        self.scanPar['LiveReconButton'] = QtWidgets.QCheckBox(
            'Live reconstruction',
            )
        self.scanPar['LiveReconButton'].setCheckable(True)
        # tool tip
        self.scanPar['LiveReconButton'].setToolTip(
            'Reconstruct live the line of the camera frame. The line index'
            ' is set by the LiveReconIdxEdit. None of this is saved or'
            ' interferes with saving the data.'
            )
        self.scanPar['LiveReconIdxEdit'] = QtWidgets.QSpinBox()
        self.scanPar['LiveReconIdxEdit'].setRange(0, 10000)  # dflt step 1
        self.scanPar['LiveReconIdxEdit'].setValue(200)
        self.scanPar['LiveReconIdxEdit'].setToolTip(
            'Line px of the camera to reconstruct live via FBP',
            )
        self.scanPar['LiveReconIdxLabel'] = QtWidgets.QLabel('Recon Idx')
        self.scanPar['CurrentReconStepLabel'] = QtWidgets.QLabel(
            f'Current Recon: -/{self.getOptSteps()}',
            )

        self.scanPar['MockOpt'] = QtWidgets.QCheckBox(
            'Demo experiment',
            )
        self.scanPar['MockOpt'].setCheckable(True)
        # tool tip
        self.scanPar['MockOpt'].setToolTip(
            'Run a mock experiment with synthetic generated data. The'
            ' data is can be saved and processed for demonstration'
            ' purposes.'
            )

        # Start and Stop buttons
        self.scanPar['StartButton'] = QtWidgets.QPushButton('Start')
        # tool tip
        self.scanPar['StartButton'].setToolTip('Start the OPT scan.')
        self.scanPar['StopButton'] = QtWidgets.QPushButton('Stop')
        # tool tip
        self.scanPar['StopButton'].setToolTip('Stop the OPT scan.'
                                              ' Metadata still saved')
        self.scanPar['PlotReportButton'] = QtWidgets.QPushButton('Report')
        # tool tip
        self.scanPar['PlotReportButton'].setToolTip('Show timing report of the'
                                                    ' last experiemnt.')
        self.scanPar['SaveButton'] = QtWidgets.QCheckBox('Save')
        self.scanPar['SaveButton'].setCheckable(True)
        # tool tip
        self.scanPar['SaveButton'].setToolTip(
            'Save the data to the disk. Data folder per scan is created.'
            ' Metadata saved in the same folder.'
            )
        self.scanPar['noRamButton'] = QtWidgets.QCheckBox('no RAM')
        self.scanPar['noRamButton'].setCheckable(True)
        # tool tip
        self.scanPar['noRamButton'].setToolTip(
            'Save the data to the disk without storing in the RAM.'
            ' Useful for large datasets, viewer will show only'
            ' the last acquired'
            ' projection. Does not affect the saving option selected.'
            )

        self.liveReconPlot = pg.ImageView()
        self.intensityPlot = pg.PlotWidget()

        # tab for plots
        self.tabsPlots = QtWidgets.QTabWidget()
        self.tabRecon = QtWidgets.QWidget()
        self.grid2 = QtWidgets.QGridLayout()
        self.tabRecon.setLayout(self.grid2)
        self.grid2.addWidget(self.liveReconPlot, 0, 0)

        self.tabInt = QtWidgets.QWidget()
        self.grid3 = QtWidgets.QGridLayout()
        self.tabInt.setLayout(self.grid3)
        self.grid3.addWidget(self.intensityPlot)

        # two more grids and tabs
        self.tabsAcq = QtWidgets.QTabWidget()
        self.tabCorr = QtWidgets.QWidget()
        self.grid4 = QtWidgets.QGridLayout()
        self.tabCorr.setLayout(self.grid4)

        self.tabAcq = QtWidgets.QWidget()
        self.grid5 = QtWidgets.QGridLayout()
        self.tabAcq.setLayout(self.grid5)

        # Add tabs
        self.tabsPlots.addTab(self.tabRecon, "Recon")
        self.tabsPlots.addTab(self.tabInt, "Intensity")
        self.tabsAcq.addTab(self.tabCorr, "Corrections")
        self.tabsAcq.addTab(self.tabAcq, "OPT acquisition")

        currentRow = 0
        # corrections
        self.grid4.addWidget(QtWidgets.QLabel('<strong>Corrections:</strong>'),
                             currentRow, 0)
        self.grid4.addWidget(self.scanPar['AveragesEdit'], currentRow, 1)
        self.grid4.addWidget(self.scanPar['AveragesLabel'], currentRow, 2)

        currentRow += 1

        self.grid4.addWidget(self.scanPar['GetHotPixels'], currentRow, 0)
        self.grid4.addWidget(self.scanPar['HotPixelsStdEdit'], currentRow, 1)
        self.grid4.addWidget(self.scanPar['HotPixelsStdLabel'], currentRow, 2)

        currentRow += 1

        self.grid4.addWidget(self.scanPar['HotPixelCount'], currentRow, 0)
        self.grid4.addWidget(self.scanPar['HotPixelMean'], currentRow, 1)
        self.grid4.addWidget(self.scanPar['NonHotPixelMean'], currentRow, 2)

        currentRow += 1

        self.grid4.addWidget(self.scanPar['GetDark'], currentRow, 0)
        self.grid4.addWidget(self.scanPar['DarkMean'], currentRow, 1)
        self.grid4.addWidget(self.scanPar['DarkStd'], currentRow, 2)

        currentRow += 1

        self.grid4.addWidget(self.scanPar['GetFlat'], currentRow, 0)
        self.grid4.addWidget(self.scanPar['FlatMean'], currentRow, 1)
        self.grid4.addWidget(self.scanPar['FlatStd'], currentRow, 2)

        # OPT settings
        currentRow += 1
        self.grid5.addWidget(self.scanPar['RotatorLabel'], currentRow, 0)
        self.grid5.addWidget(self.scanPar['Rotator'], currentRow, 1)
        self.grid5.addWidget(self.scanPar['StepsPerRevLabel'], currentRow, 2)

        currentRow += 1
        self.grid5.addWidget(self.scanPar['DetectorLabel'], currentRow, 0)
        self.grid5.addWidget(self.scanPar['Detector'], currentRow, 1)

        currentRow += 1

        self.grid5.addWidget(self.scanPar['RotStepsLabel'], currentRow, 0)
        self.grid5.addWidget(self.scanPar['OptStepsEdit'], currentRow, 1)
        self.grid5.addWidget(self.scanPar['MockOpt'], currentRow, 2)

        currentRow += 1

        self.grid5.addWidget(self.scanPar['LiveReconButton'], currentRow, 0)
        self.grid5.addWidget(self.scanPar['LiveReconIdxEdit'], currentRow, 1)
        self.grid5.addWidget(self.scanPar['LiveReconIdxLabel'], currentRow, 2)

        currentRow += 1

        self.grid5.addWidget(self.scanPar['CurrentStepLabel'], currentRow, 0)
        self.grid5.addWidget(self.scanPar['SaveButton'], currentRow, 1)
        self.grid5.addWidget(self.scanPar['noRamButton'], currentRow, 2)

        currentRow += 1

        # Start and Stop buttons
        self.grid5.addWidget(self.scanPar['StartButton'], currentRow, 0)
        self.grid5.addWidget(self.scanPar['StopButton'], currentRow, 1)
        self.grid5.addWidget(self.scanPar['PlotReportButton'], currentRow, 2)

        # Progress bar for synthetic data generation;
        # not visible by default, shown only when mock experiment is requested
        self.sinogramProgressBar = QtWidgets.QProgressBar(self)
        self.sinogramProgressBar.setValue(0)
        self.sinogramProgressBar.setFormat('Sinogram point: %v')
        self.sinogramProgressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.sinogramProgressBar.setTextVisible(True)
        self.sinogramProgressBar.setVisible(False)

        self.grid5.addWidget(self.sinogramProgressBar, currentRow, 0, 1, -1)

        currentRow += 1
        self.grid.addWidget(self.tabsAcq, currentRow, 0, 1, -1)
        currentRow += 1
        self.grid.addWidget(self.tabsPlots, currentRow, 0, 1, -1)


class PlotDialog(QtWidgets.QDialog):
    """
    Create a pop-up widget with the OPT time execution
    statistical plots. Timings are collected during the last run
    OPT scan. The plots show the relevant statistics spent
    on particular tasks during the overall experiment,
    as well as per OPT step.
    """
    def __init__(self, parent, report: dict) -> None:
        super(PlotDialog, self).__init__(parent)
        self.mainWidget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.mainWidget)
        canvas = ReportCanvas(report, self.mainWidget, width=300, height=300)
        layout.addWidget(canvas)
        self.setLayout(layout)


class ReportCanvas(FigureCanvas):
    def __init__(self, report, parent=None, width=300, height=300):
        """ Plot of the report

        Args:
            report (dict): report data dictionary
            parent (_type_, optional): parent class. Defaults to None.
            width (int, optional): width of the plot in pixels.
                Defaults to 300.
            height (int, optional): height of the plot in pixels.
                Defaults to 300.
        """
        fig = Figure(figsize=(width, height))
        self.ax1 = fig.add_subplot(131)
        self.ax2 = fig.add_subplot(132)
        self.ax3 = fig.add_subplot(133)

        self.createFigure(report)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def createFigure(self, report: dict) -> None:
        """Create report plot.

        Args:
            report (dict): report dictionary.
        """
        keys = report.keys()
        mean, std, percTime, tseries = [], [], [], []
        my_cmap = mpl.colormaps.get_cmap("viridis")
        colors = my_cmap(np.linspace(0, 1, len(keys)))

        # sort timestamps by keys which belong to certain acquisition steps
        for key, value in report.items():
            if key == "start" or key == "end":
                continue
            percTime.append(value['PercTime'])
            mean.append(value['Mean'])
            std.append(value['STD'])
            tseries.append(value['Tseries'])

        # add plot 1
        self.ax1.bar(keys, percTime, color=colors)

        # add plot 2
        self.ax1.set_ylabel('Percentage of Total exp. time [%]')
        self.ax2.bar(keys, mean, color=colors,
                     yerr=std, align='center',
                     ecolor='black', capsize=10)
        self.ax2.set_ylabel('Mean time per operation [s]')

        # add plot 3
        for i, k in enumerate(keys):
            self.ax3.plot(tseries[i][0], tseries[i][1], 'o', label=k)
        self.ax3.set_yscale('log')
        self.ax3.set_ylabel('duration [s]')
        self.ax3.legend()


# Copyright (C) 2020-2022 ImSwitch developers
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
