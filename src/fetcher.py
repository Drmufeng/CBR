"""网页价格采集接口模块。

当前阶段不实现稳定采集逻辑，只保留统一接口，
便于后续接入 Selenium、requests 或第三方数据源。
"""


class PriceFetcher:
    """销售价格采集器接口。"""

    def fetch_by_model_name(self, model_name):
        """按车型名称获取销售价格。

        返回值建议统一为：
        {
            'success': bool,
            'price': float | None,
            'source': str,
            'collected_at': str,
            'message': str,
        }
        """
        return {
            'success': False,
            'price': None,
            'source': '未实现',
            'collected_at': '',
            'message': '当前仅预留采集接口，尚未实现自动抓取逻辑。',
        }

    def fetch_by_url(self, url):
        """按网页链接获取销售价格。"""
        return {
            'success': False,
            'price': None,
            'source': url,
            'collected_at': '',
            'message': '当前仅预留采集接口，尚未实现自动抓取逻辑。',
        }
