from PyQt5.QtCore import pyqtSlot

import numpy as np
from scipy.signal import correlate
import pdb
import pyqtgraph as pg

from imswitch.imcommon.model import initLogger
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal


class AlignOptController(ImConWidgetController):
    """ OPT scan controller.
    """
    sigImageReceived = Signal(str, np.ndarray)
    sigRequestSnap = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)
        self.optStack = np.ones((1, 1, 1))
        self.counterProj = np.ones((1, 1, 1))
        self.cor = None

        # Set up rotator in widget
        self._widget.initControls()
        self.isOptRunning = False

        # select detectors, this does not update if detector in
        # recording changes, right?
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        self._widget.scanPar['Rotator'].currentIndexChanged.connect(
            self.updateRotator)
        self._widget.scanPar['xShift'].valueChanged.connect(self.replotAll)
        self.updateShift()

        # get rotators
        self.getRotators()
        # populated widget comboBox, this triggers the updateRotator too
        for rotator in self.__rotators:
            self._widget.scanPar['Rotator'].addItem(rotator)

        # Connect widget signals
        self._widget.scanPar['StartButton'].clicked.connect(self.getProj)
        self._widget.scanPar['PlotHorCuts'].clicked.connect(self.plotHorCuts)

    def getProj(self):
        """ Reset and initiate Opt 0 and 180 degrees. """
        self.sigImageReceived.connect(self.processAlign)
        self._widget.scanPar['StartButton'].setEnabled(False)

        self._commChannel.sigSetSnapVisualization.emit(False)
        self.sigRequestSnap.connect(self._commChannel.sigSnapImg)
        self._commChannel.sigMemorySnapAvailable.connect(self.handleSnap)
        self._master.rotatorsManager[
            self.__rotators[self.motorIdx]]._motor.opt_step_done.connect(
                self.post_step)

        # equidistant steps for the OPT scan in absolute values.
        curPos = self._master.rotatorsManager[
            self.__rotators[self.motorIdx]]._motor.current_pos[0]
        counterPos = (curPos + self.__motor_steps//2) % self.__motor_steps
        self.opt_steps = [curPos, counterPos]
        self.__logger.debug(f'OPT steps: {self.opt_steps}')
        self.allFrames = []

        # run OPT
        if not self.isOptRunning:
            self.isOptRunning = True
            self.__currentStep = 0
            self.moveAbsRotator(self.__rotators[self.motorIdx],
                                self.opt_steps[self.__currentStep])

    @pyqtSlot()
    def moveAbsRotator(self, name, dist):
        """ Move a specific rotator to a certain position. """
        self.__logger.debug(f'Scancontroller, dist to move: {dist}')
        self._master.rotatorsManager[name].move_abs_steps(dist)
        self.__logger.debug('Scancontroller, after move.')

    def post_step(self, s):
        """Acquire image after motor step is done, stop OPT in
        case of last step,
        otherwise move motor again.
        """
        print(f'test string: {s}')

        # memory saving option needs to set in the recording controller.
        self.sigRequestSnap.emit()

        self.__currentStep += 1

        if self.__currentStep > len(self.opt_steps)-1:
            self.stopOpt()
        else:
            self.__logger.debug(f'post_step func, step{self.__currentStep}')
            self.moveAbsRotator(self.__rotators[self.motorIdx],
                                self.opt_steps[self.__currentStep])

    def stopOpt(self):
        """Stop OPT acquisition and enable buttons
        """
        self.isOptRunning = False
        self.optStack = np.array(self.allFrames)
        self.sigImageReceived.emit('OPT stack', self.optStack)

        self._master.rotatorsManager[
            self.__rotators[self.motorIdx]]._motor.opt_step_done.disconnect()
        self._widget.scanPar['StartButton'].setEnabled(True)
        self._logger.info("Align scan stopped.")
        self.sigRequestSnap.disconnect()

        self._commChannel.sigSetSnapVisualization.emit(True)

    ##################
    # Image handling #
    ##################
    def handleSnap(self, name, image, filePath, savedToDisk):
        """ Handles computation over a snapped image. Method is triggered by
        the `sigMemorySnapAvailable` signal.

        Args:
            name (`str`): key of the virtual table used to store images
                in RAM; format is "{filePath}_{channel}"
            image (`np.ndarray`): captured image snap data;
            filepath (`str`): path to the file stored on disk;
            savedToDisk (`bool`): weather the image is saved on
                disk (`True`) or not (`False`)
        """
        self._logger.debug('handling snap')
        self.frame = image
        if self.isOptRunning:
            self._logger.debug('appending snap')
            self.allFrames.append(image)

    def processAlign(self, name, arr):
        # subsample stack
        self.cor = AlignCOR(name, arr, self.xShift)
        self.cor.merge()
        self._widget.plotCounterProj(self.cor.merged)
        self.sigImageReceived.disconnect()

    def plotHorCuts(self):
        # query the line indeces to get hor cuts.
        self.horIdxList = self.getHorCutIdxs()
        # process the hor cuts
        self.cor.processHorCuts(self.horIdxList)

        # plotting
        self._widget.plotHorCuts.clear()  # clear plotWidget first
        self._widget.plotHorCuts.addLegend()
        self._widget.plotHorCuts.setTitle('Horizontal cuts', color='b')
        for i, px in enumerate(self.horIdxList):
            self._logger.info(f'plotting {i}, {px}')
            self._widget.plotHorCuts.plot(self.cor.horCuts[i][0],
                                          name=f'single {px}',
                                          pen=pg.mkPen('r'))
            self._widget.plotHorCuts.plot(self.cor.horCuts[i][1],
                                          name=f'merge {px}',
                                          pen=pg.mkPen('b'))

        # plot CC
        self._widget.plotCC.clear()  # clear plotWidget first
        self._widget.plotCC.addLegend()
        self._widget.plotCC.setTitle('Autocorrelation', color='b')
        for i, px in enumerate(self.horIdxList):
            self._widget.plotCC.plot(self.cor.crossCorr[i],
                                     name=f'{px}',
                                    #  pen=pg.mkPen('r'),
                                     )

    def replotAll(self):
        self.updateShift()
        print(self.xShift)
        try:
            self.cor._updateShift(self.xShift)
            self._widget.plotCounterProj(self.cor.merged)
            self.plotHorCuts()
            self._logger.info('Replotting')
        except TypeError:
            self._logger.info('No alignment stack available')        

    def saveScanParamsToFile(self, filePath: str) -> None:
        """ Saves the set scanning parameters to the specified file. """
        self.getParameters()

    def loadScanParamsFromFile(self, filePath: str) -> None:
        """ Loads scanning parameters from the specified file. """
        self.setParameters()

    def enableWidgetInterface(self, enableBool):
        self._widget.enableInterface(enableBool)

    def getHorCutIdxs(self):
        return [int(k) for k in self._widget.getHorCutsIdxList().split()]

    def updateShift(self):
        self.xShift = self._widget.scanPar['xShift'].value()

    def getRotationSteps(self):
        """ Get the total rotation steps. """
        return self._widget.getRotationSteps()

    def getRotators(self):
        """ Get a list of all rotators."""
        self.__rotators = self._master.rotatorsManager.getAllDeviceNames()

    def updateRotator(self):
        self.motorIdx = self._widget.getRotatorIdx()
        self.__motor_steps = self._master.rotatorsManager[
            self.__rotators[self.motorIdx]]._motor._steps_per_turn
        self.__logger.debug(
            f'Rotator: {self.__rotators[self.motorIdx]}, {self.__motor_steps} steps/rev',
            )


class AlignCOR():
    def __init__(self, name, img_stack, shift):
        self.name = name
        print('COR shape', img_stack.shape)
        if len(img_stack) != 2:
            raise IndexError('Check if Snap save mode contains save to display')
        self.img_stack_raw = img_stack
        self.shift = shift
        self.createShiftedStack()

        self.horCuts = []
        self.merged = None

    def _updateShift(self, value):
        self.shift = value
        self.recalcWithShift()

    def merge(self):
        self.merged = np.array(self.img_stack).mean(axis=0).astype(np.int16)

    def processHorCuts(self, idx_list):
        self.horCuts = []
        self.valid_idx = []
        for i in idx_list:
            try:
                # append tuple of first from stack and merged one at given idx
                self.horCuts.append((self.img_stack[0][i],
                                     self.merged[i]))
                self.valid_idx.append(i)
            except IndexError:
                # TODO: this has to update the valid idx list too
                print('Index out of range')

        # calculate cross-correlation
        self.crossCorr = []
        for i in self.valid_idx:
            self.crossCorr.append(
                correlate(self.img_stack[0][i], self.img_stack[1][i], mode='full'),
                )

    def recalcWithShift(self):
        """Called after shift value changes.
        """
        # first redo the stack
        self.createShiftedStack()

        # redo merge
        self.merge()

        # process cuts
        self.processHorCuts(self.valid_idx)

    def createShiftedStack(self):
        """This shfits the first of the two projections
        by self.shift
        """
        shifted = np.zeros(self.img_stack_raw[0].shape)

        if self.shift < 0:
            shifted[:, :self.shift] = np.roll(self.img_stack_raw[0],
                                              self.shift,
                                              axis=1,
                                              )[:, :self.shift]
        else:
            shifted[:, self.shift:] = np.roll(self.img_stack_raw[0],
                                              self.shift,
                                              axis=1,
                                              )[:, self.shift:]
        self.img_stack = [shifted[:, ::-1],
                          self.img_stack_raw[1]]


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
