import logging
import os
import re

from logging.handlers import TimedRotatingFileHandler
from utils.config import LOG_FILE_DIR, log_name


def setup_log(log_name, when="D", interval=1, backupCount=7):  # 切割单位，频率以及保存的时间
    # 创建logger对象, 传入logger名字
    logger = logging.getLogger(log_name)
    log_path = os.path.join(LOG_FILE_DIR, log_name)
    # 设置日志记录等级
    logger.setLevel(logging.INFO)
    # when 单位时间 "S": Seconds, "M": Minutes, "H": Hours, "D": Days, "W": Week
    # interval 滚动周期，指interval个when后，进行切割
    # when="MIDNIGHT", interval=1 表示每天0点为更新点，每天生成一个文件
    # backupCount  表示日志保存个数
    file_handler = TimedRotatingFileHandler(filename=log_path, when=when, interval=interval, backupCount=backupCount,
                                            encoding='utf-8')
    # filename="mylog" suffix设置，会生成文件名为 mylog.2020-02-25.log
    file_handler.suffix = "%Y-%m-%d.log"
    # extMatch是编译好正则表达式，用于匹配日志文件名后缀
    # 需要注意的是suffix和extMatch一定要匹配的上，如果不匹配，过期日志不会被删除。
    file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")
    # 定义日志输出格式
    logFormatStr = '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
    file_handler.setFormatter(logging.Formatter(logFormatStr))
    logger.addHandler(file_handler)
    return logger
