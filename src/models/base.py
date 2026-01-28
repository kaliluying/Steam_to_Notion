"""
基础模型类
提供从字典加载对象的基础功能
"""

import logging
import typing as tp

logger = logging.getLogger(__name__)


class BaseModel:
    """
    基础模型类
    所有数据模型的基类，提供从字典加载对象的功能
    """

    @classmethod
    def load(cls, d: tp.Optional[dict]):
        """
        从字典加载模型对象

        Args:
            d: 包含模型数据的字典，如果为None或非字典则返回None

        Returns:
            模型实例或None
        """
        if d is None or not isinstance(d, dict):
            return None
        try:
            return cls(**d)
        except (TypeError, KeyError) as e:
            logger.warning(f"加载 {cls.__name__} 失败: {e}")
            return None
