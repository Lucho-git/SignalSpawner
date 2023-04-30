from parse_signal import SignalProviderBase
from signal_conditions import Signal
from trade_conditions import FutureBasic, SpotBasic

class GGShotSignal(SignalProviderBase):
    def __init__(self):
        super().__init__(source='GGshot', signal_identifier=['SIGNAL DETAILS', 'TARGET1'])


    def parse(self, message, sanitised_message):
        '''Parses out the signal message into values'''
        coin = sanitised_message[0].split('#')[1].split('USDT')[0]
        base = 'USDT'
        direction = ''
        if('SHORT' in sanitised_message[1].upper()):
            direction = 'SHORT'
        elif('LONG' in sanitised_message[1].upper()):
            direction = 'LONG'
        entry = sanitised_message[1].split(':')[1].split('-')
        profit_targets = []
        stop_loss = ''
        for count, line in enumerate(sanitised_message[5:], start=1):
            #If target and # in line, append it to profit targets
            targetCheck = 'TARGET'+str(count)
            if(targetCheck in line.upper()):
                profit_targets.append(line.split(':')[1])
            elif('STOP-LOSS' in line.upper()):
                stop_loss = line.split(':')[1]

        signal =  Signal(self.source, message, coin, base, entry, profit_targets, stop_loss, direction)
        return signal


    def get_trade_from_signal(self, signal):
        '''Convert Signal into trade values'''
        trade = SpotBasic(signal, signal.entry[0], signal.take_profit[0], signal.stop_loss)
        return trade