import utility
import config
import datetime
import json
'''
Defines a set of conditions and parameters for a given signal
These values should be static

'''
class Signal:
    def __init__(self, source, signal, coin, base, entry, take_profit, stop_loss, direction):
        self.source = source
        self.signal = signal
        self.coin = coin
        self.base = base
        self.pair = coin+base
        self.entry = entry
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.direction = direction
        self.market_price = self.get_market_price()
        self.time_generated = utility.get_timestamp_now()

    def __str__(self) -> str:
        return str({
                "source": self.source,
                "coin": self.coin,
                "base": self.base,
                "pair": self.pair,
                "entry": self.entry,
                "profit_targets": self.take_profit,
                "stop_loss": self.stop_loss,
                "direction": self.direction,
                "market_price": self.market_price,
                "time_generated": self.time_generated
                })

    def get_json(self):
        input_dict = self.convert_dict(self.__dict__)
        signal_json = json.dumps(input_dict)
        return signal_json

    def convert_dict(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
        elif isinstance(obj, type):
            return obj.__name__
        elif isinstance(obj, dict):
            return {k: self.convert_dict(v) for k, v in obj.items()}
        elif hasattr(obj, '__dict__'):
            return self.convert_dict(vars(obj))
        elif hasattr(obj, '__iter__') and not isinstance(obj, str):
            return [self.convert_dict(v) for v in obj]
        else:
            return obj


    def decode_unicode_escapes(self, s):
        return s.encode('utf-8').decode('unicode_escape')


    def get_market_price(self):
        '''Gets current price from binanace'''
        return float(config.get_binance_config().get_symbol_ticker(symbol=self.pair)['price'])