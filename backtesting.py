import pandas as pd
import config
import datetime
from collections import namedtuple

# Initialize Binance client
client = config.get_binance_config()

# Define a namedtuple for storing the backtest result
BacktestResult = namedtuple('BacktestResult', [
    'exit_condition', 
    'stop_price', 
    'stop_time', 
    'stop_percentage', 
    'take_profit_hits', 
    'take_profit_times', 
    'take_profit_percentages',
    'backtest_type',
])


class BackTest:
    """
    This class implements a backtest of a trading strategy. It takes entry price, 
    take profit and stop loss levels, and fetches historical price data to simulate trades.

    Attributes:
    ----------
    """
    def __init__(self, entry_time, entry_price, take_profit_values, stop_loss, direction, symbol, interval):
        """ Initialize a BackTest instance. """
        self.entry_time = int(entry_time)
        self.entry_price = entry_price
        self.take_profit_values = take_profit_values.copy()  
        self.stop_loss = stop_loss
        self.direction = direction
        self.symbol = symbol
        self.interval = interval
        self.entry_timeout_hours = 168 #trade times out in 24 hours

        # Sort take profit values based on direction
        if self.direction == 'LONG':
            self.take_profit_values.sort()
        elif self.direction == 'SHORT':
            self.take_profit_values.sort(reverse=True)

        # Get historical klines
        self.data = self.get_historical_klines()
        self.data['high'] = pd.to_numeric(self.data['high'])
        self.data['low'] = pd.to_numeric(self.data['low'])

        #print first price data
        first_price_value = self.data.iloc[0]['open']
        print(first_price_value)

    def get_historical_klines(self):
        """ Fetch historical klines (OHLCV data) for the given symbol, interval and time range. """
        start_str = self.entry_time
        end_time = self.entry_time + (1000 * 60 * 60 * 24 * 7)  # 1 weeks in milliseconds
        klines = client.get_historical_klines(self.symbol, self.interval, start_str, end_time)
        return pd.DataFrame(klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignored'])


    def calculate_profit_percentage(self, target_price):
        """ Calculate the profit percentage for a given target price based on the entry price and trade direction. """
        if self.direction == 'LONG':
            return round(((target_price - self.entry_price) / self.entry_price) * 100, 2)
        elif self.direction == 'SHORT':
            return round(((self.entry_price - target_price) / self.entry_price) * 100, 2)


    def backtest(self):
        #Timeout
        #Take_profit
        #Stop_loss

        stop_loss = self.stop_loss  # Create a copy of stop_loss
        take_profit_values = self.take_profit_values.copy()  # Create a copy of take_profit_values
        take_profit_hits = 0
        take_profit_times = {}
        take_profit_percentages = {}

        for index, row in self.data.iterrows():
            if (row['open_time'] - self.entry_time) / (1000 * 60 * 60) > self.entry_timeout_hours:
                stop_loss = row['close']
                stop_loss_time = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)
                stop_loss_percentage = stop_loss_percentage = self.calculate_profit_percentage(stop_loss)
                return BacktestResult('time_out', stop_loss, stop_loss_time, stop_loss_percentage, take_profit_hits, take_profit_times, take_profit_percentages, 'standard')

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                stop_loss_percentage = self.calculate_profit_percentage(stop_loss)
                stop_loss_time = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)
                return BacktestResult('stop_loss', stop_loss, stop_loss_time, stop_loss_percentage, take_profit_hits, take_profit_times, take_profit_percentages, 'standard')

            for take_profit in list(take_profit_values):  # Iterate over a copy
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    take_profit_hits += 1
                    take_profit_times[take_profit] = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)  # Time difference in hours
                    take_profit_percentages[take_profit] = self.calculate_profit_percentage(take_profit)
                    take_profit_values.remove(take_profit)

        exit_condition = 'ongoing'
        if take_profit_hits == len(self.take_profit_values):
            exit_condition = 'take_profit'

        return BacktestResult(exit_condition, None, None, None, take_profit_hits, take_profit_times, take_profit_percentages, 'standard')

    def backtest_with_entry(self):
        #Timeout
        #Take_profit
        #Stop_loss
        #Not entered

        entered = False
        stop_loss = self.stop_loss  # Create a copy of stop_loss
        take_profit_values = self.take_profit_values.copy()  # Create a copy of take_profit_values
        take_profit_hits = 0
        take_profit_times = {}
        take_profit_percentages = {}

        for index, row in self.data.iterrows():
            if (row['open_time'] - self.entry_time) / (1000 * 60 * 60) > self.entry_timeout_hours:
                stop_loss = row['close']
                stop_loss_time = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)
                stop_loss_percentage = stop_loss_percentage = self.calculate_profit_percentage(stop_loss)
                return BacktestResult('time_out', stop_loss, stop_loss_time, stop_loss_percentage, take_profit_hits, take_profit_times, take_profit_percentages, 'standard_entry')

            if self.direction == 'LONG' and row['low'] <= self.entry_price:
                entered = True
            elif self.direction == 'SHORT' and row['high'] >= self.entry_price:
                entered = True
            if not entered:
                continue

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                stop_loss_percentage = self.calculate_profit_percentage(stop_loss)
                stop_loss_time = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)
                return BacktestResult('stop_loss', stop_loss, stop_loss_time, stop_loss_percentage, take_profit_hits, take_profit_times, take_profit_percentages, 'standard_entry')

            for take_profit in list(take_profit_values):  # Iterate over a copy
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    take_profit_hits += 1
                    take_profit_times[take_profit] = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)  # Time difference in hours
                    take_profit_percentages[take_profit] = self.calculate_profit_percentage(take_profit)
                    take_profit_values.remove(take_profit)

        exit_condition = 'ongoing'
        if take_profit_hits == len(self.take_profit_values):
            exit_condition = 'take_profit'
        elif not entered:
            exit_condition = 'not_entered'
        
        return BacktestResult(exit_condition, None, None, None, take_profit_hits, take_profit_times, take_profit_percentages, 'standard_entry')


    def backtest_with_trailing_stop(self):
        #Timeout
        #Take_profit
        #Stop_loss -> moves to entry on takeprofit target
        #Not entered

        entered = False
        stop_loss = self.stop_loss
        take_profit_values = self.take_profit_values.copy()
        take_profit_hits = 0
        take_profit_times = {}
        take_profit_percentages = {}

        for index, row in self.data.iterrows():
            if (row['open_time'] - self.entry_time) / (1000 * 60 * 60) > self.entry_timeout_hours:
                return BacktestResult('time_out', None, None, None, take_profit_hits, take_profit_times, take_profit_percentages, 'trailing_stop')

            if self.direction == 'LONG' and row['low'] <= self.entry_price:
                entered = True
            elif self.direction == 'SHORT' and row['high'] >= self.entry_price:
                entered = True
            if not entered:
                continue

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                stop_loss_percentage = self.calculate_profit_percentage(stop_loss)
                stop_loss_time = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)
                return BacktestResult('stop_loss', stop_loss, stop_loss_time, stop_loss_percentage, take_profit_hits, take_profit_times, take_profit_percentages, 'trailing_stop')

            for take_profit in list(take_profit_values):
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    take_profit_hits += 1
                    take_profit_times[take_profit] = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)
                    take_profit_percentages[take_profit] = self.calculate_profit_percentage(take_profit)
                    take_profit_values.remove(take_profit)
                    stop_loss = self.entry_price  # move stop loss to entry price

        exit_condition = 'ongoing'
        if take_profit_hits == len(self.take_profit_values):
            exit_condition = 'take_profit'
        elif not entered:
            exit_condition = 'not_entered'
        
        return BacktestResult(exit_condition, None, None, None, take_profit_hits, take_profit_times, take_profit_percentages, 'trailing_stop')


    def backtest_with_progressive_stop(self):
        #Timeout
        #Take_profit
        #Stop_loss -> moves on each take profit target
        #Not entered

        entered = False
        last_take_profit_hit = None
        take_profit_hits = 0
        take_profit_times = {}
        take_profit_percentages = {}

        stop_loss = self.stop_loss
        take_profit_values = self.take_profit_values.copy()

        for index, row in self.data.iterrows():
            if (row['open_time'] - self.entry_time) / (1000 * 60 * 60) > self.entry_timeout_hours:
                return BacktestResult('time_out', None, None, None, take_profit_hits, take_profit_times, take_profit_percentages, 'progressive_stop')

            if self.direction == 'LONG' and row['low'] <= self.entry_price:
                entered = True
            elif self.direction == 'SHORT' and row['high'] >= self.entry_price:
                entered = True
            if not entered:
                continue

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                stop_loss_percentage = self.calculate_profit_percentage(stop_loss)
                stop_loss_time = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)
                return BacktestResult('stop_loss', stop_loss, stop_loss_time, stop_loss_percentage, take_profit_hits, take_profit_times, take_profit_percentages, 'progressive_stop')

            for take_profit in list(take_profit_values):
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    take_profit_hits += 1
                    take_profit_times[take_profit] = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)
                    take_profit_percentages[take_profit] = self.calculate_profit_percentage(take_profit)
                    take_profit_values.remove(take_profit)

                    if take_profit_hits == 1:
                        stop_loss = self.entry_price
                    else:
                        stop_loss = last_take_profit_hit
                    last_take_profit_hit = take_profit

        exit_condition = 'ongoing'
        if take_profit_hits == len(self.take_profit_values):
            exit_condition = 'take_profit'
        elif not entered:
            exit_condition = 'not_entered'
        
        return BacktestResult(exit_condition, None, None, None, take_profit_hits, take_profit_times, take_profit_percentages, 'progressive_stop')

    def print_result(self, result):
        print(f"\nRunning Backtest on {self.symbol}, with {result.backtest_type} strategy")
        print(f"Exit Condition: {result.exit_condition}")
        print(f"StopLoss Price: {result.stop_price}")
        print(f"StopLoss Time: {result.stop_time}")
        print(f"StopLoss Percentage: {result.stop_percentage}")
        print(f"Number of Take Profits hit: {result.take_profit_hits}")
        if result.take_profit_hits > 0:
            print("Take Profits hit:")
            for price, time in result.take_profit_times.items():
                profit = result.take_profit_percentages[price]
                print(f"Profit target of {price} was hit after {time} hours with a profit of {profit}%")
        print('\n')

def get_sample_long_data():
    return ['MAGICUSDT', client.KLINE_INTERVAL_5MINUTE, '1684059363825', 0.837, [0.84043,0.85021,0.85941,0.90288], 0.7661, 'LONG']

def get_sample_short_data():
    return ['COTIUSDT', client.KLINE_INTERVAL_5MINUTE, '1684385817070', 0.072, [0.07164, 0.07092, 0.0702, 0.06883, 0.06804], 0.078, 'SHORT']

def run_backtest_from_signal(signal):
    
    entry = signal.entry[0]
    backtest = BackTest(signal.time_generated, entry, signal.take_profit, signal.stop_loss, signal.direction, signal.pair, client.KLINE_INTERVAL_5MINUTE)
    
    
    backtest.print_result(backtest.backtest())
    backtest.print_result(backtest.backtest_with_trailing_stop())
    backtest.print_result(backtest.backtest_with_progressive_stop())


def run_backtest_from_trade(trade):
    """Run specific backtest result for a quantifiable trade"""
    backtest = BackTest(trade.signal.time_generated, trade.entry, [trade.take_profit], trade.stop_loss, trade.signal.direction, trade.signal.pair, client.KLINE_INTERVAL_5MINUTE)
    print('Market_Price', trade.signal.market_price)
    print(trade.signal.source, type(trade))
    
    if trade.signal.source == 'Hirn':
        results = backtest.backtest()
    else:
        results = backtest.backtest_with_entry()
    print('\n\n', trade)
    print(results)
    result = {}
    if results.take_profit_hits > 0:
        result['result'] = 'profit'
        result['amount'] = list(results.take_profit_percentages.keys())[0]
        result['percentage'] = list(results.take_profit_percentages.values())[0]
        result['time_complete'] = list(results.take_profit_times.values())[0]
    elif results.stop_price:
        result['result'] = 'loss'
        result['amount'] = results.stop_price
        result['percentage'] = results.stop_percentage
        result['time_complete'] = results.stop_time
    elif results.exit_condition == 'timeout':
        result['result'] = 'not_entered'
        result['amount'] = results.stop_price
        result['percentage'] = results.stop_percentage
        result['time_complete'] = results.stop_time
    elif results.exit_condition == 'not_entered':
        result['result'] = 'not_entered'
        result['amount'] = ''
        result['percentage'] = ''
        result['time_complete'] = ''
    elif results.exit_condition == 'ongoing':
        result['result'] = 'ongoing'
        result['amount'] = ''
        result['percentage'] = ''
        result['time_complete'] = ''
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











