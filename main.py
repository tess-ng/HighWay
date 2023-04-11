# -*- coding: utf-8 -*-
import logging
import re
from logging.handlers import TimedRotatingFileHandler

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

# 初始化kafka对象
from Tessng import *

from utils.config import TESSNG_FILE_PATH, LOG_FILE_DIR, log_name
from utils.kafka_utils import MyProcess
from MyPlugin import *
from utils.log import setup_log


if __name__ == '__main__':
    logger = setup_log(os.path.join(LOG_FILE_DIR, 'main'), log_name, when="MIDNIGHT", interval=7, backupCount=2)
    logger.info('start process')

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
