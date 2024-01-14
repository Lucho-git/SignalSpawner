from parse_signal import SignalProviderBase
from signal_conditions import Signal
from trade_conditions import FutureBasic, SpotBasic

class BinanceKillers(SignalProviderBase):
    def __init__(self, source = 'BinanceKillers'):
        super().__init__(source=source, signal_identifier=['SIGNAL ID:', 'TARGETS'])


    def parse(self, message, sanitised_message):
        '''Parses out the signal message into values'''
        print(sanitised_message)
        coin = sanitised_message[1].split('$')[1].split('/USDT')[0]
        print(coin)
        base = 'USDT'
        direction = ''
        entry = sanitised_message[4].split(':')[1].split('-')
        print(entry)
        take_profit = []
        stop_loss = ''
        take_profit = sanitised_message[7].split(':')[1].split('-')
        print(take_profit)
        stop_loss = sanitised_message[9].split(':')[1]
        print(stop_loss)
        direction = 'LONG'
        if entry[0] > take_profit[0]:
            direction = 'SHORT'

        signal =  Signal(self.source, message, coin, base, entry, take_profit, stop_loss, direction)
        return signal


    def get_all_trades_from_signal(self, signal):
        '''Convert Signal into trade values'''
        trades = []
        trade = FutureBasic(self.source+'|0|1|0|standard_entry', signal.time_generated, signal.entry[0], signal.take_profit[1], signal.stop_loss, signal.direction, 1)
        trades.append(trade)
        return trades


    def filter_trade(self, trade, signal):
        return True
        if signal.direction == 'LONG':
            return True
        return False