"""Module interacts with the database, for saving and loading various data/logs"""
from datetime import datetime, timedelta, timezone

import handle_signal_message
import os
import pickle
import json
import jsonpickle
import pytz
import requests
import traceback
from signal_conditions import Signal

from config import get_firebase_config, get_storage_paths

paths = get_storage_paths()
firebase = get_firebase_config()
storage = firebase.storage()
database = firebase.database()
tz = timezone.utc




def error_log(error):
    '''Logs exceptions to database'''
    now = datetime.now(tz)
    month_year = now.strftime('%B-%Y')
    date_formatted = now.strftime('%d-%b-%y')
    time_formatted = now.strftime('%H:%M:%S:')

    error_filepath = paths.LOG + 'exceptions/' + month_year + '/' + date_formatted + '.txt'
    error_dirpath = error_filepath.rsplit('/', 1)[0]+'/'
    if not os.path.exists(error_dirpath):
        os.makedirs(error_dirpath)

    print(str(error))
    storage.child(error_filepath).download("./", error_filepath)
    with open(error_filepath, 'a', encoding="utf8") as f:
        f.write(time_formatted + '| ' + str(error) + '\n\n')
    storage.child(error_filepath).put(error_filepath)



def gen_log(log):
    '''Logs general program runtime for debugging purposes'''
    now = datetime.now(tz)
    month_year = now.strftime('%B-%Y')
    date_formatted = now.strftime('%d-%b-%y')
    time_formatted = now.strftime('%H:%M:%S:')
    genlog_filepath = paths.LOG + 'general_logs/' + month_year + '/' + date_formatted + '.txt'
    genlog_dirpath = genlog_filepath.rsplit('/', 1)[0]+'/'
    if not os.path.exists(genlog_dirpath):
        os.makedirs(genlog_dirpath)

    log = log.replace('\n', str('\n'+time_formatted+'| '))
    storage.child(genlog_filepath).download("./", genlog_filepath)
    # If file exists, add to it, else create a new one
    with open(genlog_filepath, 'a+', encoding="utf8") as f:
        f.write(time_formatted + '| ' + log + '\n\n')
    storage.child(genlog_filepath).put(genlog_filepath)


def failed_message(msg, origin, ex):
    '''Exceptions related to specific signal groups messages
    Example: an error in Hirns signal format, or couldn't match the coin type'''
    now = datetime.now(tz)
    month_year = now.strftime('%B-%Y')

    failedmsg_filepath = paths.SAVE_TRADE + origin + '/failed/' + month_year + '.txt'
    failedmsg_dirpath = failedmsg_filepath.rsplit('/', 1)[0]+'/'
    if not os.path.exists(failedmsg_dirpath):
        os.makedirs(failedmsg_dirpath)

    storage.child(failedmsg_filepath).download("./", failedmsg_filepath)
    with open(failedmsg_filepath, 'a', encoding="utf8") as f:
        f.write(msg + '\n')
        f.write('__________________________\n')
        f.write(str(ex))
        f.write('\n\n')
    storage.child(failedmsg_filepath).put(failedmsg_filepath)


def realtime_signal_logs(msg):
    '''Logs general program runtime for debugging purposes'''
    now = datetime.now(tz)
    timestamp = str(int(now.timestamp()*1000))
    month_year = now.strftime('%B-%Y')
    date_formatted = now.strftime('%d-%b-%y')
    time_formatted = now.strftime('%H:%M:%S:')
    genlog_filepath = paths.LOG + date_formatted + '/signal_logging/' + timestamp
    push_to_realtime(genlog_filepath, msg)


def get_from_realtime(pathway):
    for key,value in paths.items():
        if pathway == key:
            pathway = value
            print(f"Matched Key: {key}, Value: {value}")
    return database.child(pathway).get()


def set_to_realtime(pathway, data):
    database.child(pathway).set(data)

def add_to_realtime(pathway, data):
    try:
        existing_data = database.child(pathway).get().val()
        existing_data.update(data)
    except:
        existing_data = data
    database.child(pathway).update(existing_data)

def push_to_realtime(pathway, data):
    database.child(pathway).set(data)

def add_discord_channel(id, name, category):
    splitids = id.split('-')
    guild_id = splitids[0]
    channel_id = splitids[1]
    data = {
        'guild_id': guild_id,
        'channel_id': channel_id,
        'channel_name': name,
        'type': category,
    }
    print('DATA:',data)
    add_to_realtime(paths.DISCORD_CHANNEL +f"/{guild_id}/{channel_id}", data)
    print('Added new discord channel')

def add_telegram_channel(id, name, category):
    data = {
        id: name,
    }
    add_to_realtime(paths.TELEGRAM_CHANNEL +f"/{category}", data)
    print('Added new telegram channel')


def get_discord_channels():
    return get_from_realtime(paths.DISCORD_CHANNEL).val()


def post_results(data):
    response = requests.post(paths.RESULTS_ENDPOINT_URL, json=data)
    if response.status_code == 200:
        print("Request to (", paths.RESULTS_ENDPOINT_URL, "succeeded!")
        print("Response content:", response.json())
    else:
        print(f"Request failed with status code {response.status_code}")
        print("Response content:", response.text)

def post_signal(data):
    response = requests.post(paths.SIGNAL_ENDPOINT_URL, json=data)
    if response.status_code == 200:
        print("Request to (", paths.SIGNAL_ENDPOINT_URL, "succeeded!")
        print("Response content:", response.json())
    else:
        print(f"Request failed with status code {response.status_code}")
        print("Response content:", response.text)


def save_raw_signal(signal):
    signal_group = signal.source
    path = paths.RAW_SIGNALS + signal_group

    print('\nSaving to realtime...',path)
    jsonData = signal.get_json()
    json_data_dict = json.loads(jsonData)
    print('Saving Signal', json_data_dict,'\n')
    key = str(json_data_dict['time_generated'])
    database.child(path).child(key).update(json_data_dict)


def generate_signals_from_timeframe(days = 7, start_time=None, end_time=None, override=False):
    path = paths.RAW_SIGNALS
    data = database.child(path).get().val()
    time_generated_list = []
    signals_list = []

    if start_time:
        #TODO generate from specific timeframe
        raise Exception('This section not implemented yet')
    else:
        timeframe = datetime.now() - timedelta(days = days)
    # Iterate over the outer dictionary
    for outer_key, outer_value in data.items():
        # Iterate over the inner dictionary
        for inner_key, inner_value in outer_value.items():
            # Extract the time_generated field
            # print('\n\nInnerValue:', inner_value)
            time_generated = inner_value['time_generated']
            time_generated_dt = datetime.fromtimestamp(time_generated/1000)
            if time_generated_dt > timeframe:
                signal = Signal.from_data(inner_value)
                signals_list.append(signal)
    return signals_list


def save_signals(signals_list):
    signal_group_paths = set([paths.RAW_SIGNALS + signal.source for signal in signals_list])
    existing_data_dict = {}

    # Download existing data for all signal groups
    for path in signal_group_paths:
        existing_data_dict[path] = database.child(path).get().val()

    for signal in signals_list:
        jsonData = signal.get_json()
        json_data_dict = json.loads(jsonData)

        path = paths.RAW_SIGNALS + signal.source
        key = str(json_data_dict['time_generated'])

        # If data exists and is the same as new data, don't update
        if path in existing_data_dict and key in existing_data_dict[path] and existing_data_dict[path][key] == json_data_dict:
            print("Data has not changed, skipping update.")
            continue

        # Call save_raw_signal if data has changed
        save_raw_signal(signal)


def generate_trades(signals_list, override = False):
    for signal in signals_list:
        signal.generate_trades(override) #If true generate trades, if false only generate non-existant trades


def backtest_trades(signals_list):
    for signal in signals_list:
        signal.backtest_trades(override = True) # Force Backtest


def deep_backtest_signals(signals_list):
    for signal in signals_list:
        signal.backtest_self(override = False) # If doesn't exist generate trades


def backtest_signals(signals_list):
    for signal in signals_list:
        signal.backtest_self()

def post_trades(signals_list):
    time_generated_list = []

    for signal in signals_list:
        trades = signal.trades
        if trades:
            for t in trades:
                post_data = t.get_trade_dict(signal) # might need to remove this?
                try:
                    print('test', post_data['timeout'])
                except:
                    print('postdata: no time genreated:', post_data)
                time_generated_list.append(post_data)   

    time_sorted_data = sorted(time_generated_list, key=lambda x: x['timeout'])
    for t in time_sorted_data:
        timestamp_ms = t['time_generated']
        timeout_ms = t['timeout']

        timestamp_s = timestamp_ms / 1000.0
        timeout_s = timeout_ms / 1000.0
        timestamp_dt = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
        timeout_dt = datetime.fromtimestamp(timeout_s, tz=timezone.utc)

    # Get the current datetime (in UTC)
        now = datetime.now(timezone.utc)

        # Calculate the difference
        difference = now - timestamp_dt
        timeout_diff = timeout_dt - timestamp_dt
        hours_difference = difference.total_seconds() / 3600.0
        to_hours_difference = timeout_diff.total_seconds() / 3600.0
        print(t,hours_difference,to_hours_difference,'\n')
    post_signal(time_sorted_data)

def post_backtest_results(signals_list):
    backtest_results_list = []

    for signal in signals_list:
        backtest_results = signal.get_backtest_results_dict()
        if backtest_results is not None:
            print('\n\nTESTRESULTS:',backtest_results)
            backtest_results_list.extend(backtest_results)
            
    print('\n\nFINAL',backtest_results_list)
    backtest_results_sorted = backtest_results_list.sort(key=lambda x: x['results'][0]['start'])
    post_results(backtest_results_sorted)

def generate_last_week_signals():
    path = paths.RAW_SIGNALS
    data = database.child(path).get().val()
    one_week = datetime.now() - timedelta(days=7)
    time_generated_list = []
    print('generating last week signals...')

    # Iterate over the outer dictionary
    for outer_key, outer_value in data.items():
        # Iterate over the inner dictionary
        for inner_key, inner_value in outer_value.items():
            # Extract the time_generated field
            time_generated = inner_value['time_generated']
            time_generated_dt = datetime.fromtimestamp(time_generated/1000)
            if time_generated_dt > one_week:
                trade = handle_signal_message.trade_from_signal_data(inner_value, True)
                if trade:
                    trade.run_backtest()
                    post_data = trade.get_dict()
                    time_generated_list.append(post_data)
    time_sorted_data = sorted(time_generated_list, key=lambda x: x['time_generated'])
    post_signal(time_sorted_data)
    # Print the list of extracted values


def get_old_signals():
    print('getting them')
    path = paths.RAW_SIGNALS
    data = database.child(path).get().val()
    one_week = datetime.now() - timedelta(days=7)
    time_generated_list = []
    print('generating last week signals...')
    # Iterate over the outer dictionary
    for outer_key, outer_value in data.items():
        # Iterate over the inner dictionary
        for inner_key, inner_value in outer_value.items():
            # Extract the time_generated field
            time_generated = inner_value['time_generated']
            time_generated_dt = datetime.fromtimestamp(time_generated/1000)
            if time_generated_dt > one_week:
                signal = handle_signal_message.signal_from_signal_data(inner_value)
                if signal:
                    print(signal, type(signal))
                    time_generated_list.append(signal)
    time_sorted_data = sorted(time_generated_list, key=lambda x: x.time_generated)
    print('Returning:', time_sorted_data)
    return time_sorted_data


def change_database_value():
    '''Can change the path, and values you want to replace in database to anything'''
    find_value = 'take_profit'
    replacement_value = ''
    path = paths.RAW_SIGNALS
    data = database.child(path).get().val()
    #print('\n\n',data,'\n\n')
    # Iterate over the outer dictionary
    for outer_key, outer_value in data.items():
        # Iterate over the inner dictionary
        for inner_key, inner_value in outer_value.items():
            if(find_value in inner_value and isinstance(inner_value[find_value], str)):
                inner_value[find_value] = [inner_value[find_value]]
                print('\nInner Value', inner_value[find_value], type(inner_value[find_value]))
                #inner_value[replacement_value] = inner_value.pop(find_value)
                database.child(path).child(outer_key).child(inner_key).set(inner_value)
                print('\n\nReplaced Value\n\n')


def delete_database_duplicates():
    path = paths.RAW_SIGNALS
    data = database.child(path).get().val()

    seen_entries = {}  # Will contain the latest entries with a unique message

    for outer_key, outer_value in data.items():
    # Iterate over the inner dictionary
        for inner_key, inner_value in outer_value.items():
            comp_key = inner_value['message']['message']

            if comp_key in seen_entries:
                # If current entry is newer than the one in seen_entries, delete it
                if inner_value['time_generated'] > seen_entries[comp_key]['time_generated']:
                    print('Deleting Duplicate...', inner_value)
                    database.child(path).child(outer_key).child(inner_key).remove()
                # If current entry is older, delete the newer one in seen_entries and update seen_entries
                else:
                    print('Deleting...')
                    database.child(path).child(seen_entries[comp_key]['outer_key']).child(seen_entries[comp_key]['inner_key']).remove()
                    seen_entries[comp_key] = {'time_generated': inner_value['time_generated'],
                                                'outer_key': outer_key, 'inner_key': inner_key}
            else:
                seen_entries[comp_key] = {'time_generated': inner_value['time_generated'],
                                            'outer_key': outer_key, 'inner_key': inner_key}
                

def delete_database_almost_duplicates():
    path = paths.RAW_SIGNALS
    data = database.child(path).get().val()

    seen_entries = {}  # Will contain the latest entries with a unique message

    for outer_key, outer_value in data.items():
    # Iterate over the inner dictionary
        for inner_key, inner_value in outer_value.items():
            # Concatenating the required keys to make a unique entry
            keys_to_check = [
                inner_value['coin'],
                inner_value['base'],
                inner_value['direction'],
                str(inner_value['entry']),
                inner_value['source'],
                str(inner_value['stop_loss']),
                str(inner_value['take_profit']),
            ]

            comp_key = "|".join(keys_to_check)

            # If the comp_key is already in the seen_entries, print it because it's a duplicate
            if comp_key in seen_entries:
                # Convert the time_generated of both the current and duplicate entry to a datetime object
                timestamp1 = datetime.fromtimestamp(inner_value['time_generated'] / 1000)  # divide by 1000 to convert ms to s
                timestamp2 = datetime.fromtimestamp(seen_entries[comp_key]['value']['time_generated'] / 1000)  # divide by 1000 to convert ms to s

                # Calculate the time difference
                time_difference = timestamp1 - timestamp2

                print("\nDuplicate Entry:")
                print(inner_value,'|||\n------\n',seen_entries[comp_key],'\n')
                print(f"Time difference: {time_difference}\n\n")
                # Check which entry is newer and delete it
                if timestamp1 > timestamp2:
                    print('Deleting newer entry...')
                    database.child(path).child(outer_key).child(inner_key).remove()
                else:
                    print('Deleting older entry...')
                    database.child(path).child(seen_entries[comp_key]['outer_key']).child(seen_entries[comp_key]['inner_key']).remove()
                    seen_entries[comp_key] = {'value': inner_value, 'outer_key': outer_key, 'inner_key': inner_key}
            else:
                # Else, add it to seen_entries
                seen_entries[comp_key] = {'value': inner_value, 'outer_key': outer_key, 'inner_key': inner_key}
                   
