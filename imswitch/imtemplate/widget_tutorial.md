# creating Widget

1. In the file `view/widgets/FFTWidget.py` create class FFTWidget(Widget), where from `.basewidgets import Widget`
2.  to the `view/widgets/__init__.py` add `from .FFTWidget import FFTWidget`
3. To the `controller/controllers/__init__.py` add `from .FFTController import FFTController`
4. In the file `controller/controllers/FFTController.py` create `class FFTController(WidgetController)`, where `from ..basecontrollers import WidgetController`
5. Add GUI elements to the Widget class
6. Go to the `view/ImConMainView.py` and add a line to the rightDockInfo with the widgets name

## What did I do differently

- In the HelloWidget.py I havent imported following (what is comented), it was causing errors
```python
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

# from imswitch.imcommon.view.guitools import pyqtgraphtools
# from imswitch.imcontrol.view import guitools

from .basewidgets import Widget
```
- I've coped from the other modules the `basewidgets.py`.
- pydantic library for my napari 0.4.7 needed a specific version to be >=1.8.1
- In the `ImTempMainView.py` the following pkg hasnt been imported
```python
from dataclasses import dataclass

from pyqtgraph.dockarea import Dock, DockArea
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.model import initLogger
from imswitch.imcommon.view import PickDatasetsDialog
from . import widgets
# from .PickSetupDialog import PickSetupDialog
```
