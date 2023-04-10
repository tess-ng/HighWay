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


def setup_log(log_name):
    # 创建logger对象, 传入logger名字
    logger = logging.getLogger(log_name)
    log_path = os.path.join(LOG_FILE_DIR, log_name)
    # 设置日志记录等级
    logger.setLevel(logging.INFO)
    # interval 滚动周期，
    # when="MIDNIGHT", interval=1 表示每天0点为更新点，每天生成一个文件
    # backupCount  表示日志保存个数
    file_handler = TimedRotatingFileHandler(filename=log_path, when="MIDNIGHT", interval=1, backupCount=7, encoding='utf-8')
    # filename="mylog" suffix设置，会生成文件名为mylog.2020-02-25.log
    file_handler.suffix = "%Y-%m-%d.log"
    # extMatch是编译好正则表达式，用于匹配日志文件名后缀
    # 需要注意的是suffix和extMatch一定要匹配的上，如果不匹配，过期日志不会被删除。
    file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")
    # 定义日志输出格式
    logFormatStr = '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
    file_handler.setFormatter(logging.Formatter(logFormatStr))
    logger.addHandler(file_handler)
    return logger


if __name__ == '__main__':
    logger = setup_log(log_name)
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
