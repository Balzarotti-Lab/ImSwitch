from abc import ABC, abstractmethod

from typing import Dict, List


class PositionerManager(ABC):
    """ Abstract base class for managers that control positioners. Each type of
    positioner corresponds to a manager derived from this class. """

    @abstractmethod
    def __init__(self, positionerInfo, name: str, initialPosition: Dict[str, float]):
        """
        Args:
            positionerInfo: See setup file documentation.
            name: The unique name that the device is identified with in the
              setup file.
            initialPosition: The initial position for each axis. This is a dict
              in the format ``{ axis: position }``.
        """

        self._positioner_info = positionerInfo
        self._position = initialPosition
        self.__axes = positionerInfo.axes
        self.__name = name

        self._speed = positionerInfo.managerProperties.get("initialSpeed", {axis: 0 for axis in self.__axes })
        self._is_homed = positionerInfo.managerProperties.get("initialIsHomed", {axis: 0 for axis in self.__axes })
        self._is_stopped = positionerInfo.managerProperties.get("initialIsStopped", {axis: False for axis in self.__axes })

        self.__for_positioning = positionerInfo.forPositioning
        self.__for_scanning = positionerInfo.forScanning
        if not positionerInfo.forPositioning and not positionerInfo.forScanning:
            raise ValueError('At least one of forPositioning and forScanning must be set in'
                             ' PositionerInfo.')

    @property
    def name(self) -> str:
        """ Unique positioner name, defined in the positioner's setup info. """
        return self.__name

    @property
    def position(self) -> Dict[str, float]:
        """ The position of each axis. This is a dict in the format
        ``{ axis: position }``. """
        return self._position

    @property
    def speed(self) -> Dict[str, float]:
        """ The speed of each axis. This is a dict in the format
        ``{ axis: position }``. """
        return self._speed

    @property
    def is_homed(self) -> Dict[str, bool]:
        """ The home of each axis. This is a dict in the format
        ``{ axis: homed }``. """
        return self._is_homed

    @property
    def is_stopped(self) -> Dict[str, bool]:
        """ The stop of each axis. This is a dict in the format
        ``{ axis: stopped }``. """
        return self._is_stopped

    @property
    def axes(self) -> List[str]:
        """ The list of axes that are controlled by this positioner. """
        return self.__axes

    @property
    def for_positioning(self) -> bool:
        """ Whether the positioner is used for manual positioning. """
        return self.__for_positioning

    @property
    def for_scanning(self) -> bool:
        """ Whether the positioner is used for scanning. """
        return self.__for_scanning

    @abstractmethod
    def move(self, dist: float, axis: str):
        """ Moves the positioner by the specified distance and returns the new
        position. Derived classes will update the position field manually. If
        the positioner controls multiple axes, the axis must be specified. """
        pass

    # @abstractmethod
    # def _set_position(self, pos, axis):
    #     pass

    def setPosition(self, position: float, axis: str):
        """ Adjusts the positioner to the specified position and returns the
        new position. Derived classes will update the position field manually.
        If the positioner controls multiple axes, the axis must be specified.
        """
        # result_pos = self._set_position(position, axis)
        # self._position[axis] = result_pos

        pass

    def finalize(self) -> None:
        """ Close/cleanup positioner. """
        pass


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