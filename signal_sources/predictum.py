import time
import utility
import database_logging as db
from trade_conditions import FutureBasic, SpotBasic
from datetime import datetime

TRADE_TIMEOUT = 604800000  # 7 Days in econds

class PredictumSignal():

    def new_message(self, signal):
        '''Entry point, returns nothing, or a trade signal'''
        if not self.validate_signal(signal.message):
            return
        print('PREDICTUM SIGNAL!')
        try:
            return self.parse(signal)
        except ValueError as e:
            print('Exception in Predictum Signal')
            print(e)
            
    def validate_signal(self, msg):
        '''Verifies if the message from Predictum is a trade signal'''
        if '/USDT ⚡️⚡️' in msg:
            return True
        else:
            return False
        
    def parse(self, signal):
        '''Parses out the signal message into values'''
        lines = signal.message.split('\n')
        print(lines)
        pair = lines[0].split('⚡️')[2]
        coin = pair.split('/')[0]
        base = pair.split('/')[1]
        pair = pair.split('/')[0] + base
        entry = lines[5].split(': ')[1]
        if '-' in entry:
            entry = entry.split('-')[1]
        entry = float(entry)
        profit_price = float(lines[8].split(': ')[1])
        stop_loss = float(lines[14].split(': ')[1])
        lev = 1
        if entry > profit_price:
            direction = 'short'
            return
        else:
            direction = 'long'
        loss_price = entry * stop_loss/lev
        timeout = utility.get_timestamp_now() + TRADE_TIMEOUT # 7 Days timeout in seconds
        return [SpotBasic('Predictum', signal, coin, base, entry, profit_price, stop_loss, timeout)]