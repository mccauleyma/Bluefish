from sys import exit
import pandas as pd
import numpy as np
import time
from datetime import datetime
import PySimpleGUI as sG
import os
import excel_processing as xp

temp_log = ""
if os.name == 'nt':
    bf_icon = 'img\\blue-fish-clipart.ico\\blue-fish-clipart.ico'
else:
    bf_icon = 'img/blue-fish-clipart.png'


def get_csv(file):
    """ get_csv(file)
    file = file path to a csv data file
    Reads a given csv and copies the data to a formatted DataFrame. This structure is declare as a global variable,
    rather than returning the frame.
    RETURNS None
    """
    df = pd.DataFrame

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
        time_size = len(dataFiles[i]['Timestamp'].unique())

        for ii in range(len(address_table[i])):
            if address_table[i][ii].index.size > (white_noise_threshold * time_size):
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
                    matching_table.iat[in_ii, in_i] = \
                        [x + '-' if x == address else x for x in matching_table.iat[in_ii, in_i]]
                    matching_table.iat[out_i, out_ii] = \
                        [x + '+' if x == address else x for x in matching_table.iat[out_i, out_ii]]
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

    if os.name == 'nt':
        path = output_path + '\\' + output_name + '.csv'
    else:
        path = output_path + '/' + output_name + '.csv'

    output_table.to_csv(path_or_buf=path, index=False)
    excel = xp.create_excel_from_df(output_table, output_path, output_name)
    xp.format_excel(excel[0], excel[1], excel[2])


dataFiles, dataFilesBackup, address_table, time_offsets, approach_names, primary_approaches = [], [], [], [], [], []

layout = [[sG.Text('Configure import and select files')],
          [sG.Text('Submitted files'), sG.Multiline('', size=(70, 5), key='_FILES_', autoscroll=True)],
          [sG.Text('Select Files'), sG.FileBrowse(target='_FILE_NAME_'),
           sG.Input(key='_FILE_NAME_', visible=False, enable_events=True)],
          [sG.Text('White Noise Threshold'),
           sG.Slider(range=(0, 100), key='_WHITE_NOISE_', default_value=10, orientation='horizontal')],
          [sG.Text('Scan Time'), sG.InputText('5', key='_SCAN_TIME_'), sG.Text('Scan Error'),
           sG.InputText('', key='_SCAN_ERROR_')],
          [sG.Text('Start Datetime'), sG.InputText('MM/DD/YY hh:mm:ss', key='_TOTAL_START_DATE_')],
          [sG.Text('End Datetime'), sG.InputText('MM/DD/YY hh:mm:ss', key='_TOTAL_END_DATE_')],
          [sG.Text('Output Folder'), sG.FolderBrowse(target='_OUT_FOLDER_'),
           sG.Input(key='_OUT_FOLDER_')],
          [sG.Text('Output File Name'), sG.InputText('', key='_OUT_FILE_NAME_')],
          [sG.Ok(), sG.Cancel(), sG.Button(button_text='Format CSV', key='_F_CSV_')]]

window = sG.Window("Bluefish File Processor", layout, icon=bf_icon)

while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == 'Exit' or event == 'Cancel':
        exit()
    if event == '_FILE_NAME_':
        window.Element('_FILES_').Update(window.Element('_FILES_').Get() + window.Element('_FILE_NAME_').Get())
        get_csv(window.Element('_FILE_NAME_').Get())
    elif event == 'Ok':
        noise_threshold = values['_WHITE_NOISE_']
        total_start_time = window.Element('_TOTAL_START_DATE_').Get()
        total_end_time = window.Element('_TOTAL_END_DATE_').Get()
        out_folder = window.Element('_OUT_FOLDER_').Get()
        out_file_name = window.Element('_OUT_FILE_NAME_').Get()
        scan_time_in = window.Element('_SCAN_TIME_').Get()
        scan_error_in = window.Element('_SCAN_ERROR_').Get()
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

                cancelled = False
                for k in range(0, len(dataFiles)):
                    text_name_in, text_time_in = '', ''

                    if cancelled is False:
                        window2 = sG.Window(layout=[[sG.Text('Name for Approach'), sG.InputText(key='_NAME_')],
                                                    [sG.Text('Data Start Time'), sG.InputText('hh:mm:ss', key='_TIME_')],
                                                    [sG.Checkbox('Designate Primary Approach', key='_PRIMARY_')],
                                                    [sG.Ok(), sG.Cancel()]],
                                            title='Data File Setup #' + str(k + 1),
                                            icon=bf_icon)

                        while True:  # Nested Event Loop
                            event2, values2 = window2.Read()
                            if event2 is None or event2 == 'Exit' or event2 == 'Cancel':
                                cancelled = True
                                break
                            if event2 == 'Ok':
                                text_name_in = window2.Element('_NAME_').Get()
                                text_time_in = window2.Element('_TIME_').Get()

                                if text_name_in is None or text_name_in == '':
                                    sG.PopupError('Please enter a name', icon=bf_icon)
                                else:
                                    try:
                                        time.strptime(text_time_in, '%H:%M:%S')
                                    except ValueError:
                                        sG.PopupError('Please enter a valid time in hh:mm:ss format', icon=bf_icon)
                                        window2.Element('_TIME_').Update('hh:mm:ss')
                                    except TypeError:
                                        sG.PopupError('Please enter a time', icon=bf_icon)
                                    else:
                                        break

                        if cancelled is False:
                            approach_names.append(text_name_in)
                            primary_approaches.append(values2['_PRIMARY_'])
                            process_file(k, start_day + ' ' + text_time_in)

                        window2.Close()

                if cancelled is False:
                    break
                else:
                    approach_names, primary_approaches = [], []
                    address_table = setup_address_table()
                    dataFiles = dataFilesBackup
                    temp_log = temp_log + "Cancelled -> Reset Approaches\n"

    elif event == '_F_CSV_':
        input_file = sG.PopupGetFile('Select a CSV file to convert to Excel', 'Input File', icon=bf_icon)
        if input_file is not None:
            output_folder_path = sG.PopupGetFolder('Select a folder to output to', 'Output Destination', icon=bf_icon)
            if output_folder_path is not None:
                ex_file = xp.create_excel_from_csv(input_file, output_folder_path)
                xp.format_excel(ex_file[0], ex_file[1], ex_file[2])

window.Close()

time_to_cross = []
matching_table = pd.DataFrame
matching_table_debug = pd.DataFrame
output_table = pd.DataFrame

layout = [[sG.Text('Data Processing')],
          [sG.Multiline(temp_log + 'Click SUBMIT to start processing', key='_CONSOLE_', autoscroll=True)],
          [sG.Submit(), sG.CloseButton('Close')]]

window = sG.Window("Bluefish Data Processor", layout, icon=bf_icon)

while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == 'Close':
        exit()
    if event == 'Submit':
        cancelled = False
        for j in range(len(address_table)):
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
            cont_processing(noise_threshold, int(scan_time_in), int(scan_error_in))
            match_movements(total_start_time, total_end_time, out_folder, out_file_name, int(scan_time_in))
            window.Element('_CONSOLE_').Update(window.Element('_CONSOLE_').Get() + "----PROCESSING COMPLETE----")
        else:
            time_to_cross = []
