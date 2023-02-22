# -*- coding: utf-8 -*-

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

# 初始化kafka对象
from Tessng import *

from utils.config import TESSNG_FILE_PATH
from utils.kafka_utils import MyProcess
from MyPlugin import *


if __name__ == '__main__':
    config_module = __import__('utils.config', fromlist=('config',))
    my_process = MyProcess(config_module)
    sys.modules["__main__"].__dict__['myprocess'] = my_process

    app = QApplication()

    workspace = os.fspath(Path(__file__).resolve().parent)
    config = {'__workspace': workspace,
              '__netfilepath': TESSNG_FILE_PATH,
              '__simuafterload': True,
              "__writesimuresult": False,
              '__custsimubysteps': True,
              '__timebycpu': True
              }
    plugin = MyPlugin()
    factory = TessngFactory()
    tessng = factory.build(plugin, config)

    if tessng is None:
        sys.exit(0)
    else:
        sys.exit(app.exec_())
