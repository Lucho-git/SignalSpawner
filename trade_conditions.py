import utility
import config
import json
import backtesting
from types import SimpleNamespace

'''
Defines a set of conditions and parameters, 
for a signal to become a trade.

These values should be static

'''
class SpotBasic:
    '''Spot basic is a market spot order, with a takeprofit value, optional stoploss or
    timelimit to exit trade,if no stoploss is entered then a mandatory 7 day limit is applied'''
    def __init__(self, source, time_generated, entry, take_profit, stop_loss):
        self.source = source
        self.entry = entry
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.timeout = time_generated + 604800000 #7 Days timeout in seconds
        self.backtest = 'undetermined'

    def check_timeout(self, trade):
        '''Checks to see if trade has timed out'''
        if self.timeout:
            if trade.latest_time > self.timeout:
                trade.status = 'timeout'

    def check_trade(self, trade):
        '''Checks to see if trade conditions have been met'''
        if trade.highest_price > self.take_profit:
            trade.status = 'profit'
            return
        if trade.lowest_price < self.stop_loss:
            trade.status = 'loss'

    def get_value(self, trade):
        '''Returns current value of the trade'''
        raw_change = trade.last_price - trade.entry_price
        decimal_change = raw_change/trade.entry_price
        return decimal_change + 1

    def get_time(self):
        '''Gets the starting trade time, should use binance'''
        return utility.get_timestamp_now()

    def get_price(self):
        '''Gets current price from binanace'''
        return float(config.get_binance_config().get_symbol_ticker(symbol=self.signal.pair)['price'])
    
    def __str__(self) -> str:
        return str(self.get_dict())


    def get_dict(self):
        return {
            "entry": self.entry,
            "profit": self.take_profit,
            "loss": self.stop_loss,
            "direction": "LONG",
            "backtest": self.backtest,
            "timeout": self.timeout,
        }

    def get_trade_dict(self, signal):
        return {
            "source": signal.source,
            "coin": signal.coin,
            "base": signal.base,
            "pair": signal.pair,
            "entry": self.entry,
            "profit": self.take_profit,
            "loss": self.stop_loss,
            "direction": "LONG",
            "backtest": self.backtest,
            "timeout": self.timeout,
            "time_generated": signal.time_generated
        }
    
    def run_backtest(self, signal):
        if (isinstance(self.backtest, SimpleNamespace)):
            if (self.backtest.result == 'profit' or self.backtest.result == 'loss'):
                return
        print('Starting New Backtest', type(self.backtest), self.backtest)
        self.backtest = backtesting.run_backtest_from_trade(self, signal)
        print('BACKTEST TYPE', type(self.backtest), self.backtest)


class FutureBasic(SpotBasic):
    '''Futures basic is a market futures order, can only be ISO,
    must have stoploss before liquidation value'''
    def __init__(self, source, time_generated, entry, take_profit, stop_loss, direction, leverage):
        super().__init__(source, time_generated, entry, take_profit, stop_loss)
        self.direction = direction
        self.leverage = leverage

    def get_dict(self):
        add_dict = super().get_dict()
        add_dict['leverage'] = self.leverage
        add_dict['direction'] = self.direction
        return add_dict

    def get_trade_dict(self, signal):
        add_dict = super().get_trade_dict(signal)
        add_dict['leverage'] = self.leverage
        add_dict['direction'] = self.direction
        return add_dict


class SpotAdvanced(SpotBasic):
    """Spot advanced allows for multiple exit prices and percentages"""
    def __init__(self, source, signal, coin, base, entry, take_profit, stop_loss, profit_amount, loss_amount, timeout=None):
        super().__init__(source, signal, coin, base, entry, take_profit, stop_loss, timeout)
        self.profit_amount = profit_amount
        self.loss_amount = loss_amount


class FutureAdvanced(SpotAdvanced):
    '''Futures advanced combines all of the previous features in a derivatives market'''
    def __init__(self, source, signal, coin, base, entry, take_profit, stop_loss, profit_amount, loss_amount, direction, leverage, timeout=None):
        super().__init__(source, signal, base, coin, entry, take_profit, stop_loss, profit_amount, loss_amount, timeout)
        self.direction = direction
        self.leverage = leverage


class SpotBasicBinance(SpotBasic):
    '''SpotBasic real binance trade'''
    def __init__(self, user, source, signal, coin, base, entry, profit, loss=None, timeout=None):
        super().__init__(source, signal, coin, base, entry, profit, loss, timeout)
        self.user = user
        self.receipt = self.user.binance.market_trade(self)
