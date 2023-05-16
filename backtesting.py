import pandas as pd
import config


client = config.get_binance_config()

class BackTest:
    def __init__(self, entry_time, entry_price, take_profit_values, stop_loss, direction, symbol, interval):
        self.entry_time = int(entry_time)
        self.entry_price = entry_price
        self.take_profit_values = take_profit_values.copy()  
        self.stop_loss = stop_loss
        self.direction = direction
        self.symbol = symbol
        self.interval = interval
        self.entry_timeout_hours = 24 #trade times out in 24 hours


        if self.direction == 'LONG':
            self.take_profit_values.sort()
        elif self.direction == 'SHORT':
            self.take_profit_values.sort(reverse=True)

        self.data = self.get_historical_klines()
        self.data['high'] = pd.to_numeric(self.data['high'])
        self.data['low'] = pd.to_numeric(self.data['low'])


    def get_historical_klines(self):
        start_str = self.entry_time
        end_time = self.entry_time + (1000 * 60 * 60 * 24 * 7)  # 1 weeks in milliseconds
        klines = client.get_historical_klines(self.symbol, self.interval, start_str, end_time)
        return pd.DataFrame(klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignored'])


    def calculate_profit_percentage(self, target_price):
        if self.direction == 'LONG':
            return round(((target_price - self.entry_price) / self.entry_price) * 100, 2)
        elif self.direction == 'SHORT':
            return round(((self.entry_price - target_price) / self.entry_price) * 100, 2)


    def backtest(self):
        entered = False
        take_profit_hits = 0
        take_profit_times = {}
        take_profit_percentages = {}

        stop_loss = self.stop_loss  # Create a copy of stop_loss
        take_profit_values = self.take_profit_values.copy()  # Create a copy of take_profit_values


        for index, row in self.data.iterrows():
            if (row['open_time'] - self.entry_time) / (1000 * 60 * 60) > self.entry_timeout_hours:
                break

            if self.direction == 'LONG' and row['low'] <= self.entry_price:
                entered = True
            elif self.direction == 'SHORT' and row['high'] >= self.entry_price:
                entered = True
            if not entered:
                continue
            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                stop_loss_percentage = self.calculate_profit_percentage(stop_loss)
                return ('stop_loss', stop_loss, row['open_time'], take_profit_hits, take_profit_times, stop_loss_percentage, take_profit_percentages)
            for take_profit in list(take_profit_values):  # Iterate over a copy
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    take_profit_hits += 1
                    take_profit_times[take_profit] = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)  # Time difference in hours
                    take_profit_percentages[take_profit] = self.calculate_profit_percentage(take_profit)
                    take_profit_values.remove(take_profit)
        if not entered:
            return ('not_entered', None, None, take_profit_hits, take_profit_times, None, take_profit_percentages)
        return ('time_out', None, None, take_profit_hits, take_profit_times, None, take_profit_percentages)


    def backtest_with_trailing_stop(self):
        entered = False
        stop_loss_adjusted = False
        take_profit_hits = 0
        take_profit_times = {}
        take_profit_percentages = {}

        stop_loss = self.stop_loss  # Create a copy of stop_loss
        take_profit_values = self.take_profit_values.copy()  # Create a copy of take_profit_values


        for index, row in self.data.iterrows():
            if (row['open_time'] - self.entry_time) / (1000 * 60 * 60) > self.entry_timeout_hours:
                break

            if self.direction == 'LONG' and row['low'] <= self.entry_price:
                entered = True
            elif self.direction == 'SHORT' and row['high'] >= self.entry_price:
                entered = True
            if not entered:
                continue

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                stop_loss_percentage = self.calculate_profit_percentage(stop_loss)
                return ('stop_loss', stop_loss, row['open_time'], take_profit_hits, take_profit_times, stop_loss_percentage, take_profit_percentages)

            for take_profit in list(take_profit_values):  # Iterate over a copy
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    take_profit_hits += 1
                    take_profit_times[take_profit] = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)  # Time difference in hours
                    take_profit_percentages[take_profit] = self.calculate_profit_percentage(take_profit)
                    take_profit_values.remove(take_profit)

                    if take_profit_hits == 1 and not stop_loss_adjusted:
                        stop_loss = self.entry_price
                        stop_loss_adjusted = True

        if not entered:
            return ('not_entered', None, None, take_profit_hits, take_profit_times, None, take_profit_percentages)

        return ('time_out', None, None, take_profit_hits, take_profit_times, None, take_profit_percentages)


    def backtest_with_progressive_stop(self):
        entered = False
        last_take_profit_hit = None
        take_profit_hits = 0
        take_profit_times = {}
        take_profit_percentages = {}

        stop_loss = self.stop_loss  # Create a copy of stop_loss
        take_profit_values = self.take_profit_values.copy()  # Create a copy of take_profit_values

        for index, row in self.data.iterrows():
            if (row['open_time'] - self.entry_time) / (1000 * 60 * 60) > self.entry_timeout_hours:
                break

            if self.direction == 'LONG' and row['low'] <= self.entry_price:
                entered = True
            elif self.direction == 'SHORT' and row['high'] >= self.entry_price:
                entered = True
            if not entered:
                continue

            if (self.direction == 'LONG' and row['low'] <= stop_loss) or (self.direction == 'SHORT' and row['high'] >= stop_loss):
                stop_loss_percentage = self.calculate_profit_percentage(stop_loss)
                return ('stop_loss', stop_loss, row['open_time'], take_profit_hits, take_profit_times, stop_loss_percentage, take_profit_percentages)

            for take_profit in list(take_profit_values):  # Iterate over a copy
                if (self.direction == 'LONG' and row['high'] >= take_profit) or (self.direction == 'SHORT' and row['low'] <= take_profit):
                    take_profit_hits += 1
                    take_profit_times[take_profit] = round((row['open_time'] - self.entry_time) / (1000 * 60 * 60), 2)  # Time difference in hours
                    take_profit_percentages[take_profit] = self.calculate_profit_percentage(take_profit)
                    take_profit_values.remove(take_profit)

                    if take_profit_hits == 1:
                        stop_loss = self.entry_price
                    else:
                        stop_loss = last_take_profit_hit
                    last_take_profit_hit = take_profit

        if not entered:
            return ('not_entered', None, None, take_profit_hits, take_profit_times, None, take_profit_percentages)

        return ('time_out', None, None, take_profit_hits, take_profit_times, None, take_profit_percentages)


def get_sample_long_data():
    return ['MAGICUSDT', client.KLINE_INTERVAL_5MINUTE, '1684059363825', 0.837, [0.84043,0.85021,0.85941,0.90288], 0.7661, 'LONG']

def get_sample_short_data():
    return ['ETHUSDT', client.KLINE_INTERVAL_5MINUTE, '1683970193138', 1830, [1820.85, 1811.7, 1793.4, 1740.33, 1692.0], 1955.2, 'SHORT']


def run_backtest():
    backtesting_data = get_sample_long_data()

    symbol = backtesting_data[0]
    interval = backtesting_data[1]
    entry_time = backtesting_data[2]
    entry_price = backtesting_data[3]
    take_profit_values = backtesting_data[4]
    stop_loss = backtesting_data[5]
    direction = backtesting_data[6]

    backtest = BackTest(entry_time, entry_price, take_profit_values, stop_loss, direction, symbol, interval)


    result_type, result_price, result_time, take_profit_hits, take_profit_times, stop_loss_percentage, take_profit_percentages = backtest.backtest()
    print('\nTest 1:')
    print(f"Result: {result_type} at price {result_price} and time {result_time}")
    print(f"Number of Take Profits hit: {take_profit_hits}")
    if stop_loss_percentage is not None:
        print(f"Stop loss hit at price {result_price} with a loss of {stop_loss_percentage}%")
    for tp, time in take_profit_times.items():
        print(f"Profit target of {tp} was hit after {time} hours with a profit of {take_profit_percentages[tp]}%")


    result_type, result_price, result_time, take_profit_hits, take_profit_times, stop_loss_percentage, take_profit_percentages = backtest.backtest_with_trailing_stop()
    print('\nTest 2:')
    print(f"Result: {result_type} at price {result_price} and time {result_time}")
    print(f"Number of Take Profits hit: {take_profit_hits}")
    if stop_loss_percentage is not None:
        print(f"Stop loss hit at price {result_price} with a loss of {stop_loss_percentage}%")
    for tp, time in take_profit_times.items():
        print(f"Profit target of {tp} was hit after {time} hours with a profit of {take_profit_percentages[tp]}%")


    result_type, result_price, result_time, take_profit_hits, take_profit_times, stop_loss_percentage, take_profit_percentages = backtest.backtest_with_progressive_stop()
    print('\nTest 3:')
    print(f"Result: {result_type} at price {result_price} and time {result_time}")
    print(f"Number of Take Profits hit: {take_profit_hits}")
    if stop_loss_percentage is not None:
        print(f"Stop loss hit at price {result_price} with a loss of {stop_loss_percentage}%")
    for tp, time in take_profit_times.items():
        print(f"Profit target of {tp} was hit after {time} hours with a profit of {take_profit_percentages[tp]}%")











