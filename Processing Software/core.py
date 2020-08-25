from sys import exit
import pandas as pd
import numpy as np
import time
from datetime import datetime
import PySimpleGUI as sG
import os
import excel_processing as xp
from json import (load as jsonload, dump as jsondump)

SCAN_TIME = 4

temp_log = ""

if os.name == 'nt':
    os_slash = '\\'
else:
    os_slash = '/'

if os.name == 'nt':
    bf_icon = 'img\\blue-fish-clipart.ico\\blue-fish-clipart.ico'
else:
    bf_icon = 'img/blue-fish-clipart.png'

config_dict = {
    "FC": 0,
    "FMl": "",
    "WN": "100",
    "TU": True,
    "SE": "",
    "SDt": "MM/DD/YY hh:mm:ss",
    "EDt": "MM/DD/YY hh:mm:ss",
    "OF": "",
    "OFN": ""
}
recovery_opt = 0


def get_csv(file):
    """ get_csv(file)
    file = file path to a csv data file
    Reads a given csv and copies the data to a formatted DataFrame. This structure is declare as a global variable,
    rather than returning the frame.
    RETURNS None
    """
    os.rename(file, file[0:-3] + "csv")
    df = pd.read_csv(file[0:-3] + "csv", sep='\s*,\s*', engine='python')

    if file[-3:] != "csv":
        df['Address'] = df['Timestamp']
        df['Timestamp'] = df.index

    print(df)
    dataFiles.append(df)
    dataFilesBackup.append(df)


def remove_values_from_list(the_list, val):
    """ remove_values_from_list(the_list, val)
    Given a list and a target value, this function will return the same list without the targeted value.
    RETURNS Array"""
    return [value for value in the_list if value is not val]


def setup_table(interval, start, end, column_list, multi_dim):
    """ setup_table(interval, start, end, column_list, multi_dim)
    interval = BT scan interval in milliseconds
    start = start time in seconds since epoch; end = end time ' '
    column_list = array of names for each column
    multi_dim = T/F if table is multidimensional
    Creates an empty table with expected time intervals in the 'Time' column. Additionally will make multiple dimensions
    if needed, based on the quantity of data files imported by the script.
    RETURNS DateFrame"""
    time_array = []
    dataframe = pd.DataFrame(columns=column_list)

    for i in range(start, end, interval):
        time_array.append(i)

    dataframe['Time'] = time_array

    if multi_dim is True:
        out = [dataframe]
        for i in range(len(dataFiles)):
            out.append(dataframe)
        return out
    else:
        return dataframe


def setup_address_table():
    """ setup_address_table()
    Creates a blank multi-dimensional array based on the number of data files imported
    RETURNS Array"""
    out = []
    for i in range(len(dataFiles)):
        out.append([])

    return out


def process_file(index, offset_time):
    """ process_file(index, offset_time)
    index = index of the target file in the dataFile array
    offset_time = text input of what time the target file started recording in MM/DD/YY hh:mm:ss format
    Edits the target data file such that timestamps are in time since epoch (rather than time since system boot up).
    Additionally counts unique addresses, for early analysis/human error detection, which is added to the temp log.
    These unique addresses are stored in the address_table for further use.
    RETURNS None"""
    time_offset = time.mktime(time.strptime(offset_time, '%m/%d/%y %H:%M:%S')) * 1000
    time_offsets.append(time_offset)
    dataFiles[index]['Timestamp'] = dataFiles[index]['Timestamp'].add(time_offset)

    unique_addresses = dataFiles[index]['Address'].unique()

    for i in range(len(unique_addresses)):
        address_table[index].append(dataFiles[index].loc[dataFiles[index]['Address'] == unique_addresses[i]])

    global temp_log
    temp_log = temp_log + "Found " + str(len(unique_addresses)) + " unique addresses in approach " \
        + approach_names[index] + "\n"


def cont_processing(white_noise_threshold, scan_time, scan_error):
    """ cont_processing(white_noise_threshold, scan_time, scan_error)
    white_noise_threshold = percentage presence a MAC needs to be considered noise
    scan_time = BT scan time in seconds
    scan_error = number of scans that can be missed before being considered a new presence/arrival
    Checks the count of each unique address against the count of time intervals in the dataset. If the address is
    present in a percentage of intervals greater than given by the threshold then the address is entirely removed. Time
    differentials between occurrences of each MAC are calculated and utilized to determine when an address is considered
    miss-scanned or an actual new occurrence. Each block of addresses considered a single occurrence are reduced to one.
    RETURNS None"""
    white_noise_count = 0

    for i in range(len(address_table)):
        for ii in range(len(address_table[i])):
            if address_table[i][ii].index.size > white_noise_threshold:
                address_table[i][ii] = 0
                white_noise_count += 1

        address_table[i] = remove_values_from_list(address_table[i], 0)

    for i in range(len(address_table)):
        for ii in range(len(address_table[i])):
            address_table[i][ii]['Time_Dif'] = address_table[i][ii]['Timestamp'] - \
                                               address_table[i][ii]['Timestamp'].shift(1)
            address_table[i][ii] = address_table[i][ii] \
                .drop(address_table[i][ii][address_table[i][ii]['Time_Dif'] < (scan_time * scan_error * 1000)].index)

        address_table[i] = remove_values_from_list(address_table[i], 0)

        global temp_log
        window.Element('_CONSOLE_').Update(window.Element('_CONSOLE_').Get() + "Removed " + str(white_noise_count) +
                                           " white-noise addresses from approach " + approach_names[i])


def check_inner_loop(out_i, out_ii, address, interval, time_range):
    """ check_inner_loop(out_i, out_ii, address, interval, time_range)
    out_i = Start row index
    out_ii = Start column index
    address = MAC address that is being searched for
    interval = scan time in milliseconds
    time_range = maximum time to cross in seconds
    Given a start index and an address, this function checks the data frame for another occurrence of the given address,
    within the maximum time to cross. If a match is found, the address is added to the output table in the matched cell.
    RETURNS None"""
    for jj in range(1, len(approach_names) + 1):
        if jj != out_ii:
            if address in matching_table.iat[out_i, jj]:
                if primary_approaches[out_ii - 1] == primary_approaches[jj - 1]:
                    return
                elif primary_approaches[out_ii - 1] is False and primary_approaches[jj - 1] is True:
                    return
                else:
                    break

    for in_ii in reversed(range(out_i + 1, out_i + int((time_range * 1000) / interval))):
        if in_ii < len(matching_table['Time']):
            for in_i in range(1, len(approach_names) + 1):
                if address in matching_table.iat[in_ii, in_i]:
                    # logically this is: (((out_ii - 1) * len(approach_names)) + 1) + (in_i - 1), but the +/- 1 cancel
                    output_table.iat[in_ii, ((out_ii - 1) * len(approach_names)) + in_i] = \
                        output_table.iat[in_ii, ((out_ii - 1) * len(approach_names)) + in_i] + 1
                    output_table_timings.append(
                        [address, matching_table['Time'].iat[out_i], matching_table['Time'].iat[in_ii],
                         approach_names[out_ii - 1], approach_names[in_i - 1],
                         (matching_table['Time'].iat[in_ii] - matching_table['Time'].iat[out_i]) / 1000])
                    matching_table.iat[in_ii, in_i] = \
                        [x + '-' + str(in_ii) if x == address else x for x in matching_table.iat[in_ii, in_i]]
                    matching_table.iat[out_i, out_ii] = \
                        [x + '+' + str(out_i) if x == address else x for x in matching_table.iat[out_i, out_ii]]
                    return


def match_movements(start_time_entry, end_time_entry, output_path, output_name, scan_time):
    """ match_movements(end_time_entry, output_path, output_name, scan_time)
    end_time_entry = text entry of end time in MM/DD/YY hh:mm:ss format
    output_path = output folder path
    output_name = output file name
    scan_time = BT scan interval in seconds
    Creates a matching table consisting of all address scanned at each approach at each time. User is then prompted to
    enter the maximum time to cross for each approach. This is then utilized to search for pairs within the matching
    table, which are removed when found and added counted in the output table.
    RETURNS None"""
    if len(dataFiles) < 2:
        window.Element('_CONSOLE_').Update(window.Element('_CONSOLE_').Get() +
                                           "Cannot match movements with less than 2 approaches")
        return

    columns = approach_names
    columns.insert(0, 'Time')
    factor = 1000 * scan_time
    start_time = time.mktime(time.strptime(start_time_entry, '%m/%d/%y %H:%M:%S')) * 1000
    end_time = time.mktime(time.strptime(end_time_entry, '%m/%d/%y %H:%M:%S')) * 1000
    global matching_table
    matching_table = setup_table(factor, int((min(time_offsets) / factor) * factor),
                                 int((end_time / factor) * factor), columns, False)
    approach_names.remove('Time')
    blank = []
    for i in range(len(matching_table['Time'])):
        blank.append([])
    for name in approach_names:
        matching_table[name] = blank

    for i in range(len(address_table)):
        window.Element('_CONSOLE_').Update(window.Element('_CONSOLE_').Get() + "Preparing " +
                                           approach_names[i] + " for matching")
        for ii in range(len(address_table[i])):
            address = address_table[i][ii]['Address'].iloc[0]
            for iii in range(len(address_table[i][ii]['Timestamp'])):
                timestamp = address_table[i][ii]['Timestamp'].iloc[iii]
                index = matching_table.loc[((matching_table['Time'] < timestamp) &
                                            (matching_table['Time'] > (timestamp - factor))),
                                           approach_names[i]].index.values
                if len(index) == 0:
                    break
                else:
                    index = index.astype(int)[0]
                temp_val = matching_table.loc[((matching_table['Time'] < timestamp) &
                                               (matching_table['Time'] > (timestamp - factor))),
                                              approach_names[i]].values[0]
                temp = temp_val.copy()
                temp.append(address)
                matching_table.iat[index, i + 1] = temp

    global output_table
    output_table = setup_table(factor, int((min(time_offsets) / factor) * factor),
                               int((end_time / factor) * factor), ['Time'], False)

    for i in range(len(approach_names)):
        for ii in range(len(approach_names)):
            output_table[approach_names[i] + ' -> ' + approach_names[ii]] = np.nan
    output_table = output_table.fillna(0)

    matching_table.drop(matching_table[matching_table['Time'] < start_time - max(time_to_cross)].index, inplace=True)
    output_table.drop(output_table[output_table['Time'] < start_time].index, inplace=True)
    global matching_table_debug
    matching_table_debug = matching_table.copy()  # Record for debugging

    for i in range(len(matching_table['Time'])):
        for ii in range(1, len(approach_names) + 1):
            cell = matching_table.iat[i, ii]
            if len(cell) > 0:
                for iii in range(len(cell)):
                    address = cell[iii]
                    check_inner_loop(i, ii, address, factor, time_to_cross[ii - 1])

    global output_table_timings
    output_table_timings = pd.DataFrame(data=output_table_timings,
                                        columns=['Address', 'Start Time', 'End Time', 'Start Location', 'End Location',
                                                 'Elapsed'])

    path = output_path + os_slash + output_name + '.csv'
    path_timing = output_path + os_slash + output_name + '_timings.csv'

    output_table.to_csv(path_or_buf=path, index=False)
    output_table_timings.to_csv(path_or_buf=path_timing, index=False)
    excel = xp.create_excel_from_df(output_table, output_path, output_name)
    xp.format_excel(excel[0], excel[1], excel[2])


dataFiles, dataFilesBackup, address_table, time_offsets, approach_names, primary_approaches, file_paths, settings = \
    [], [], [], [], [], [], [], []

window2 = sG.Window("Session Recovery",
                    [[sG.Radio('Files', "_RECOV_OPT_", size=(50, 1))],
                     [sG.Radio('Approach Config', "_RECOV_OPT_", size=(50, 1))],
                     [sG.Ok(), sG.Cancel()]],
                    icon=bf_icon)

while True:
    event, values = window2.Read()
    if event is None or event == 'Exit' or event == 'Cancel':
        break
    if event == 'Ok':
        if values[0]:
            recovery_opt = 1
        elif values[1]:
            recovery_opt = 2
        else:
            break
        config_file = sG.popup_get_file("Select your config file", "Select Configuration", icon=bf_icon)
        if config_file == '' or config_file is None:
            recovery_opt = 0
            break
        else:
            try:
                with open(config_file, 'r') as f:
                    config_dict = jsonload(f)
            except Exception as e:
                sG.popup_quick_message(f'exception {e}', keep_on_top=True, background_color='red', text_color='white')
            break

window2.Close()

layout = [[sG.Text('Configure import and select files')],
          [sG.Text('Submitted files', size=(20, 1)), sG.Multiline(config_dict['FMl'], size=(70, 5), key='_FILES_', autoscroll=True)],
          [sG.Text('Select Files', size=(20, 1)), sG.FileBrowse(target='_FILE_NAME_'),
           sG.Input(key='_FILE_NAME_', visible=False, enable_events=True)],
          [sG.Text('White Noise Threshold', size=(20, 1)),
           sG.Slider(range=(0, 500), key='_WHITE_NOISE_', default_value=config_dict['WN'], orientation='horizontal')],
          [sG.Text('TTC Value Entry', size=(20, 1)), sG.Radio('Unified', 'TTC_Entry', default=config_dict['TU']),
           sG.Radio('Individual', 'TTC_Entry', default=(not config_dict['TU']))],
          [sG.Text('Scan Error', size=(20, 1)), sG.InputText(config_dict['SE'], key='_SCAN_ERROR_', size=(10, 10), enable_events=True)],
          [sG.Text('Start Datetime', size=(20, 1)),
           sG.InputText(config_dict['SDt'], key='_TOTAL_START_DATE_', size=(20, 10), enable_events=True)],
          [sG.Text('End Datetime', size=(20, 1)),
           sG.InputText(config_dict['EDt'], key='_TOTAL_END_DATE_', size=(20, 10), enable_events=True)],
          [sG.Text('Output Folder', size=(20, 1)), sG.Input(config_dict['OF'], key='_OUT_FOLDER_'),
           sG.FolderBrowse(target='_OUT_FOLDER_')],
          [sG.Text('Output File Name', size=(20, 1)), sG.InputText(config_dict['OFN'], key='_OUT_FILE_NAME_')],
          [sG.Ok(), sG.Cancel(), sG.Button(button_text='Format CSV', key='_F_CSV_')]]

if recovery_opt is not 0:
    for n in range(0, config_dict['FC']):
        get_csv(config_dict['FNR' + str(n)])
        file_paths.append(config_dict['FNR' + str(n)])

window = sG.Window("Bluefish File Processor", layout, icon=bf_icon)

while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == 'Exit' or event == 'Cancel':
        exit()
    if event == '_FILE_NAME_':
        file_name_raw = window.Element('_FILE_NAME_').Get()
        if file_name_raw not in file_paths and file_name_raw != '':
            window.Element('_FILES_').Update(window.Element('_FILES_').Get() + file_name_raw)
            get_csv(file_name_raw)
            file_paths.append(file_name_raw)
    elif event == '_SCAN_ERROR_' and values['_SCAN_ERROR_'] and values['_SCAN_ERROR_'][-1] not in '0123456789':
        window['_SCAN_ERROR_'].update(values['_SCAN_ERROR_'][:-1])
    elif event == '_TOTAL_START_DATE_' and values['_TOTAL_START_DATE_'] and \
            values['_TOTAL_START_DATE_'][-1] not in '0123456789:/ ':
        window['_TOTAL_START_DATE_'].update(values['_TOTAL_START_DATE_'][:-1])
    elif event == '_TOTAL_END_DATE_' and values['_TOTAL_END_DATE_'] and \
            values['_TOTAL_END_DATE_'][-1] not in '0123456789:/ ':
        window['_TOTAL_END_DATE_'].update(values['_TOTAL_END_DATE_'][:-1])
    elif event == 'Ok':
        noise_threshold = values['_WHITE_NOISE_']
        total_start_time = window.Element('_TOTAL_START_DATE_').Get()
        total_end_time = window.Element('_TOTAL_END_DATE_').Get()
        out_folder = window.Element('_OUT_FOLDER_').Get()
        out_file_name = window.Element('_OUT_FILE_NAME_').Get()
        scan_error_in = window.Element('_SCAN_ERROR_').Get()
        ttc_unified = values[0]
        if total_end_time == '':
            sG.PopupError('Please enter an end time', icon=bf_icon, title='Error')
        elif total_start_time == '':
            sG.PopupError('Please enter a start time', icon=bf_icon, title='Error')
        elif out_folder == '':
            sG.PopupError('Please select an output directory', icon=bf_icon, title='Error')
        elif out_file_name == '':
            sG.PopupError('Please enter an output file name', icon=bf_icon, title='Error')
        elif scan_error_in == '':
            sG.PopupError('Please enter an acceptable scan error limit', icon=bf_icon, title='Error')
        else:
            try:
                time.strptime(total_start_time, '%m/%d/%y %H:%M:%S')
                time.strptime(total_end_time, '%m/%d/%y %H:%M:%S')
            except ValueError:
                sG.PopupError('Please enter datetimes in MM:DD:YY hh:mm:ss format', icon=bf_icon, title='Error')
                window.Element('_TOTAL_START_DATE_').Update('MM:DD:YY hh:mm:ss')
                window.Element('_TOTAL_END_DATE_').Update('MM:DD:YY hh:mm:ss')
            else:
                address_table = setup_address_table()

                start_day = datetime.fromtimestamp(
                    time.mktime(time.strptime(total_start_time, '%m/%d/%y %H:%M:%S'))).strftime('%m/%d/%y')

                if recovery_opt == 0 or recovery_opt == 1:
                    cancelled = False
                    for k in range(0, len(dataFiles)):
                        text_name_in, text_time_in = '', ''

                        if cancelled is False:
                            path_split = file_paths[k].split(os_slash)
                            win2 = sG.Window(layout=[[sG.Text('Name for Approach'), sG.InputText(key='_NAME_')],
                                                     [sG.Text('Data Start Time'),
                                                      sG.InputText('hh:mm:ss', key='_TIME_')],
                                                     [sG.Checkbox('Designate Primary Approach', key='_PRIMARY_')],
                                                     [sG.Ok(), sG.Cancel()]],
                                             title='Data File Setup #' + str(k + 1) +
                                                   ': ' + path_split[len(path_split) - 1],
                                             icon=bf_icon)

                            while True:  # Nested Event Loop
                                event2, values2 = win2.Read()
                                if event2 is None or event2 == 'Exit' or event2 == 'Cancel':
                                    cancelled = True
                                    break
                                if event2 == 'Ok':
                                    text_name_in = win2.Element('_NAME_').Get()
                                    text_time_in = win2.Element('_TIME_').Get()

                                    if text_name_in is None or text_name_in == '':
                                        sG.PopupError('Please enter a name', icon=bf_icon)
                                    else:
                                        try:
                                            time.strptime(text_time_in, '%H:%M:%S')
                                        except ValueError:
                                            sG.PopupError('Please enter a valid time in hh:mm:ss format', icon=bf_icon)
                                            win2.Element('_TIME_').Update('hh:mm:ss')
                                        except TypeError:
                                            sG.PopupError('Please enter a time', icon=bf_icon)
                                        else:
                                            break

                            if cancelled is False:
                                approach_names.append(text_name_in)
                                primary_approaches.append(values2['_PRIMARY_'])
                                process_file(k, start_day + ' ' + text_time_in)

                                config_dict['AN' + str(k)] = text_name_in
                                config_dict['PA' + str(k)] = values2['_PRIMARY_']
                                config_dict['T' + str(k)] = text_time_in

                            win2.Close()

                    if cancelled is False:
                        break
                    else:
                        approach_names, primary_approaches = [], []
                        address_table = setup_address_table()
                        dataFiles = dataFilesBackup
                        temp_log = temp_log + "Cancelled -> Reset Approaches\n"
                else:
                    for n in range(0, config_dict['FC']):
                        approach_names.append(config_dict['AN' + str(n)])
                        primary_approaches.append(config_dict['PA' + str(n)])
                        process_file(n, start_day + ' ' + config_dict['T' + str(n)])
                    break
    elif event == '_F_CSV_':
        input_file = sG.PopupGetFile('Select a CSV file to convert to Excel', 'Input File', icon=bf_icon)
        if input_file is not None:
            output_folder_path = sG.PopupGetFolder('Select a folder to output to', 'Output Destination', icon=bf_icon)
            if output_folder_path is not None:
                ex_file = xp.create_excel_from_csv(input_file, output_folder_path)
                xp.format_excel(ex_file[0], ex_file[1], ex_file[2])

config_dict['FMl'] = window.Element('_FILES_').Get()
window.Close()

config_dict['FC'] = len(dataFiles)
config_dict['WN'] = noise_threshold
config_dict['TU'] = ttc_unified
config_dict['SE'] = scan_error_in
config_dict['SDt'] = total_start_time
config_dict['EDt'] = total_end_time
config_dict['OF'] = out_folder
config_dict['OFN'] = out_file_name

for k in range(0, len(dataFiles)):
    config_dict['FNR' + str(k)] = file_paths[k]

time_to_cross = []
matching_table = pd.DataFrame
matching_table_debug = pd.DataFrame
output_table = pd.DataFrame
output_table_timings = []
rerun = False

layout = [[sG.Text('Data Processing')],
          [sG.Multiline(temp_log + 'Click SUBMIT to start processing', key='_CONSOLE_', autoscroll=True)],
          [sG.Submit(), sG.CloseButton('Close')]]

window = sG.Window("Bluefish Data Processor", layout, icon=bf_icon)

while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == 'Close':
        exit()
    if event == 'Submit':
        if rerun:
            out_file_name = sG.popup_get_text("You're rerunning with new TTC values. "
                                              "Please enter a new output file name", title="TTC Rerun")

        cancelled = False
        for j in range(len(address_table)):
            if ttc_unified and j > 0:
                for k in range(len(address_table) - 1):
                    time_to_cross.append(time_to_cross[0])
                continue
            valid = False
            ttc_in = ''
            while not valid and not cancelled:
                ttc_in = sG.PopupGetText(approach_names[j] + " time to cross (seconds): ", 'Time to Cross',
                                         icon=bf_icon)

                try:
                    int(ttc_in)
                except ValueError:
                    sG.PopupError('That was not a valid number. Please try again.', icon=bf_icon)
                except TypeError:
                    cancelled = True
                else:
                    valid = True
                    time_to_cross.append(int(ttc_in))

        if cancelled is False:
            cont_processing(noise_threshold, SCAN_TIME, int(scan_error_in))
            match_movements(total_start_time, total_end_time, out_folder, out_file_name, SCAN_TIME)
            window.Element('_CONSOLE_').Update(window.Element('_CONSOLE_').Get() + "----PROCESSING COMPLETE----")
            rerun = True

            with open(out_folder + os_slash + out_file_name + '.cfg', 'w') as f:
                jsondump(config_dict, f)
        else:
            time_to_cross = []
