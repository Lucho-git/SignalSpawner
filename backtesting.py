import pandas as pd
import config
import datetime
from collections import namedtuple
from dataclasses import dataclass
from dotmap import DotMap


# Initialize Binance client
client = config.get_binance_config()

# Define a namedtuple for storing the backtest result
BacktestResult = namedtuple('BacktestResult', [
    'exit_condition', 
    'entered_trade',
    'stop_price', 
    'stop_time', 
    'stop_percentage',  
    'take_profit_hits', 
    'take_profit_times', 
    'take_profit_percentages',
    'backtest_type',
    'results',
])

class Entry:
    def __init__(self, entry_price):
        self.hit: bool = None
        self.price: float = entry_price
        self.time_stamp: int = None
    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join([f'{k}={v}' for k, v in self.__dict__.items()])})"
class ProfitTarget:
    def __init__(self, price):
        self.hit: bool = None
        self.price: float = price
        self.time: str = None
        self.percentage: float = None
    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join([f'{k}={v}' for k, v in self.__dict__.items()])})"
class BackTestResult:
    def __init__(self, trade_type, entries, profit_targets):
        self.backtest_type = trade_type
        self.exit_condition = None
        self.entered = None
        self.entries = [Entry(e) for e in entries]
        self.profit_targets = [ProfitTarget(t) for t in profit_targets]
        self.exit_price = None
        self.exit_time = None
        self.exit_percentage = None
        self.results = None
    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join([f'{k}={v}' for k, v in self.__dict__.items()])})"


class BackTest:
    """
    This class implements a backtest of a trading strategy. It takes entry price, 
    take profit and stop loss levels, and fetches historical price data to simulate trades.

    Attributes:
    ----------
    """
    def __init__(self, entry_time, entries, take_profit_values, stop_loss, direction, symbol, interval):
        """ Initialize a BackTest instance. """
        self.signal_start_time = int(entry_time)
        self.entries = entries.copy()
        self.take_profit_values = take_profit_values.copy()
        self.stop_loss = stop_loss
        self.direction = direction
        self.symbol = symbol
        self.interval = interval
        self.signal_start_timeout_hours = 24 #trade times out in 24 hours
        self.signal_entered_timeout_hours = 168 #trade times out in 1 week

        # Sort take profit values based on direction
        if self.direction == 'LONG':
            self.take_profit_values.sort()
        elif self.direction == 'SHORT':
            self.take_profit_values.sort(reverse=True)

        # Get historical klines
        self.data = self.get_historical_klines()
        self.data['high'] = pd.to_numeric(self.data['high'])
        self.data['low'] = pd.to_numeric(self.data['low'])
        self.data['open'] = pd.to_numeric(self.data['low'])
        self.data['close'] = pd.to_numeric(self.data['low'])

        #print first price data
        first_price_value = self.data.iloc[0]['open']
        print(first_price_value)

    def get_historical_klines(self):
        """ Fetch historical klines (OHLCV data) for the given symbol, interval and time range. """
        start_str = self.signal_start_time
        end_time = self.signal_start_time + (1000 * 60 * 60 * 24 * 7)  # 1 weeks in milliseconds
        klines = client.get_historical_klines(self.symbol, self.interval, start_str, end_time)
        return pd.DataFrame(klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignored'])


    def calculate_profit_percentage(self, target_price):
        """ Calculate the profit percentage for a given target price based on the entry price and trade direction. """
        target_price = float(target_price)
        if self.direction == 'LONG':
            return round(((target_price - self.entry_price) / self.entry_price) * 100, 2)
        elif self.direction == 'SHORT':
            return round(((self.entry_price - target_price) / self.entry_price) * 100, 2)

    def calculate_profit_percentage_with_entry(self, entry_price, target_price):
        """ Calculate the profit percentage for a given target price based on the entry price and trade direction. """
        entry_price = float(entry_price)
        target_price = float(target_price)
        if self.direction == 'LONG':
            return round(((target_price - entry_price) / entry_price) * 100, 2)
        elif self.direction == 'SHORT':
            return round(((entry_price - target_price) / entry_price) * 100, 2)


    def backtest(self):
        result = BackTestResult('standard', [self.entries[0]], self.take_profit_values)#only 1 entry value for this backtest
        result.entries[0].time_stamp = None

        stop_loss = self.stop_loss
        take_profit_values = self.take_profit_values.copy()
        take_profit_hits = 0

        for index, row in self.data.iterrows():
            if result.entries[0].time_stamp is None:  # Update entry timestamp
                result.entries[0].time_stamp = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                result.entries[0].hit = True
                result.entered = True

            if result.entries[0].price is None: # Set entry price
                result.entries[0].entry_price = row['open']

            if (row['open_time'] - self.signal_start_time) / (1000 * 60 * 60) > self.signal_entered_timeout_hours:
                result.exit_condition = 'timeout'
                result.exit_price = row['close']
                result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, result.exit_price)
                return result

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                result.exit_condition = 'stop_loss'
                result.exit_price = self.stop_loss
                result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, result.exit_price)
                result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                return result

            for take_profit in list(take_profit_values):
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    result.profit_targets[take_profit_hits].hit = True
                    result.profit_targets[take_profit_hits].time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                    result.profit_targets[take_profit_hits].percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, take_profit)
                    take_profit_values.remove(take_profit)
                    take_profit_hits += 1

        result.exit_condition = 'ongoing'
        if take_profit_hits == len(self.take_profit_values):
            result.exit_condition = 'take_profit'
            result.exit_price = self.take_profit_values[-1]
            result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, result.exit_price)
            result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
        return result

    def backtest_with_entry(self):
        result = BackTestResult('standard_entry', self.entries, self.take_profit_values) #Multiple entries possible
        result.entries[0].time_stamp = None
        result.entered = False
        stop_loss = self.stop_loss
        take_profit_values = self.take_profit_values.copy()
        take_profit_hits = 0

        for index, row in self.data.iterrows():
            if (row['open_time'] - self.signal_start_time) / (1000 * 60 * 60) > self.signal_start_timeout_hours:
                if not result.entered:
                    result.exit_condition = 'not_entered_ever'
                    return result

                elif (row['open_time'] - self.signal_start_time) / (1000 * 60 * 60) > self.signal_entered_timeout_hours:
                    result.exit_condition = 'timeout'
                    result.exit_price = row['close']
                    result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                    result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, result.exit_price)
                    return result
                    

            # Checks to see if trade has hit the entry value yet
            if not result.entered and ((self.direction == 'LONG' and row['low'] <= result.entries[0].price) or (self.direction == 'SHORT' and row['high'] >= result.entries[0].price)):
                result.entered = True
                result.entries[0].hit = True
                result.entries[0].time_stamp = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)

            # If the trade has hit entry value
            if result.entered and take_profit_hits == 0:
                for entry in result.entries:
                    if entry.hit:
                        continue
                    if (self.direction == 'LONG' and row['low'] <= entry.price) or (self.direction == 'SHORT' and row['high'] >= entry.price):
                        entry.time_stamp = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                        entry.hit = True

            # If not entered, go next candle
            if not result.entered:
                continue

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                result.exit_condition = 'stop_loss'
                result.exit_price = stop_loss
                result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, stop_loss)
                return result

            for take_profit in list(take_profit_values):
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    result.profit_targets[take_profit_hits].hit = True
                    result.profit_targets[take_profit_hits].time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                    result.profit_targets[take_profit_hits].percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, take_profit)
                    take_profit_values.remove(take_profit)
                    take_profit_hits += 1

        result.exit_condition = 'ongoing'
        if take_profit_hits == len(self.take_profit_values):
            result.exit_condition = 'take_profit'
            result.exit_price = self.take_profit_values[-1]
            result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, result.exit_price)
            result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
        elif not result.entered:
            result.exit_condition = 'not_entered_yet'

        return result


    def backtest_with_trailing_stop(self, trailing_target=1):
        backtest_name = 'trailing_stop_' + str(trailing_target)
        result = BackTestResult(backtest_name, self.entries, self.take_profit_values)
        result.entries[0].time_stamp = None
        stop_loss = self.stop_loss
        take_profit_values = self.take_profit_values.copy()
        take_profit_hits = 0
        result.entered = False

        for index, row in self.data.iterrows():
            if (row['open_time'] - self.signal_start_time) / (1000 * 60 * 60) > self.signal_start_timeout_hours:
                if not result.entered:
                    result.exit_condition = 'not_entered_ever'
                    return result
                elif (row['open_time'] - self.signal_start_time) / (1000 * 60 * 60) > self.signal_entered_timeout_hours:
                    result.exit_condition = 'timeout'
                    result.exit_price = row['close']
                    result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                    result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, result.exit_price)
                    return result
                
            if not result.entered and ((self.direction == 'LONG' and row['low'] <= result.entries[0].price) or (self.direction == 'SHORT' and row['high'] >= result.entries[0].price)):
                result.entered = True
                result.entries[0].hit = True
                result.entries[0].time_stamp = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)

            if result.entered and take_profit_hits == 0:
                for entry in result.entries:
                    if entry.hit:
                        continue
                    if (self.direction == 'LONG' and row['low'] <= entry.price) or (self.direction == 'SHORT' and row['high'] >= entry.price):
                        entry.time_stamp = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                        entry.hit = True

            if not result.entered:
                continue

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                result.exit_condition = 'stop_loss'
                result.exit_price = stop_loss
                result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, stop_loss)
                return result
            
            for take_profit in list(take_profit_values):
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    result.profit_targets[take_profit_hits].hit = True
                    result.profit_targets[take_profit_hits].time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                    result.profit_targets[take_profit_hits].percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, take_profit)
                    take_profit_values.remove(take_profit)
                    take_profit_hits += 1

                    # move stop loss to entry price after hitting first profit target
                    if take_profit_hits == trailing_target:
                        stop_loss = result.entries[0].price

        result.exit_condition = 'ongoing'
        if take_profit_hits == len(self.take_profit_values):
            result.exit_condition = 'take_profit'
            result.exit_price = self.take_profit_values[-1]
            result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, result.exit_price)
            result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
        elif not result.entered:
            result.exit_condition = 'not_entered_yet'

        return result

    def backtest_with_progressive_stop(self, trailing_target=1):
        backtest_name = 'progressive_stop_' + str(trailing_target)
        result = BackTestResult(backtest_name, self.entries, self.take_profit_values)
        result.entries[0].time_stamp = None
        stop_loss = self.stop_loss
        take_profit_values = self.take_profit_values.copy()
        take_profit_hits = 0
        result.entered = False
        last_take_profit_hits = [None for _ in range(trailing_target)]  # Maintain list of last n take profit hits

        for index, row in self.data.iterrows():
            if (row['open_time'] - self.signal_start_time) / (1000 * 60 * 60) > self.signal_start_timeout_hours:
                if not result.entered:
                    result.exit_condition = 'not_entered_ever'
                    return result

                elif (row['open_time'] - self.signal_start_time) / (1000 * 60 * 60) > self.signal_entered_timeout_hours:
                    result.exit_condition = 'timeout'
                    result.exit_price = row['close']
                    result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                    result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, result.exit_price)
                    return result

            if not result.entered and ((self.direction == 'LONG' and row['low'] <= result.entries[0].price) or (self.direction == 'SHORT' and row['high'] >= result.entries[0].price)):
                result.entered = True
                result.entries[0].hit = True
                result.entries[0].time_stamp = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)

            if result.entered and take_profit_hits == 0:
                for entry in result.entries:
                    if entry.hit:
                        continue
                    if (self.direction == 'LONG' and row['low'] <= entry.price) or (self.direction == 'SHORT' and row['high'] >= entry.price):
                        entry.time_stamp = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                        entry.hit = True

            if not result.entered:
                continue

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                result.exit_condition = 'stop_loss'
                result.exit_price = stop_loss
                result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, stop_loss)
                return result

            for take_profit in list(take_profit_values):
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    result.profit_targets[take_profit_hits].hit = True
                    result.profit_targets[take_profit_hits].time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
                    result.profit_targets[take_profit_hits].percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, take_profit)
                    take_profit_values.remove(take_profit)
                    take_profit_hits += 1

                    last_take_profit_hits = last_take_profit_hits[1:] + [take_profit]

                    if take_profit_hits == trailing_target:
                        stop_loss = result.entries[0].price
                    elif take_profit_hits > trailing_target:
                        stop_loss = last_take_profit_hits[0]

        result.exit_condition = 'ongoing'
        if take_profit_hits == len(self.take_profit_values):
            result.exit_condition = 'take_profit'
            result.exit_price = self.take_profit_values[-1]
            result.exit_percentage = self.calculate_profit_percentage_with_entry(result.entries[0].price, result.exit_price)
            result.exit_time = round((row['open_time'] - self.signal_start_time) / (1000 * 60 * 60), 2)
        elif not result.entered:
            result.exit_condition = 'not_entered_yet'

        return result

    def print_result(self, result):
        print(result)
        print(f"\nRunning Backtest on {self.symbol}, with {result.backtest_type} strategy")
        entry_targets_hit = 0
        for e in result.entries:
            if e.hit:
                entry_targets_hit += 1
                print(f"Entry target of {e.price} was hit after {e.time_stamp} hours")
        print(f"Number of Entry Targets hit: {entry_targets_hit} / {len(self.entries)}")


        print(f"Exit Condition: {result.exit_condition}")
        print(f"Exit Price: {result.exit_price}")
        print(f"Exit Time: {result.exit_time}")
        print(f"Exit Percentage: {result.exit_percentage}")
        take_profit_hits = 0
        for t in result.profit_targets:
            if t.hit:
                take_profit_hits += 1
                print(f"Profit target of {t.price} was hit after {t.time} hours with a profit of {t.percentage}%")

        print(f"Number of Take Profits hit: {take_profit_hits} / {len(self.take_profit_values)}")

        print('\n')

def get_sample_long_data():
    return ['MAGICUSDT', client.KLINE_INTERVAL_5MINUTE, '1684059363825', 0.837, [0.84043,0.85021,0.85941,0.90288], 0.7661, 'LONG']

def get_sample_short_data():
    return ['COTIUSDT', client.KLINE_INTERVAL_5MINUTE, '1684385817070', 0.072, [0.07164, 0.07092, 0.0702, 0.06883, 0.06804], 0.078, 'SHORT']

def run_backtest_from_signal(signal):
    print('Running Backtests from signal:::::')
    backtest = BackTest(signal.time_generated, signal.entry, signal.take_profit, signal.stop_loss, signal.direction, signal.pair, client.KLINE_INTERVAL_5MINUTE)
    standard_backtest = backtest.backtest()
    backtest.print_result(standard_backtest)
    standard_entry_backtest = backtest.backtest_with_entry()
    backtest.print_result(standard_entry_backtest)
    trailing_stop_backtest = backtest.backtest_with_trailing_stop(2)
    backtest.print_result(trailing_stop_backtest)
    progressive_stop_backtest = backtest.backtest_with_progressive_stop(2)
    backtest.print_result(progressive_stop_backtest)
    signal.backtests = [standard_backtest, standard_entry_backtest, trailing_stop_backtest, progressive_stop_backtest]
    for backtest in signal.backtests:
        backtest.result = get_backtest_results(backtest)

def build_backtest_results_from_signal(signal):
    # Check if signal.backtest.result is empty or if signal.backtest.entered is False
    print(signal.backtests)
    if any(not backtest.entered or not backtest.result for backtest in signal.backtests):
        return None
    # print('Returning:', signal.backtests)
    return [
        DotMap({
            'pair': signal.pair,
            'source': signal.source,
            'direction': signal.direction,
            'results': [
                {
                    'type': backtest.backtest_type,
                    'result': backtest.result,
                    'start': backtest.entries[0].time_stamp,
                    'end': backtest.exit_time,
                }
            ]
        })
        for backtest in signal.backtests
    ]

def get_backtest_results(backtest):
    #exit if trade not concluded, or never began
    if (backtest.exit_condition == 'not_entered_yet' or backtest.exit_condition == 'ongoing' or not backtest.exit_condition):
        return None
    if backtest.exit_condition == 'not_entered_ever':
        return [0]* len(backtest.profit_targets)

    #Append all profit values
    result = []
    for p in backtest.profit_targets:
        if p.hit:
            result.append(DotMap(percentage=p.percentage, time=p.time))

    #Append exit values for remainder of array
    remaining_targets = len(backtest.profit_targets) - len(result)
    for i in range(remaining_targets):
        result.append(DotMap(percentage=backtest.exit_percentage, time=backtest.exit_time))

    return result

def run_backtest_from_trade(trade, signal):
    """Run specific backtest result for a quantifiable trade"""
    backtest = BackTest(signal.time_generated, [trade.entry], [trade.take_profit], trade.stop_loss, signal.direction, signal.pair, client.KLINE_INTERVAL_1MINUTE)

    # try:
    #     backtest = BackTest(signal.time_generated, trade.entry, [trade.take_profit], trade.stop_loss, signal.direction, signal.pair, client.KLINE_INTERVAL_1MINUTE)
    # except Exception as e:
    #     print(e)
    #     return
    print('Market_Price', signal.market_price)
    print(signal.source, type(trade))
    
    if signal.source == 'Hirn':
        results = backtest.backtest()
    else:
        results = backtest.backtest_with_entry()
    print('\n\n', trade)
    print(results)
    result = DotMap()
    if results.exit_condition == 'take_profit':
        result.result = 'profit'
        result.amount = results.exit_price
        result.percentage = results.exit_percentage
        result.time_complete = results.exit_time
    elif results.exit_condition == 'stop_loss':
        result.result = 'loss'
        result.amount = results.exit_price
        result.percentage = results.exit_percentage
        result.time_complete = results.exit_time
    elif results.exit_condition == 'timeout':
        result.result = 'timeout'
        result.amount = results.exit_price
        result.percentage = results.exit_percentage
        result.time_complete = results.exit_time
    elif results.exit_condition == 'not_entered_ever':
        result.result = 'not_entered_ever'
        result.amount = ''
        result.percentage = ''
        result.time_complete = ''
    elif results.exit_condition == 'ongoing':
        result.result = 'ongoing'
        result.amount = ''
        result.percentage = ''
        result.time_complete = ''
    return result


def run_backtest():
    """
    Run backtest for sample data using different strategies: standard, trailing stop, stop loss take profit.
    """
    backtesting_data = get_sample_long_data()

    symbol = backtesting_data[0]
    interval = backtesting_data[1]
    entry_time = backtesting_data[2]
    entry_price = backtesting_data[3]
    take_profit_values = backtesting_data[4]
    stop_loss = backtesting_data[5]
    direction = backtesting_data[6]

    backtest = BackTest(entry_time, entry_price, take_profit_values, stop_loss, direction, symbol, interval)


    result = backtest.backtest()
    backtest.print_result(result)

    result = backtest.backtest_with_trailing_stop()
    backtest.print_result(result)

    result = backtest.backtest_with_progressive_stop()
    backtest.print_result(result)











