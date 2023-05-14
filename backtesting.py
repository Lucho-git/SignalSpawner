import pandas as pd
import config


client = config.get_binance_config()

def get_sample_data():
    return ['MAGICUSDT', client.KLINE_INTERVAL_1MINUTE, '1684059363825', 0.836, [0.84043,0.85021,0.85941,0.90288], 0.7661]


def get_historical_klines(symbol, interval, start_str):
    end_str = int(start_str) + (1000 * 60 * 60 * 24 * 7)
    klines = client.get_historical_klines(symbol, interval, start_str, end_str)
    data = pd.DataFrame(klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignored'])
    print(data)
    return data

def calculate_profit_percentage(entry_price, target_price):
    return round(((target_price - entry_price) / entry_price) * 100, 2)

def backtest(data, entry_price, take_profit_values, stop_loss, start_time):
    data['high'] = pd.to_numeric(data['high'])
    data['low'] = pd.to_numeric(data['low'])

    take_profit_values.sort()
    take_profit_hits = 0
    take_profit_times = {}
    take_profit_percentages = {}

    for index, row in data.iterrows():
        if row['low'] <= stop_loss:
            stop_loss_percentage = calculate_profit_percentage(entry_price, stop_loss)
            return ('stop_loss', stop_loss, row['open_time'], take_profit_hits, take_profit_times, stop_loss_percentage, take_profit_percentages)
        for take_profit in take_profit_values:
            if row['high'] >= take_profit:
                take_profit_hits += 1
                take_profit_times[take_profit] = round((row['open_time'] - int(start_time)) / (1000 * 60 * 60), 2)  # Time difference in hours
                take_profit_percentages[take_profit] = calculate_profit_percentage(entry_price, take_profit)
                take_profit_values.remove(take_profit)
    return ('time_out', None, None, take_profit_hits, take_profit_times, None, take_profit_percentages)



def run_backtest():
    backtesting_data = get_sample_data()
    kline_data = get_historical_klines(backtesting_data[0],backtesting_data[1],backtesting_data[2])
    result_type, result_price, result_time, take_profit_hits, take_profit_times, stop_loss_percentage, take_profit_percentages = backtest(kline_data, backtesting_data[3], backtesting_data[4], backtesting_data[5], backtesting_data[2])

    print(f"Result: {result_type} at price {result_price} and time {result_time}")
    print(f"Number of Take Profits hit: {take_profit_hits}")
    if stop_loss_percentage is not None:
        print(f"Stop loss hit with a loss of {stop_loss_percentage}%")
    for tp, time in take_profit_times.items():
        print(f"Profit target of {tp} was hit after {time} hours with a profit of {take_profit_percentages[tp]}%")