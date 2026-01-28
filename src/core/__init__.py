"""
核心工具模块
提供URL验证等核心功能
"""
import requests


def is_valid_link(url, verify_ssl=True):
    """
    验证URL是否可访问

    Args:
        url: 要验证的URL字符串
        verify_ssl: 是否验证SSL证书（企业环境可设为False）

    Returns:
        bool: 如果URL可访问返回True，否则返回False
    """
    try:
        r = requests.get(url, timeout=3, verify=verify_ssl)
        return r.ok
    except (requests.Timeout, requests.ConnectionError, requests.RequestException):
        return False
