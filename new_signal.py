'''This module contains references to all of the different trade groups, sends signal info to them and recieves trade info'''
import json
import database_logging
from signal_sources import hirn, predictum, ggshot
from trade import Trade
import database_logging as db

hirn_controller = hirn.HirnSignal()
predictum_controller = predictum.PredictumSignal()
ggshot_controller = ggshot.GGShotSignal()

async def get_signal(message):
    '''Sends signal to the specified group'''
    if message.origin.id == '1558766055':
        signal = predictum_controller.new_message(message)
        if signal:
            return predictum_controller.get_trade_from_signal(signal)

    elif message.origin.id == '1248393106':
        signal = hirn_controller.new_message(message)
        if signal:
            if signal.base == 'USDT':
                return hirn_controller.get_trade_from_signal(signal)

    elif message.origin.id == '1825288627':
        signal = ggshot_controller.new_message(message)
        if signal:
            if signal.direction == 'LONG':
                return ggshot_controller.get_trade_from_signal(signal)


async def new_signal(message):
    '''Controller for signals coming from a signal group'''
    # Get trade details from signal
    trade = await get_signal(message)
    if(trade):
        print('posting signal', trade)
        print(trade.__str__())
        data = trade.get_dict()
        database_logging.post_signal(data)

