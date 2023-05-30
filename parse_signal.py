import time
from trade_conditions import FutureBasic, SpotBasic
import utility
import database_logging as db
import traceback


class SignalProviderBase():
    #source is the name of signal group
    #identifier is the text that identifies if a message is a signal, can be an array for multiple identifiers
    def __init__(self, source='Default', signal_identifier='None'):
        self.timer = utility.get_timestamp_now()
        self.first = True
        self.cooldown_time = 10
        self.source = source
        self.signal_identifier = signal_identifier

    def new_signal_message(self, message):
        '''Entry point, returns nothing, or a trade signal'''
        raw_message = message.message
        try:
            sanitised_message = self.sanitise_message(raw_message)
            signal = self.parse(message, sanitised_message)
            if signal:
                db.save_raw_signal(signal)
                return signal
        except Exception as e:
            #should database log this
            print('Unexpected exception parsing signal message:')
            print(e)
            traceback.print_exc()

    def cooldown(self):
        '''Avoids processing duplicate signals'''
        if not self.first:
            time.sleep(5)
        self.first = False

        timenow = utility.get_timestamp_now()
        if timenow < self.timer:
            raise ValueError('Duplicate Signal in ' + str(self.source) + ' while Cooling Down')
        else:
            self.timer = timenow + self.cooldown_time
            self.first = True

    def sanitise_message(self, raw_message):
        '''Sanitises the input, returns array of lines'''
        text = raw_message.replace(" ","")
        while('\n\n' in text): 
            text = text.replace('\n\n','\n')
        lines = text.split('\n')
        return lines

    def validate_signal(self, msg):
        if (isinstance(self.signal_identifier, list)):
            if all(substring in msg.upper() for substring in self.signal_identifier):
                self.cooldown()
                return True

        elif isinstance(self.signal_identifier, str):
            if self.signal_identifier in msg:
                self.cooldown()
                return True
        else:
            print('Not a signal')

    def filter_trade(self, trade, signal):
        return True

    def parse(self, message, sanitised_message):
        '''This function should be implemented in subclasses'''
        raise NotImplementedError()
    
    def get_trades_from_signal(self, signal):
        '''This function should be implemented in subclasses'''
        raise NotImplementedError()

    def get_filtered_trades_from_signal(self, signal):
        trades = self.get_trades_from_signal(signal)
        print('trades|', trades)
        returning_trades = []
        for t in trades:
            if self.filter_trade(t, signal):
                returning_trades.append(t)
        return returning_trades