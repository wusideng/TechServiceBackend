import os
import logging
from logging.handlers import RotatingFileHandler

from config import is_dev


logging.basicConfig(
    level=logging.INFO if is_dev else logging.INFO,  # 日志级别
    format="%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        RotatingFileHandler(
            os.path.join(os.getcwd(), "log.txt"),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=0,  # 保留5个备份文件
            encoding="utf-8",
        ),  # 输出到文件，最大10MB
    ],
)

# 创建logger
logger = logging.getLogger(__name__)
