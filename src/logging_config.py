"""
日志配置模块
提供统一的日志配置功能
"""

import logging
from pathlib import Path


def setup_logging(
    log_file: str = "steam_to_notion.log",
    level: int = logging.INFO,
    log_format: str = None,
) -> logging.Logger:
    """
    配置日志格式和输出目标

    Args:
        log_file: 日志文件名（默认: steam_to_notion.log）
        level: 日志级别（默认: logging.INFO）
        log_format: 自定义日志格式（可选）

    Returns:
        logging.Logger: 配置后的根logger
    """
    if log_format is None:
        log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    # 格式化器
    formatter = logging.Formatter(log_format)

    # 文件处理器
    log_path = Path(log_file)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # 根 logger 配置
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 清除已有处理器（避免重复）
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的logger

    Args:
        name: logger名称（通常使用 __name__）

    Returns:
        logging.Logger: 配置好的logger实例
    """
    return logging.getLogger(name)


def set_log_level(level: int):
    """
    设置日志级别

    Args:
        level: 日志级别（如 logging.DEBUG, logging.INFO）
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)


def add_file_handler(log_file: str, level: int = None):
    """
    添加额外的文件处理器

    Args:
        log_file: 日志文件路径
        level: 日志级别（可选，默认使用根logger级别）
    """
    root_logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    if level is not None:
        file_handler.setLevel(level)
    else:
        file_handler.setLevel(root_logger.level)

    root_logger.addHandler(file_handler)
