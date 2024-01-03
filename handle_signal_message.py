'''This module contains references to all of the different trade groups, sends signal info to them and recieves trade info'''
import json
import traceback
import database_logging as db
from trade import Trade
from signal_sources import hirn, predictum, ggshot, ggshot_vip
from signal_conditions import Signal

hirn_controller = hirn.HirnSignal()
predictum_controller = predictum.PredictumSignal()
ggshot_controller = ggshot.GGShotSignal()
ggshot_free_controller = ggshot.GGShotSignal('GGshot_free')
ggshot_leaked_controller = ggshot.GGShotSignal('GGshot_Leaked')
ggshot_vip_controller = ggshot_vip.GGShotVipSignal()

controller_mapping = {
    '1558766055': predictum_controller,
    '1248393106': hirn_controller,
    '1825288627': ggshot_controller,
    '1175262142': ggshot_free_controller,
    '1480838869': ggshot_leaked_controller,
    '1737189058': ggshot_vip_controller,
}


async def process_message(message):
    '''Controller for signals coming from a signal group'''
    # Get trade details from signal
    controller = controller_mapping.get(message.origin.id)
    if controller.validate_signal(message.message):
        try:
            signal = controller.new_signal_message(message)
            trade = controller.get_filtered_trades_from_signal(signal)
            for t in trade:
                print('posting signal', t)
                print(t.__str__())
                data = t.get_trade_dict(signal)
                print('Posting Signal Data:', data)
                db.post_signal(data)
            else:
                print('\nFiltered Signal:', signal)
        except Exception as e:
            print('Unexpected exception parsing signal message:')
            print(e)
            traceback.print_exc()

def trades_from_signal(signal, filter):
    '''Creates a trade from signal data'''
    controller = controller_mapping.get(signal.message.origin.id)
    try:
        return controller.get_trades_from_signal(signal, filter)
    except Exception as e:
        print('Unexpected getting trade from signal message:')
        print(e)
        traceback.print_exc()
        return