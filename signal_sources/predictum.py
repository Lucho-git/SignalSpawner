from parse_signal import SignalProviderBase
from signal_conditions import Signal
from trade_conditions import FutureBasic, SpotBasic


class PredictumSignal(SignalProviderBase):
    def __init__(self):
        super().__init__(source='Predictum', signal_identifier=['⚡️⚡️','USDT'])


    def parse(self, message, sanitised_message):
        '''Parses out the signal message into values'''
        print(sanitised_message)
        pair = sanitised_message[0].split('⚡️⚡️')[1]
        coin, base = pair.split('/')
        entry = sanitised_message[3].split(':')[1].split('-')
        profit_targets = []
        stop_loss = ''
        for count, line in enumerate(sanitised_message[4:], start=1):
            #If target and # in line, append it to profit targets
            targetCheck = 'TARGET'+str(count)
            if(targetCheck in line.upper()):
                profit_targets.append(line.split(':')[1])
            elif('STOPLOSS' in line.upper()):
                stop_loss = line.split(':')[1]

        direction = 'LONG'
        if entry[0] > profit_targets[0]:
            direction = 'SHORT'
 
        signal =  Signal(self.source, message, coin, base, entry, profit_targets, stop_loss, direction)
        return signal


    def get_trade_from_signal(self, signal):
        '''Convert Signal into trade values'''
        trade = SpotBasic(signal, signal.entry[0], signal.take_profit[1], signal.stop_loss)
        return trade
    
    
    def filter_trade(self, trade):
        if trade.signal.direction == 'LONG':
            return True
        return False