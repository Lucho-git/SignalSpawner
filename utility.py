"""Various Helper commands that are hard to place elsewhere"""
import re
import os
import binance
import numpy as np
import math
from datetime import datetime
from config import get_binance_exchange_info

binance_exchange_info = get_binance_exchange_info()

def format_float(num):
    return np.format_float_positional(num, trim='-')

def strip_ansi_codes(s):
    return re.sub('\033\\[([0-9]+)(;[0-9]+)*m', '', s)

# Converts a Binance server timestamp into a local timestamp in milliseconds
def convert_timestamp_utc8(timestamp):
    '''Converts a utc servertime to utc8 as a number timestring'''
    dt = float(timestamp / 1000)
    utctime = datetime.utcfromtimestamp(dt)
    timedelta = 60 * 60 * 8  # + 8 Hours from UTC
    timestamp = datetime.timestamp(utctime) + timedelta
    return int(timestamp * 1000)

def utc_to_utc8(timestamp):
    '''convert to utc8'''

def get_timestamp_now():
    '''Returns current timestamp'''
    stamp = datetime.now().timestamp()
    stamp = int(stamp * 1000)
    return stamp

def get_price_precision(symbol):
    symbol_info = get_binance_symbol_info(symbol)
    for f in symbol_info['filters']:
        if f['filterType'] == 'PRICE_FILTER':
            tick_size = str(f['tickSize'])
    split = tick_size.split('.')
    if split[0] == '1':
        return 0
    split = split[1].split('1')[0]
    price_precision = int(len(split) + 1)
    return price_precision

def round_decimals_down(number: float, decimals: int = 2):
    if decimals == 0:
        return math.floor(number)
    factor = 10 ** decimals
    return math.floor(number * factor) / factor 

def sanitise_price_data(symbol, price):
    precision = get_price_precision(symbol)
    if isinstance(price, list):
        for p in price:
            p = round_decimals_down(float(p), precision)
    elif isinstance(price, str) or isinstance(price, float):
        price = round_decimals_down(float(price), precision)
    else:
        raise ValueError('Bad Data Type', str(type(price)))
    return price

def get_binance_symbol_info(symbol):
    return binance_exchange_info.get(symbol)
