# -*- coding: utf-8 -*-
import os
from pathlib import Path
import sys

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from Tessng import *
from MyPlugin import *

if __name__ == '__main__':
    app = QApplication()

    workspace = os.fspath(Path(__file__).resolve().parent)
    config = {'__workspace':workspace,
              '__netfilepath':"C:/TESSNG_2.0.0/Example/教学视频案例-机动车交叉口__.tess",
              '__simuafterload': False,
              "__writesimuresult": False,
              '__custsimubysteps': True
              }
    plugin = MyPlugin()
    factory = TessngFactory()
    tessng = factory.build(plugin, config)
    if tessng is None:
        sys.exit(0)
    else:
        sys.exit(app.exec_())



