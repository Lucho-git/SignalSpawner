import utility
import config
import datetime
import json
'''
Defines a set of conditions and parameters for a given signal
These values should be static

'''
class Signal:
    def __init__(self, source, message, coin, base, entry, take_profit, stop_loss, direction, market_price = None, time_generated = None):
        #Validate Signal
        if not take_profit:
            raise TypeError('No Take Profit value')
        if not stop_loss:
            raise TypeError('No Stop Loss value')

        self.source = source
        self.message = message
        self.coin = coin
        self.base = base
        self.pair = coin+base
        self.entry = entry
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.direction = direction
        if not market_price:
            self.market_price = self.get_market_price()
        if not time_generated:
            self.time_generated = utility.get_timestamp_now()
        self.convert_price_data_float()

    def __str__(self) -> str:
        return str({
                "source": self.source,
                "coin": self.coin,
                "base": self.base,
                "pair": self.pair,
                "entry": self.entry,
                "take_profit": self.take_profit,
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

    def convert_price_data_float(self):
        for i in range(len(self.entry)):
            self.entry[i] = float(self.entry[i])
        for i in range(len(self.take_profit)):
            self.take_profit[i] = float(self.take_profit[i])
        self.stop_loss = float(self.stop_loss)


    def check_data_types(self):
        for key, value in vars(self).items():
            print(f"{key}: {value} (type: {type(value)})")    
            if (isinstance(value, list)):
                for v in value:
                    print(v, type(v))

    def get_market_price(self):
        '''Gets current price from binanace'''
        return float(config.get_binance_config().get_symbol_ticker(symbol=self.pair)['price'])