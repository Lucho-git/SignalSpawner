import time
from datetime import datetime
from trade_conditions import FutureBasic, SpotBasic
import utility
import database_logging as db


class SignalProviderBase():
    def __init__(self):
        self.timer = datetime.now().timestamp()
        self.first = True
        self.cooldown_time = 10
        self.source = 'Default-Source'

    def new_message(self, message):
        '''Entry point, returns nothing, or a trade signal'''
        raw_message = message.message
        try:
            if not(self.validate_signal(raw_message)):
                return
        except ValueError as e:
            print(e)
            return
        
        try:
            sanitised_message = self.sanitise_message(raw_message)
            return self.parse(message, sanitised_message)
        except Exception as e:
            #should database log this
            print('Unexpected exception parsing signal message:')
            print(e)

    def cooldown(self):
        '''Avoids processing duplicate signals'''
        if not self.first:
            time.sleep(5)
        self.first = False

        timenow = datetime.now().timestamp()
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

    def validate_signal(self, message):
        '''This function should be implemented in subclasses'''
        raise NotImplementedError()

    def parse(self, message, sanitised_message):
        '''This function should be implemented in subclasses'''
        raise NotImplementedError()
    
    def create_trade(self, signal):
        '''This function should be implemented in subclasses'''
        raise NotImplementedError()