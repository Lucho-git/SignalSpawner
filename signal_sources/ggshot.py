import time
import utility
import database_logging as db
from trade_conditions import FutureAdvanced, FutureBasic, SpotBasic
from signal_conditions import Signal
from datetime import datetime

TRADE_TIMEOUT = 604800000  # 7 Days in econds
SIGNAL_COOLDOWN_TIME = 10  # In seconds
LEVERAGE = 1

class GGShotSignal():
    def __init__(self):
        self.timer = datetime.now().timestamp()
        self.tradeheat = False
        self.first = True


    def new_message(self, signal):
        '''Entry point, returns nothing, or a trade signal'''
        if not self.validate_signal(signal.message):
            return
        print('GGSHOT SIGNAL!')
        try:
            return self.parse(signal)
        except Exception as e:
            print('Exception in GGSHOT Signal')
            print(e)
    

    def validate_signal(self, msg):
        '''Verifies if the message from GGSHOT is a trade signal'''
        if 'SIGNAL DETAILS' in msg.upper() and 'Target1' in msg:
            try:
                self.cooldown()
                return True
            except ValueError:
                print('Cooling Down')
                return False
        else:
            return False
    

    def cooldown(self):
        '''Telegram sometimes double posts their messages, this makes sure we are only trading once'''
        if not self.first:
            time.sleep(5)
        self.first = False

        timenow = datetime.now().timestamp()
        if timenow < self.timer:
            self.tradeheat = True
            raise ValueError('Duplicate Signal while Cooling Down')
        else:
            self.tradeheat = False
            self.timer = timenow + SIGNAL_COOLDOWN_TIME
            self.first = True


    def parse(self, signal):
        '''Parses out the signal message into values'''
        signals = []

        textblock = signal.message.replace(" ","")
        while('\n\n' in textblock): 
            textblock = textblock.replace('\n\n','\n')
        lines = textblock.split('\n')
        print(lines)
        coin = lines[0].split('#')[1].split('USDT')[0]
        base = 'USDT'
        direction = ''
        if('SHORT' in lines[1].upper()):
            direction = 'SHORT'
        elif('LONG' in lines[1].upper()):
            direction = 'LONG'
        entry = lines[1].split(':')[1].split('-')
        profit_targets = []
        stop_loss = ''
        for count, line in enumerate(lines[5:], start=1):
            #If target and # in line, append it to profit targets

            targetCheck = 'TARGET'+str(count)
            if(targetCheck in line.upper()):
                profit_targets.append(line.split(':')[1])
            elif('STOP-LOSS' in line.upper()):
                stop_loss = line.split(':')[1]
        
        timeout = utility.get_timestamp_now() + TRADE_TIMEOUT # 7 Days timeout in seconds


        newSignal = Signal('GGshot', signal, coin, base, entry, profit_targets, stop_loss, direction)
        signals.append(newSignal)

        if direction == 'LONG':
            #Higher entry target, 2nd profit target
            newTrade = SpotBasic('GGshot', signal, coin, base, entry[0], profit_targets[1], stop_loss, timeout)
            signals.append(newTrade)

        return signals


        #Future Advanced |source, signal, coin, base, entry, profit, loss, profit_amount, loss_amount, direction, leverage, timeout=None):
    #def __init__(self, source, signal, coin, base, entry, profit_targets, stop_loss, direction, leverage, timeout=None):
