from parse_signal import SignalProviderBase
from signal_conditions import Signal
from trade_conditions import FutureBasic, SpotBasic

class HirnSignal(SignalProviderBase):
    def __init__(self):
        super().__init__(source='Hirn', signal_identifier='Buy #')


    def parse(self, message, sanitised_message):
        '''Parses out the signal message into values'''
        print(sanitised_message)
        coin, base = sanitised_message[0].split('#')[1].split('/')
        entry = sanitised_message[1].split(':')[1]
        profit_target = sanitised_message[2].split(':')[1].split('+')[0]
        stop_loss = float(entry)*0.95
        direction = 'LONG'

        newSignal = Signal(self.source, message, coin, base, entry, profit_target, stop_loss, direction)
        return newSignal
    

    def get_trade_from_signal(self, signal):
        '''Convert Signal into trade values'''
        trade = SpotBasic(signal, signal.entry, signal.take_profit, signal.stop_loss)
        return trade
