'''This module contains references to all of the different trade groups, sends signal info to them and recieves trade info'''
import json
import database_logging
from signal_sources import hirn, predictum
from trade import Trade
import database_logging as db

hirn_controller = hirn.HirnSignal()
predictum_controller = predictum.PredictumSignal()

async def get_signal(signal):
    '''Sends signal to the specified group'''
    if signal.origin.id == '1558766055':
        signal = predictum_controller.new_message(signal)
        print('Predictum Message')
        return signal

    elif signal.origin.id == '1248393106':
        signal = hirn_controller.new_hirn_signal(signal)
        if signal:
            if signal[0].base == 'USDT':
                return signal

    elif signal.origin.id == '1825288627':
        print('GGShot Signal')

async def new_signal(signal):
    '''Controller for signals coming from a signal group'''
    # Get trade details from signal
    signal = await get_signal(signal)
    if(signal):
        print('posting signal', signal[0])
        print(signal[0].__str__())
        data = signal[0].get_dict()
        database_logging.post_signal(data)

