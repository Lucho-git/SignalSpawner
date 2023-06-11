import utility
import config
import datetime
import json
import math
import handle_signal_message
import traceback
from types import SimpleNamespace
from trade_conditions import SpotBasic, FutureBasic
'''
Defines a set of conditions and parameters for a given signal
These values should be static

'''
class Signal:
    def __init__(self, source, message, coin, base, entry, take_profit, stop_loss, direction, trades = [], market_price = None, time_generated = None):
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
        self.trades = trades
        self.market_price = market_price
        self.time_generated = time_generated
        if not trades:
            print('No Trades!')
            self.trades = trades
        else:
            new_trades = []
            try:
                for t in trades: 
                    try:
                        t.direction
                        print('FuturesBasic Trade')
                        new_futures = FutureBasic(t.source, t.time_generated, t.entry, t.take_profit, t.stop_loss, t.direction, t.leverage, backtest = t.backtest)
                        new_trades.append(new_futures)
                        print('FuturesBasicTrade Complete', new_futures)
                    except AttributeError:
                        print('SpotBasic Trade')
                        new_spot = SpotBasic(t.source, t.time_generated, t.entry, t.take_profit, t.stop_loss, backtest = t.backtest)
                        new_trades.append(new_spot)
                print('\n\nTrades recreated from database', new_trades)
                self.trades = new_trades
            except AttributeError as e:
                print(e)
                traceback.print_exc()
                self.trades = []

        if not market_price:
            self.market_price = self.get_market_price()
        if not time_generated:
            self.time_generated = utility.get_timestamp_now()
        self.convert_price_data_float() #Converts to float
        self.magnify_price_targets(self.market_price) #Adjusts the magnitude of data if it's wrong
        self.specify_price_data() #Ensures price data gets through exchange precision filters


    @staticmethod
    def deep_namespace(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k: Signal.deep_namespace(v) for k, v in d.items()})
        elif isinstance(d, list):
            return [Signal.deep_namespace(item) for item in d]
        else:
            return d


    @classmethod
    def from_data(cls, data):
        '''Clones a new signal from json signal data'''
        signal_data = cls.deep_namespace(data)
        try: 
            signal_data.trades
        except AttributeError:
            signal_data.trades = []
        return cls(signal_data.source, signal_data.message, signal_data.coin, signal_data.base, signal_data.entry, signal_data.take_profit, signal_data.stop_loss, signal_data.direction, market_price=signal_data.market_price, time_generated=signal_data.time_generated, trades=signal_data.trades)
        

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
                "trades": str(self.trades), 
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


    def check_data_types(self):
        for key, value in vars(self).items():
            print(f"{key}: {value} (type: {type(value)})")    
            if (isinstance(value, list)):
                for v in value:
                    print(v, type(v))


    def specify_price_data(self):
        '''Ensures binance will accept all price values for making orders'''
        self.entry = utility.sanitise_price_data(self.pair, self.entry)
        self.take_profit = utility.sanitise_price_data(self.pair, self.take_profit)
        self.stop_loss = utility.sanitise_price_data(self.pair, self.stop_loss)

    
    def convert_price_data_float(self):
        for i in range(len(self.entry)):
            self.entry[i] = float(self.entry[i])
        for i in range(len(self.take_profit)):
            self.take_profit[i] = float(self.take_profit[i])
        self.stop_loss = float(self.stop_loss)


    def magnify_price_targets(self, market_price):
        for i in range(len(self.entry)):
            self.entry[i] = self.adjust_magnitude(self.entry[i], market_price)

        for i in range(len(self.take_profit)):
            self.take_profit[i] = self.adjust_magnitude(self.take_profit[i], market_price)

        self.stop_loss = self.adjust_magnitude(self.stop_loss, market_price)


    def adjust_magnitude(self, original, market_price):
        # Identify the closest power of 10 that brings the original number's magnitude close to example's magnitude
        changed = original
        power = round(math.log10(market_price / original))
        # Scale the original number
        scaled = original * 10 ** power
        # Get the number of decimal places in the example
        num_decimal_places_example = len(str(market_price).split(".")[-1])
        # Adjust the decimal places of the original to match the example
        original = round(scaled, num_decimal_places_example)
        # If the rounded number is not equal to the scaled number, then keep the additional decimal places in the original number
        if original != scaled:
            original = scaled
        if(not(changed==original)):
           print('Changed', changed, 'To', original)
        return original


    def get_market_price(self):
        '''Gets current price from binanace'''
        return float(config.get_binance_config().get_symbol_ticker(symbol=self.pair)['price'])
    
    def generate_trades(self, override = False):
        if override:
            self.trades = handle_signal_message.trades_from_signal(self, False)
        else:
            if self.trades:
                return
            else:
                print('\nGenerating New Trade')
                self.trades = handle_signal_message.trades_from_signal(self, False)

    def generate_filtered_trades(self):
        self.trades = handle_signal_message.trades_from_signal(self, True)

    def backtest_trades(self):
        if not self.trades:
            raise Exception('No trades to backtest')
        for t in self.trades:
            t.run_backtest(self)