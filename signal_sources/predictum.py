from parse_signal import SignalProviderBase
from signal_conditions import Signal
from trade_conditions import FutureBasic, SpotBasic


class PredictumSignal(SignalProviderBase):
    def __init__(self, source = 'Predictum'):
        super().__init__(source=source, signal_identifier=['⚡️⚡️','USDT'])


    def parse(self, message, sanitised_message):
        '''Parses out the signal message into values'''
        print(sanitised_message)
        pair = sanitised_message[0].split('⚡️⚡️')[1]
        if '/' in pair:
            coin, base = pair.split('/')
        else:
            coin = pair.split('USDT')[0]
            base = 'USDT'
        entry = sanitised_message[3].split(':')[1].split('-')
        take_profit = []
        stop_loss = ''
        for count, line in enumerate(sanitised_message[4:], start=1):
            #If target and # in line, append it to profit targets
            targetCheck = 'TARGET'+str(count)
            if(targetCheck in line.upper()):
                take_profit.append(line.split(':')[1])
            elif('STOPLOSS' in line.upper()):
                stop_loss = line.split(':')[1]

        direction = 'LONG'
        if entry[0] > take_profit[0]:
            direction = 'SHORT'
 
        signal =  Signal(self.source, message, coin, base, entry, take_profit, stop_loss, direction)
        return signal


    def get_trades_from_signal(self, signal):
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