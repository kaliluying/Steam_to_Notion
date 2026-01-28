"""
Steam 微交易（MicroTxn）接口封装

提供初始化订单、查询与退款等能力。
"""

__author__ = "andrew"

from .core import APIConnection

import uuid


class SteamIngameStore(object):
    """Steam 游戏内商店微交易接口封装类。"""

    def __init__(self, appid, debug=False):
        """
        初始化微交易接口，debug=True 使用沙盒环境。

        :param appid: 应用的 Steam AppID。
        :param debug: 是否使用沙盒环境进行测试。
        """
        self.appid = appid
        self.interface = "ISteamMicroTxnSandbox" if debug else "ISteamMicroTxn"

    def get_user_microtxh_info(self, steamid):
        """
        获取用户微交易信息。

        :param steamid: 用户的 SteamID。
        :return: 用户的微交易信息。
        """
        return APIConnection().call(
            self.interface, "GetUserInfo", "v1", steamid=steamid, appid=self.appid
        )

    def init_purchase(
        self,
        steamid,
        itemid,
        amount,
        itemcount=1,
        language="en",
        currency="USD",
        qty=1,
        description="Some description",
    ):
        """
        初始化订单，返回交易 ID 与支付 URL。

        :param steamid: 购买用户的 SteamID。
        :param itemid: 商品 ID。
        :param amount: 金额（以分为单位）。
        :param itemcount: 商品数量，默认为 1。
        :param language: 语言设置，默认为 "en"。
        :param currency: 货币代码，默认为 "USD"。
        :param qty: 数量，默认为 1。
        :param description: 商品描述，默认为 "Some description"。
        :return: 包含交易 ID 和支付 URL 的响应。
        """
        params = {
            "steamid": steamid,
            "itemid[0]": itemid,
            "amount[0]": amount,
            "appid": self.appid,
            "orderid": uuid.uuid1().int >> 64,
            "itemcount": itemcount,
            "language": language,
            "currency": currency,
            "qty[0]": qty,
            "description[0]": description,
        }
        return APIConnection().call(
            self.interface, "InitTxn", "v3", method="POST", **params
        )

    def query_txh(self, orderid):
        """
        查询订单状态。

        :param orderid: 订单 ID。
        :return: 订单状态信息。
        """
        return APIConnection().call(
            self.interface, "QueryTxn", "v1", appid=self.appid, orderid=orderid
        )

    def refund_txh(self, orderid):
        """
        发起退款。

        :param orderid: 订单 ID。
        :return: 退款操作的结果。
        """
        return APIConnection().call(
            self.interface,
            "RefundTxn",
            "v1",
            method="POST",
            appid=self.appid,
            orderid=orderid,
        )

    def finalize_txh(self, orderid):
        """
        完成订单（标记已处理）。

        :param orderid: 订单 ID。
        :return: 完成订单操作的结果。
        """
        return APIConnection().call(
            self.interface,
            "FinalizeTxn",
            "v1",
            method="POST",
            appid=self.appid,
            orderid=orderid,
        )
