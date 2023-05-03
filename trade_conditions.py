import utility
import config
import json
'''
Defines a set of conditions and parameters, 
for a signal to become a trade.

These values should be static

'''
class SpotBasic:
    '''Spot basic is a market spot order, with a takeprofit value, optional stoploss or
    timelimit to exit trade,if no stoploss is entered then a mandatory 7 day limit is applied'''
    def __init__(self, signal, entry, take_profit, stop_loss, timeout = None):
        self.signal = signal
        self.entry = entry
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.timeout = timeout
        if not self.timeout:
            self.timeout = signal.time_generated + 604800000 #7 Days timeout in seconds, check this is correct with utils timer

        self.sanitise_price_data()

    def sanitise_price_data(self):
        '''Ensures binance will accept all price values for making orders'''
        pair = self.signal.pair
        self.entry = utility.sanitise_price_data(pair, self.entry)
        self.take_profit = utility.sanitise_price_data(pair, self.take_profit)
        self.stop_loss = utility.sanitise_price_data(pair, self.stop_loss)

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
        return str({
                "source": self.signal.source,
                "coin": self.signal.coin,
                "base": self.signal.base,
                "pair": self.signal.pair,
                "entry": self.entry,
                "profit": self.take_profit,
                "loss": self.stop_loss,
                "time_generated": self.signal.time_generated,
                "timeout": self.timeout,
                })

    def get_dict(self):
        return {
            "source": self.signal.source,
            "coin": self.signal.coin,
            "base": self.signal.base,
            "pair": self.signal.pair,
            "entry": self.entry,
            "profit": self.take_profit,
            "loss": self.stop_loss,
            "timeout": self.timeout,
            "time_generated": self.signal.time_generated
        }

class SpotAdvanced(SpotBasic):
    """Spot advanced allows for multiple exit prices and percentages"""
    def __init__(self, source, signal, coin, base, entry, take_profit, stop_loss, profit_amount, loss_amount, timeout=None):
        super().__init__(source, signal, coin, base, entry, take_profit, stop_loss, timeout)
        self.profit_amount = profit_amount
        self.loss_amount = loss_amount

class FutureBasic(SpotBasic):
    '''Futures basic is a market futures order, can only be ISO,
    must have stoploss before liquidation value'''
    def __init__(self, source, signal, coin, direction, leverage, entry, profit, loss=None, timeout=None):
        super().__init__(source, signal, 'USD', coin, entry, profit, loss, timeout)
        self.direction = direction
        self.leverage = leverage

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
