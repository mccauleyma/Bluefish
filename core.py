import pandas as pd
import numpy as np
import time
from datetime import datetime
import PySimpleGUI as sg
import os

temp_log = ""
df = pd.DataFrame

""" get_csv(file)
file = file path to a csv data file
Reads a given csv and copies the data to a formatted DataFrame. This structure is declare as a global variable, rather
than returning the frame.
RETURNS None
"""


def get_csv(file):
    global df

    os.rename(file, file[0:-3] + "csv")
    df = pd.read_csv(file[0:-3] + "csv", sep='\s*,\s*', engine='python')

    if file[-3:] != "csv":
        df['Address'] = df['Timestamp']
        df['Timestamp'] = df.index

    print(df)
    dataFiles.append(df)


""" remove_values_from_list(the_list, val)
Given a list and a target value, this function will return the same list without the targeted value.
RETURNS Array"""


def remove_values_from_list(the_list, val):
    return [value for value in the_list if value is not val]


""" setup_table(interval, start, end, column_list, multi_dim)
interval = BT scan interval in milliseconds
start = start time in seconds since epoch; end = end time ' '
column_list = array of names for each column
multi_dim = T/F if table is multidimensional
Creates an empty table with expected time intervals in the 'Time' column. Additionally will make multiple dimensions
if needed, based on the quantity of data files imported by the script.
RETURNS DateFrame"""


def setup_table(interval, start, end, column_list, multi_dim):
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


""" setup_address_table()
Creates a blank multi-dimensional array based on the number of data files imported
RETURNS Array"""


def setup_address_table():
    out = []
    for i in range(len(dataFiles)):
        out.append([])

    return out


""" process_file(index, offset_time)
index = index of the target file in the dataFile array
offset_time = text input of what time the target file started recording in MM/DD/YY hh:mm:ss format
Edits the target data file such that timestamps are in time since epoch (rather than time since system boot up).
Additionally counts unique addresses, for early analysis/human error detection, which is added to the temp log. These 
unique addresses are stored in the address_table for further use.
RETURNS None"""


def process_file(index, offset_time):
    time_offset = time.mktime(time.strptime(offset_time, '%m/%d/%y %H:%M:%S')) * 1000
    time_offsets.append(time_offset)
    dataFiles[index]['Timestamp'] = dataFiles[index]['Timestamp'].add(time_offset)

    unique_addresses = dataFiles[index]['Address'].unique()

    for i in range(len(unique_addresses)):
        address_table[index].append(dataFiles[index].loc[dataFiles[index]['Address'] == unique_addresses[i]])

    global temp_log
    temp_log = temp_log + "Found " + str(len(unique_addresses)) + " unique addresses in approach "\
        + approach_names[index] + "\n"


""" cont_processing(white_noise_threshold, scan_time, scan_error)
white_noise_threshold = percentage presence a MAC needs to be considered noise
scan_time = BT scan time in seconds
scan_error = number of scans that can be missed before being considered a new presence/arrival
Checks the count of each unique address against the count of time intervals in the dataset. If the address is present
in a percentage of intervals greater than given by the threshold then the address is entirely removed. Time
differentials between occurrences of each MAC are calculated and utilized to determine when an address is considered
miss-scanned or an actual new occurrence. Each block of addresses considered a single occurrence are reduced to one.
RETURNS None"""


def cont_processing(white_noise_threshold, scan_time, scan_error):
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
            address_table[i][ii] = address_table[i][ii]\
                .drop(address_table[i][ii][address_table[i][ii]['Time_Dif'] < (scan_time * scan_error * 1000)].index)

        address_table[i] = remove_values_from_list(address_table[i], 0)

        global temp_log
        temp_log = temp_log + "Removed " + str(white_noise_count) + " white-noise addresses from approach "\
            + approach_names[i] + "\n"


""" check_inner_loop(out_i, out_ii, address, interval, time_range)
out_i = Start row index
out_ii = Start column index
address = MAC address that is being searched for
interval = scan time in milliseconds
time_range = maximum time to cross in seconds
Given a start index and an address, this function checks the data frame for another occurrence of the given address,
within the maximum time to cross. If a match is found, the address is added to the output table in the appropriate cell.
RETURNS None
"""


def check_inner_loop(out_i, out_ii, address, interval, time_range):
    # for in_ii in range(out_i + 1, out_i + int((time_range * 1000) / interval)):
    for in_ii in reversed(range(out_i + 1, out_i + int((time_range * 1000) / interval))):
        for in_i in range(1, len(approach_names) + 1):
            if in_ii < len(matching_table['Time']):
                if address in matching_table.iat[in_ii, in_i]:
                    # logically this is: (((out_ii - 1) * len(approach_names)) + 1) + (in_i - 1), but the +/- 1 cancel
                    output_table.iat[in_ii, ((out_ii - 1) * len(approach_names)) + in_i] =\
                        output_table.iat[in_ii, ((out_ii - 1) * len(approach_names)) + in_i] + 1
                    return


""" match_movements(end_time_entry, output_path, output_name, scan_time)
end_time_entry = text entry of end time in MM/DD/YY hh:mm:ss format
output_path = output folder path
output_name = output file name
scan_time = BT scan interval in seconds
Creates a matching table consisting of all address scanned at each approach at each time. User is then prompted to enter
the maximum time to cross for each approach. This is then utilized to search for pairs within the matching table, which
are removed when found and added counted in the output table.
RETURNS None"""


def match_movements(start_time_entry, end_time_entry, output_path, output_name, scan_time):
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

    matching_table.drop(matching_table[matching_table['Time'] < start_time].index, inplace=True)

    for i in range(len(matching_table['Time'])):
        for ii in range(1, len(approach_names) + 1):
            cell = matching_table.iat[i, ii]
            if len(cell) > 0:
                for iii in range(len(cell)):
                    address = cell[iii]
                    check_inner_loop(i, ii, address, factor, time_to_cross[ii - 1])

    output_table.drop(output_table[output_table['Time'] < start_time].index, inplace=True)

    if os.name == 'nt':
        path = output_path + '\\' + output_name + '.csv'
    else:
        path = output_path + '/' + output_name + '.csv'

    output_table.to_csv(path_or_buf=path, index=False)
    print(output_table)


dataFiles = []
address_table = []
time_offsets = []
approach_names = []

# First window layout and initialization
layout = [[sg.Text('Configure import and select files')],
          [sg.Radio('Combined', "FileProcess", key="_FILE_PROCESS_", default=True),
           sg.Radio('Separate', "FileProcess")],
          [sg.Text('Submitted files'), sg.Multiline('', size=(15, 5), key='_FILES_')],
          [sg.Text('Select Files'), sg.FileBrowse(target='_FILE_NAME_'),
           sg.Input(key='_FILE_NAME_', visible=False, enable_events=True)],
          [sg.Text('White Noise Threshold'),
           sg.Slider(range=(0, 100), key='_WHITE_NOISE_', default_value=25, orientation='horizontal')],
          [sg.Text('Scan Time'), sg.InputText('', key='_SCAN_TIME_'), sg.Text('Scan Error'),
           sg.InputText('', key='_SCAN_ERROR_')],
          [sg.Text('Start Date'), sg.InputText('MM/DD/YY hh:mm:ss', key='_TOTAL_START_DATE_')],
          [sg.Text('End Date'), sg.InputText('MM/DD/YY hh:mm:ss', key='_TOTAL_END_DATE_')],
          [sg.Text('Output Folder'), sg.FolderBrowse(target='_OUT_FOLDER_'),
           sg.Input(key='_OUT_FOLDER_')],
          [sg.Text('Output File Name'), sg.InputText('', key='_OUT_FILE_NAME_')],
          [sg.Ok(), sg.Cancel()]]

window = sg.Window("Bluefish File Processor", layout)

while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == 'Exit' or event == 'Cancel':
        break
    if event == '_FILE_NAME_':
        window.Element('_FILES_').Update(window.Element('_FILES_').Get() + window.Element('_FILE_NAME_').Get())
        get_csv(window.Element('_FILE_NAME_').Get())
    elif event == 'Ok':
        # TODO: File Process system (for separate files and offsets)
        address_table = setup_address_table()

        total_start_time = window.Element('_TOTAL_START_DATE_').Get()
        start_day = datetime.fromtimestamp(time.mktime(time.strptime(total_start_time, '%m/%d/%y %H:%M:%S'))).strftime('%m/%d/%y')

        for index_1 in range(0, len(dataFiles)):
            text_name_in = sg.PopupGetText('Enter a name for the approach in data file ' + str(index_1 + 1),
                                           'Approach Name')
            approach_names.append(text_name_in)
            text_time_in = sg.PopupGetText('Enter the start time in hh:mm:ss format for ' + approach_names[index_1])
            if sg.PopupYesNo('Are you sure ' + text_time_in + ' is correct?') != 'Yes':
                text_time_in = sg.PopupGetText('Enter the start time in hh:mm:ss format for ' + approach_names[index_1])
            process_file(index_1, start_day + ' ' + text_time_in)

        break

# Fetch values from window after submission
noise_threshold = values['_WHITE_NOISE_']
total_start_time = window.Element('_TOTAL_START_DATE_').Get()
total_end_time = window.Element('_TOTAL_END_DATE_').Get()
out_folder = window.Element('_OUT_FOLDER_').Get()
out_file_name = window.Element('_OUT_FILE_NAME_').Get()
scan_time_in = window.Element('_SCAN_TIME_').Get()
scan_error_in = window.Element('_SCAN_ERROR_').Get()

window.Close()

time_to_cross = []
matching_table = pd.DataFrame
output_table = pd.DataFrame

# Second window layout and initialization
layout = [[sg.Text('Data Processing')],
          [sg.Multiline(temp_log + 'Click SUBMIT to start processing', key='_CONSOLE_')],
          [sg.Submit(), sg.CloseButton('Close')]]

window = sg.Window("Bluefish Data Processor", layout)

while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == 'Close':
        break
    if event == 'Submit':
        for j in range(len(address_table)):
            time_to_cross.append(int(sg.PopupGetText(approach_names[j] + " time to cross: ")))

        cont_processing(noise_threshold, int(scan_time_in), int(scan_error_in))
        match_movements(total_start_time, total_end_time, out_folder, out_file_name, int(scan_time_in))
        window.Element('_CONSOLE_').Update(window.Element('_CONSOLE_').Get() + "----PROCESSING COMPLETE----")
