'''This module contains references to all of the different trade groups, sends signal info to them and recieves trade info'''
import json
from types import SimpleNamespace

import database_logging as db
from trade import Trade
from signal_sources import hirn, predictum, ggshot
from signal_conditions import Signal

hirn_controller = hirn.HirnSignal()
predictum_controller = predictum.PredictumSignal()
ggshot_controller = ggshot.GGShotSignal()

controller_mapping = {
    '1558766055': predictum_controller,
    '1248393106': hirn_controller,
    '1825288627': ggshot_controller,
}


async def process_message(message):
    '''Controller for signals coming from a signal group'''
    # Get trade details from signal
    controller = controller_mapping.get(message.origin.id)
    if controller.validate_signal(message.message):
        signal = controller.new_signal_message(message)
        trade = controller.get_filtered_trade_from_signal(signal)
        if trade:
            print('posting signal', trade)
            print(trade.__str__())
            data = trade.get_dict()
            print('Posting Signal Data:', data)
            db.post_signal(data)
        else:
            print('\nFiltered Signal:', signal)


def trade_from_signal_data(signal_data, filter):
    return trade_from_signal(signal_from_signal_data(signal_data), filter)


def signal_from_signal_data(signal_data):
    '''Clones a new signal from json signal data'''
    signal_data = deep_namespace(signal_data)
    signal = Signal(signal_data.source, signal_data.message, signal_data.coin, signal_data.base, signal_data.entry, signal_data.take_profit, signal_data.stop_loss, signal_data.direction)
    signal.market_price = signal_data.market_price
    signal.time_generated = signal_data.time_generated
    return signal


def trade_from_signal(signal, filter):
    '''Creates a trade from signal data'''
    controller = controller_mapping.get(signal.message.origin.id)
    if filter:
        return controller.get_filtered_trade_from_signal(signal)
    else:
        return controller.get_trade_from_signal(signal)



def deep_namespace(d):
    if isinstance(d, dict):
        return SimpleNamespace(**{k: deep_namespace(v) for k, v in d.items()})
    elif isinstance(d, list):
        return [deep_namespace(item) for item in d]
    else:
        return d