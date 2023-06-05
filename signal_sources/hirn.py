from parse_signal import SignalProviderBase
from signal_conditions import Signal
from trade_conditions import FutureBasic, SpotBasic

class HirnSignal(SignalProviderBase):
    def __init__(self, source = 'Hirn'):
        super().__init__(source=source, signal_identifier='Buy #')


    def parse(self, message, sanitised_message):
        '''Parses out the signal message into values'''
        print(sanitised_message)
        coin, base = sanitised_message[0].split('#')[1].split('/')
        entry = sanitised_message[1].split(':')[1]
        take_profit = sanitised_message[2].split(':')[1].split('+')[0]
        stop_loss = float(entry)*0.95

        newSignal = Signal(self.source, message, coin, base, [entry], [take_profit], stop_loss, 'LONG')
        return newSignal
    

    def get_all_trades_from_signal(self, signal):
        '''Convert Signal into trade values'''
        trades = []
        trade = SpotBasic(self.source+'|0|0|0|standard', signal.time_generated, signal.entry[0], signal.take_profit[0], signal.stop_loss)
        trades.append(trade)
        return trades


    def filter_trade(self, trade, signal):
        if signal.base == 'USDT':
            return True
        return False