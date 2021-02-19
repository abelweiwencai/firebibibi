import requests
from requests.api import get
import config as cfg
import urllib

class Client():

    def __init__(self, host) -> None:
        self.host = host

    def get_data(self, path):
        """
        调用接口获取数据
        """
        url = urllib.parse.urljoin(self.host, path)
        res = requests.get(url)
        return res.content.decode()

    def get_quote(self):
        """
        获取行情
        """
        path = '/api/v2/summary.json'
        return self.get_data(path)

    def get_currencies(self):
        """
        获取所有币种
        """
        path = '/v1/common/currencys'
        return self.get_data(path)
    

if __name__ == '__main__':
    c = Client(cfg.HOST)
    res = c.get_currencies()
    print(res)