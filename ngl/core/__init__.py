"""
核心工具模块
提供URL验证等核心功能
"""
import requests


def is_valid_link(url):
    """
    验证URL是否可访问
    
    Args:
        url: 要验证的URL字符串
        
    Returns:
        bool: 如果URL可访问返回True，否则返回False
    """
    try:
        r = requests.get(url, timeout=3)
    except requests.Timeout:
        return False
    return r.ok
