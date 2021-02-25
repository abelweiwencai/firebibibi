import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
huobi_package_path = os.path.join(current_dir, 'huobi_Python')
sys.path.append(huobi_package_path)  # 火币的库加入包的搜索路径

from huobi.client.market import MarketClient
from huobi.constant import CandlestickInterval
from huobi.utils import LogInfo

from huobi.exception.huobi_api_exception import HuobiApiException
from huobi.model.market.candlestick_event import CandlestickEvent

class Strategy:
    DIRECTION_UP = 1
    DIRECTION_DOWN = 0
    DIRECTION_UNKNOWN = -1

    def __init__(self, symbol='ethusdt', interval=CandlestickInterval.MIN1, trigger_num=3) -> None:
        self.trigger_num = trigger_num  # 触发的连续次数

        self.direction = -1  # 0：下跌   1：上涨  -1：未知
        self.pre_direction = -1
        self.continuous_times = 0  # 连续数量
        self.cuttent_time = 0
        self.next_time = 0
        
        self.symbol = symbol
        self.interval = interval
        self.client = self._get_client()
        self.miss_cnt = 0
        self.pre_quote = None
        self.interval_seconds = self._get_interval_seconds()

    def _get_interval_seconds(self):
        if self.interval ==CandlestickInterval.MIN1:
            return 60 
        elif self.interval == CandlestickInterval.MIN5:
            return 60 * 5
        elif self.interval == CandlestickInterval.MIN15:
            return 60 * 15
        elif self.interval == CandlestickInterval.MIN60:
            return 60 * 60
        elif self.interval == CandlestickInterval.DAY1:
            return 60 * 60 * 24
        elif self.interval == CandlestickInterval.MON1:
            return 60 * 60 * 24 * 31
        elif self.interval == CandlestickInterval.WEEK1:
            return 60 * 60 * 24 * 7
        elif self.interval == CandlestickInterval.YEAR1:
            return 60 * 60 * 24 * 365
        return 60
        
    def _get_client(self):
        market_client = MarketClient(init_log=True)
        return market_client

    def get_quote(self):
        list_obj = self.client.get_candlestick(self.symbol, self.interval, 2)
        
        LogInfo.output(f"---- {self.interval} candlestick for {self.symbol} ----")
        LogInfo.output_list(list_obj)
        return list_obj
    
    def _handle_first_quote(self, quote):
        self.cuttent_time = quote.Id
        self.next_time = quote.id + self.interval_seconds
        self.pre_quote = quote
        if quote.Close > quote.Open:
            self.direction = self.DIRECTION_UP
        else:
            self.direction = self.DIRECTION_DOWN

        self.continuous_times = 1  # 连续数量
        self.cuttent_time = quote.Id
        self.next_time = quote.Id + self.interval_seconds
        self.pre_direction = self.direction


    def _handle_quote(self, quote):
        self.cuttent_time = quote.Id
            
        # 上涨：收盘 > 开盘
        # 下跌：收盘 < 开盘
        if quote.Close > quote.Open:
            self.direction = self.DIRECTION_UP
        else:
            self.direction = self.DIRECTION_DOWN
        

        if self.direction == self.pre_direction:
            self.continuous_times += 1
        else:
            self.continuous_times = 1

        self.pre_direction = self.direction
        self.pre_quote = quote
        self.next_time = quote.id + self.interval_seconds
        

        print(f'方向：{self.direction}，次数：{self.continuous_times}')


    def _get_direction_str(self):
        if self.direction == self.DIRECTION_UP:
            return '上涨'
        elif self.direction == self.DIRECTION_DOWN:
            return '下跌'
        else:
            return '未知方向'
        
        

        



    def run(self):
        # 获取n分钟的行情
        list_obj = self.get_quote()
        for obj in list_obj:
            self._handle_quote(obj)





if __name__ == '__main__':
    n = 3
    s = Strategy()
    s.run()










