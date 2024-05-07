import json
import os

import numpy as np

from imswitch.imcommon.model import dirtools, initLogger
from imswitch.imcontrol.model.managers.SLM_PCIeManager import MaskMode, Direction
from ..basecontrollers import ImConWidgetController


class SLM_PCIeController(ImConWidgetController):
    """Linked to SLMWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        self.slmDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_slm')
        if not os.path.exists(self.slmDir):
            os.makedirs(self.slmDir)

        if self._setupInfo.slm_PCIe is None:
            self._widget.replaceWithError('SLM is not configured in your setup file.')
            return

        self._widget.initSLMDisplay(self._setupInfo.slm_PCIe.monitorIdx)

        # Connect CommunicationChannel signals
        self._commChannel.sigSLMMaskUpdated.connect(lambda mask: self.displayMask(mask))

        # Connect SLMWidget signals
        self._widget.controlPanel.upButton.clicked.connect(
            lambda: self.moveMask(Direction.Up))  # change 'up' to (x,y)=(0,1)
        self._widget.controlPanel.downButton.clicked.connect(
            lambda: self.moveMask(Direction.Down))  # change 'down' to (x,y)=(0,-1)
        self._widget.controlPanel.leftButton.clicked.connect(
            lambda: self.moveMask(Direction.Left))  # change 'left' to (x,y)=(-1,0)
        self._widget.controlPanel.rightButton.clicked.connect(
            lambda: self.moveMask(Direction.Right))  # change 'right' to (x,y)=(1,0)

        self._widget.controlPanel.saveButton.clicked.connect(self.saveParams)
        self._widget.controlPanel.loadButton.clicked.connect(self.loadParams)

        self._widget.controlPanel.donutButton.clicked.connect(lambda: self.setMask(MaskMode.Donut))
        self._widget.controlPanel.tophatButton.clicked.connect(
            lambda: self.setMask(MaskMode.Tophat))

        self._widget.controlPanel.blackButton.clicked.connect(lambda: self.setMask(MaskMode.Black))
        self._widget.controlPanel.gaussianButton.clicked.connect(
            lambda: self.setMask(MaskMode.Gauss))

        self._widget.controlPanel.halfButton.clicked.connect(lambda: self.setMask(MaskMode.Half))
        self._widget.controlPanel.quadrantButton.clicked.connect(
            lambda: self.setMask(MaskMode.Quad))
        self._widget.controlPanel.hexButton.clicked.connect(lambda: self.setMask(MaskMode.Hex))
        self._widget.controlPanel.splitbullButton.clicked.connect(
            lambda: self.setMask(MaskMode.Split))

        self._widget.applyChangesButton.clicked.connect(self.applyParams)
        self._widget.sigSLMDisplayToggled.connect(self.toggleSLMDisplay)
        self._widget.sigSLMMonitorChanged.connect(self.monitorChanged)

        # Initial SLM display
        self.displayMask(self._master.slm_PCIeManager.maskCombined)

    def toggleSLMDisplay(self, enabled):
        self._widget.setSLMDisplayVisible(enabled)

    def monitorChanged(self, monitor):
        self._widget.setSLMDisplayMonitor(monitor)

    def displayMask(self, maskCombined):
        """ Display the mask in the SLM display. Originates from slmPy:
        https://github.com/wavefrontshaping/slmPy """

        arr = maskCombined.image()

# myAdd
        self._master.slm_PCIeManager.upload_img(arr)                                # change for SLM-PCIe
# ----------------------------------------

        # # Padding: Like they do in the software
        # pad = np.zeros((1024, 8), dtype=np.uint8)
        # arr = np.append(arr, pad, 1)

        # Create final image array
        h, w = arr.shape[0], arr.shape[1]

        if len(arr.shape) == 2:
            # Array is grayscale
            arrGray = arr.copy()
            arrGray.shape = h, w, 1
            displImg = np.concatenate((arrGray, arrGray, arrGray), axis=2)
            self._widget.updateSLMDisplay(displImg)
        else:
            displImg = arr
            self._widget.updateSLMDisplay(displImg)



    # Button pressed functions
    def moveMask(self, direction):
        amount = self._widget.controlPanel.incrementSpinBox.value()
        mask = self._widget.controlPanel.maskComboBox.currentIndex()
        self._master.slm_PCIeManager.moveMask(mask, direction, amount)
        image = self._master.slm_PCIeManager.update(maskChange=True, aberChange=True, tiltChange=True)
        self.updateDisplayImage(image)

    def saveParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        if obj == 'No objective':
            self.__logger.error('You have to choose an objective from the drop down menu.')
            return
        elif obj == 'Oil':
            filename = 'info_oil.json'
        elif obj == 'Glycerol':
            filename = 'info_glyc.json'
        else:
            raise ValueError(f'Unsupported objective "{obj}"')

        slm_info_dict = self.getInfoDict(self._widget.slmParameterTree.p,
                                         self._widget.aberParameterTree.p,
                                         self._master.slm_PCIeManager.getCenters())
        with open(os.path.join(self.slmDir, filename), 'w') as f:
            json.dump(slm_info_dict, f, indent=4)
        self.__logger.info(f'Saved SLM parameters for {obj} objective.')

    def getInfoDict(self, generalParams=None, aberParams=None, centers=None):
        state_general = None
        state_pos = None
        state_aber = None

        if generalParams is not None:
            # create dict for general params
            generalparamnames = ["radius", "sigma", "rotationAngle", "tiltAngle"]
            state_general = {generalparamname: float(
                generalParams.param("general").param(generalparamname).value()) for generalparamname
                             in generalparamnames}

        if aberParams is not None:
            # create dict for aberration params
            masknames = ["left", "right"]
            aberparamnames = ["tilt", "tip", "defocus", "spherical", "verticalComa",
                              "horizontalComa", "verticalAstigmatism", "obliqueAstigmatism"]
            state_aber = dict.fromkeys(masknames)
            for maskname in masknames:
                state_aber[maskname] = {
                    aberparamname: float(aberParams.param(maskname).param(aberparamname).value())
                    for aberparamname in aberparamnames}

        if centers is not None:
            # create dict for position params
            state_pos = dict.fromkeys(masknames)
            for maskname in masknames:
                state_pos[maskname] = {
                    "xcenter": int(centers[maskname][0]),
                    "ycenter": int(centers[maskname][1])
                }

        info_dict = {
            "general": state_general,
            "position": state_pos,
            "aber": state_aber
        }
        return info_dict

    def loadParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        if obj == 'No objective':
            self.__logger.error('You have to choose an objective from the drop down menu.')
            return
        elif obj == 'Oil':
            filename = 'info_oil.json'
        elif obj == 'Glycerol':
            filename = 'info_glyc.json'
        else:
            raise ValueError(f'Unsupported objective "{obj}"')

        with open(os.path.join(self.slmDir, filename), 'rb') as f:
            slm_info_dict = json.load(f)
            state_general = slm_info_dict["general"]
            state_pos = slm_info_dict["position"]
            state_aber = slm_info_dict["aber"]

        self.setParamTree(state_general=state_general, state_aber=state_aber)
        self._master.slm_PCIeManager.setGeneral(state_general)
        self._master.slm_PCIeManager.setCenters(state_pos)
        self._master.slm_PCIeManager.setAberrationFactors(state_aber)
        self._master.slm_PCIeManager.saveState(state_general, state_pos, state_aber)
        image = self._master.slm_PCIeManager.update(maskChange=True, tiltChange=True, aberChange=True)
        self.updateDisplayImage(image)

    def setParamTree(self, state_general, state_aber):
        generalParams = self._widget.slmParameterTree.p
        aberParams = self._widget.aberParameterTree.p

        generalparamnames = ["radius", "sigma", "rotationAngle", "tiltAngle"]
        for generalparamname in generalparamnames:
            generalParams.param("general").param(generalparamname).setValue(
                float(state_general[generalparamname])
            )

        masknames = ["left", "right"]
        aberparamnames = ["tilt", "tip", "defocus", "spherical", "verticalComa", "horizontalComa",
                          "verticalAstigmatism", "obliqueAstigmatism"]
        for maskname in masknames:
            for aberparamname in aberparamnames:
                aberParams.param(maskname).param(aberparamname).setValue(
                    float(state_aber[maskname][aberparamname])
                )

    def setMask(self, maskMode):
        # 0 = donut (left), 1 = tophat (right)
        mask = self._widget.controlPanel.maskComboBox.currentIndex()
        if maskMode != MaskMode.Black:
            slm_info_dict = self.getInfoDict(generalParams=self._widget.slmParameterTree.p,
                                            aberParams=self._widget.aberParameterTree.p)
            self.applyAberrations(slm_info_dict["aber"], mask)
        self._master.slm_PCIeManager.setMask(mask, maskMode)
        image = self._master.slm_PCIeManager.update(maskChange=True, tiltChange=True, aberChange=True)
        self.updateDisplayImage(image)

    def applyParams(self):
        slm_info_dict = self.getInfoDict(generalParams=self._widget.slmParameterTree.p,
                                         aberParams=self._widget.aberParameterTree.p)
        self.applyGeneral(slm_info_dict["general"])
        self.applyAberrations(slm_info_dict["aber"])
        image = self._master.slm_PCIeManager.update(maskChange=True, tiltChange=True, aberChange=True)
        self.updateDisplayImage(image)
        self._master.slm_PCIeManager.saveState(state_general=slm_info_dict["general"],
                                          state_aber=slm_info_dict["aber"])

    def applyGeneral(self, info_dict):
        self._master.slm_PCIeManager.setGeneral(info_dict)

    def applyAberrations(self, info_dict, mask=None):
        self._master.slm_PCIeManager.setAberrations(info_dict, mask)

    def updateDisplayImage(self, image):
        image = np.fliplr(image.transpose())
        self._widget.img.setImage(image, autoLevels=True, autoDownsample=False)


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
