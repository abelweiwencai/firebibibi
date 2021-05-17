import time
from datetime import datetime
import config
from utils import DingTalkClient

from huobi.client.market import MarketClient
from huobi.constant import CandlestickInterval


def _get_interval_seconds(self):
        if self.interval == CandlestickInterval.MIN1:
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
class Direction:
    DIRECTION_UP = 1
    DIRECTION_DOWN = 0
    DIRECTION_UNKNOWN = -1

    @classmethod
    def get_direction_label(cls, direction):
        if cls.DIRECTION_UP == direction:
            return '上涨'
        elif cls.DIRECTION_DOWN == direction:
            return '下跌'
        else:
            return '未知'


class DirectionStaus:
    def __init__(self, direction=-1, continuous_times=0, low=0, high=0) -> None:
        self.direction = direction
        self.continuous_times = continuous_times  # 相同方向连续次数
        self.low = low
        self.high = high
        self.timestamp = 0

    @property
    def direction_label(self):
        return Direction.get_direction_label(self.direction)

    def echo(self, prefix=''):
        print(
            f'{prefix}方向：{self.direction_label}，' +
            f'{prefix}次数：{self.continuous_times}，' +
            f'{prefix}最高：{self.high}，' +
            f'{prefix}最低：{self.low}，' +
            f'{prefix}时间：{datetime.fromtimestamp(self.timestamp)}，' +
            '' 
        )

class StrategyDimension:
    def __init__(self, direction=Direction.DIRECTION_DOWN, trigger_times=4, reverse_trigger_times=1, remind_times=2) -> None:
        self.direction = direction
        self.trigger_times = trigger_times  # 连续次数后才能触发
        self.reverse_trigger_times = reverse_trigger_times  # 反向的出现几次后触发
        self.remain_times = remind_times  # 提醒下单的次数（一个tick提醒一次）
    
    @property
    def direction_label(self):
        return Direction.get_direction_label(self.direction)
    
class Strategy:
    def __init__(self, symbol='ethusdt', interval=CandlestickInterval.MIN1, dimension=None, min_get_interval=5) -> None:
        self.pre_direction_status = DirectionStaus()
        self.curr_direction_status = DirectionStaus()
        self.dimension = dimension or StrategyDimension()

        self.direction_changed = False
        self.has_new = False
        
        self.symbol = symbol
        self.interval = interval
        self.client = self._get_client()
        self.interval_seconds = _get_interval_seconds(self=self)
        self.min_get_interval = min_get_interval
        self.need_print = True
        self.ding_talk_client = DingTalkClient(url=config.REMIND_DING_TALK_WEBHOOK)
        self.ma = 0
        self.has_send_ma_msg = False
        self.curr_quote = None
        
    def _get_client(self):
        market_client = MarketClient(init_log=True)
        return market_client

    @staticmethod
    def _print_quote(quote, symbole):
        print(f'{symbole}，{datetime.fromtimestamp(quote.id)}，open：{quote.open}，close：{quote.close}，high：{quote.high}，low：{quote.low}')
    
    def _print_quote_list(self, quote_list):
        for q in quote_list:
            self._print_quote(q, self.symbol)

    def get_quote(self, size=2):
        print('开始请求行情')
        list_obj = self.client.get_candlestick(self.symbol, self.interval, size)
        print('请求行情成功')
        list_obj.reverse()
        self._print_quote_list(list_obj[-2:])
        self.curr_quote = list_obj[-2]
        return list_obj

    def _handle_quote(self, quote):
        if quote.id <= self.curr_direction_status.timestamp:
            old_time = datetime.fromtimestamp(self.curr_direction_status.timestamp)
            new_time = datetime.fromtimestamp(quote.id)
            print(f'没有新行情，行情时间{new_time}，原时间：{old_time}')
            self.has_new = False
            return
        self.has_new = True
        # 上涨：收盘 >= 开盘  下跌：收盘 < 开盘
        if quote.close >= quote.open:
            direction = Direction.DIRECTION_UP
        else:
            direction = Direction.DIRECTION_DOWN

        if direction == self.curr_direction_status.direction:  # 同向
            self.direction_changed = False
            self.curr_direction_status.continuous_times += 1

            self.curr_direction_status.low = min(quote.low, self.curr_direction_status.low)
            self.curr_direction_status.high = max(quote.low, self.curr_direction_status.high)

        else:
            self.direction_changed = True
            direction_status = DirectionStaus()
            direction_status.continuous_times += 1
            direction_status.direction = direction
            direction_status.low = quote.low
            direction_status.high = quote.high

            self.pre_direction_status = self.curr_direction_status
            self.curr_direction_status = direction_status

        self.curr_direction_status.timestamp = quote.id
        self.print_status()

    def print_status(self):
        self.pre_direction_status.echo(prefix='前')
        self.curr_direction_status.echo(prefix='现')

    def handle_trade_strategy(self):
        if self.pre_direction_status.direction != self.dimension.direction:
            self._print(f'行情方向不符，实际：{self.pre_direction_status.direction_label}，标准：{self.dimension.direction_label}')
            return

        if self.pre_direction_status.continuous_times < self.dimension.trigger_times:
            self._print(f'连续次数不够，实际：{self.pre_direction_status.continuous_times}，标准：{self.dimension.trigger_times}')
            return
        
        if self.curr_direction_status.continuous_times < self.dimension.reverse_trigger_times:
            self._print(f'反向连续次数不够，实际：{self.curr_direction_status.continuous_times}，标准：{self.dimension.reverse_trigger_times}')
            return

        if self.curr_direction_status.continuous_times > self.dimension.reverse_trigger_times + self.dimension.remain_times:
            print(f'超出下单提醒次数，不提醒')
        if self.curr_direction_status.continuous_times < self.dimension.reverse_trigger_times + self.dimension.remain_times:
            self._remind()
    
    def _remind(self):
        msg = f'{self.symbol} 卧槽好时机，下单了****************'
        self.ding_talk_client.send_to_group(content=msg, msg_type='text')
        print(msg)

    def _print(self, content):
        if self.need_print:
            print(content)

    def _get_sleep_seconds(self):
        curr_quote_timestamp = self.curr_direction_status.timestamp
        next_quote_timeStamp = curr_quote_timestamp + self.interval_seconds
        curr_timestamp = int(time.time())
        print('next time: ', datetime.fromtimestamp(next_quote_timeStamp))
        print('curr time: ', datetime.fromtimestamp(curr_timestamp))
        delta_seconds = next_quote_timeStamp + self.interval_seconds - curr_timestamp  # 当前时刻只能获取前一根线的数据，所以要再加一次 self.interval_seconds
        print('delta seconds: ', delta_seconds)
        if delta_seconds > self.interval_seconds:  # sleep时间小于一个tick时间，说明少了一根线，马上获取行情
            return 0
        else:
            return delta_seconds
    def get_ma(self, quote_list):
        close_list = []
        for q in quote_list:
            close_list.append(q.close)
        self.ma = sum(close_list) / len(close_list)
        return self.ma
    
    def handle_ma_strategy(self):
        print(f'MA：{self.ma}，CLOSE：{self.curr_quote.close}')
        if self.curr_quote.close > self.ma:
            if not self.has_send_ma_msg:
                msg = f'MA策略发，250分钟MA大于收盘价。250MA：{self.ma}，当前收盘：{self.curr_quote.close}'
                self.ding_talk_client.send_to_group(content=msg)
                self.has_send_ma_msg = True
        else:
            self.has_send_ma_msg = False

    def run(self):
        while True:
            try:
                list_obj = self.get_quote(size=251)
            except Exception as e:
                print(e)
                print(f'获取行情失败，{self.min_get_interval} 秒后再次获取。\n')
                time.sleep(self.min_get_interval)
                continue
            self.get_ma(list_obj[:-1])
            self.handle_ma_strategy()
            pre_close = list_obj[-2]  # 最后一条行情是当前分钟的，收盘价是当前价格，不准确，所以要获取前一分钟的收盘价计算
            self._handle_quote(pre_close)
            if self.has_new:
                self.handle_trade_strategy()
            seconds = self._get_sleep_seconds()
            if seconds < self.min_get_interval:
                print(f'限速了，{self.min_get_interval} 秒后获取行情。\n')
                time.sleep(self.min_get_interval)
            else:
                print(f'sleep: {seconds}')
                time.sleep(seconds)
            print()


if __name__ == '__main__':
    dimension = StrategyDimension(
        direction=Direction.DIRECTION_DOWN,
        trigger_times=4,
        reverse_trigger_times=1,
        remind_times=2
    )
    s = Strategy(
        symbol='ethusdt',
        interval=CandlestickInterval.MIN1,
        dimension=dimension,
        min_get_interval=2
    )
    s.run()
