import pandas as pd
import numpy as np
import time
from time import mktime
import PySimpleGUI as sg
import os

temp_log = ""


def get_csv(file):
    global df

    # import_file_path = filedialog.askopenfilename()
    import_file_path = file

    os.rename(import_file_path, import_file_path[0:-3] + "csv")
    df = pd.read_csv(import_file_path[0:-3] + "csv", sep='\s*,\s*', engine='python')
    df = pd.read_csv(import_file_path, sep='\s*,\s*', engine='python')

    df['Address'] = df['Timestamp']
    df['Timestamp'] = df.index

    print(df)
    dataFiles.append(df)


def remove_values_from_list(the_list, val):
    return [value for value in the_list if value is not val]


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


def setup_address_table():
    out = []
    for i in range(len(dataFiles)):
        out.append([])

    return out


def process_file(index, offset_time):
    time_offset = mktime(time.strptime(offset_time, '%m%d%Y %H:%M:%S')) * 1000
    time_offsets.append(time_offset)
    dataFiles[index]['Timestamp'] = dataFiles[index]['Timestamp'].add(time_offset)

    unique_addresses = dataFiles[index]['Address'].unique()

    for i in range(len(unique_addresses)):
        address_table[index].append(dataFiles[index].loc[dataFiles[index]['Address'] == unique_addresses[i]])

    global temp_log
    temp_log = temp_log + "Found " + str(len(unique_addresses)) + " unique addresses in approach " + str(index + 1)


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
    #        if address_table[i][ii].index.size == 1 and math.isnan(address_table[i][ii]['Time_Dif'].iloc[0]):
    #            address_table[i][ii] = 0
    #            white_noise_count += 1

        address_table[i] = remove_values_from_list(address_table[i], 0)

        global temp_log
        temp_log = temp_log + "Removed " + str(white_noise_count) + " white-noise addresses from approach " + str(i + 1)


def check_inner_loop(out_i, out_ii, address, interval, time_range):
    for in_ii in range(out_i + 1, out_i + int((time_range * 1000) / interval)):
        for in_i in range(1, len(approach_names) + 1):
            if in_ii < len(matching_table['Time']):
                if address in matching_table.iat[in_ii, in_i]:
                    # logically this is: (((out_ii - 1) * len(approach_names)) + 1) + (in_i - 1), but the +/- 1 cancel
                    output_table.iat[in_ii, ((out_ii - 1) * len(approach_names)) + in_i] = output_table.iat[in_ii, ((out_ii - 1) * len(approach_names)) + in_i] + 1
                    return


def match_movements(end_time_entry, output_path, output_name, scan_time):
    if len(dataFiles) < 2:
        window.Element('_CONSOLE_').Update(window.Element('_CONSOLE_').Get() +
                                           "Cannot match movements with less than 2 approaches")
        return

    columns = approach_names
    columns.insert(0, 'Time')
    factor = 1000 * scan_time
    end_time = mktime(time.strptime(end_time_entry, '%m%d%Y %H:%M:%S')) * 1000
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

    for i in range(len(matching_table['Time'])):
        for ii in range(1, len(approach_names) + 1):
            cell = matching_table.iat[i, ii]
            if len(cell) > 0:
                for iii in range(len(cell)):
                    address = cell[iii]
                    check_inner_loop(i, ii, address, factor, time_to_cross[ii - 1])

    # output_table.drop(output_table['Time'] < start_time)

    path = output_path + output_name + '.csv'
    output_table.to_csv(path_or_buf=path, index=False)
    print(output_table)


dataFiles = []
address_table = []
time_offsets = []
approach_names = []

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
          # [sg.Text('Start Date'), sg.InputText('MMDDYYYY hh:mm:ss', key='_TOTAL_START_DATE_')],
          [sg.Text('End Date'), sg.InputText('MMDDYYYY hh:mm:ss', key='_TOTAL_END_DATE_')],
          [sg.Text('Output Folder'), sg.FileBrowse(target='_OUT_FOLDER_'),
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

        for index_1 in range(0, len(dataFiles)):
            text_name_in = sg.PopupGetText('Enter a name for the approach in data file ' + str(index_1 + 1),
                                           'Approach Name')
            approach_names.append(text_name_in)
            text_time_in = sg.PopupGetText('Enter a start date and time in MMDDYYYY hh:mm:ss format for ' +
                                           approach_names[index_1])
            process_file(index_1, text_time_in)

        break

noise_threshold = values['_WHITE_NOISE_']
# total_start_time = window.Element('_TOTAL_START_DATE_').Get()
total_end_time = window.Element('_TOTAL_END_DATE_').Get()
out_folder = window.Element('_OUT_FOLDER_').Get()
out_file_name = window.Element('_OUT_FILE_NAME_').Get()
scan_time_in = window.Element('_SCAN_TIME_').Get()
scan_error_in = window.Element('_SCAN_ERROR_').Get()

window.Close()

time_to_cross = []

layout = [[sg.Text('Data Processing')],
          [sg.Multiline('Begin Console Log:', key='_CONSOLE_')],
          [sg.Submit(), sg.CloseButton('Close')]]

window = sg.Window("Bluefish Data Processor", layout)

while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == 'Close':
        break
    if event == 'Submit':
        for i in range(len(address_table)):
            time_to_cross.append(int(sg.PopupGetText(approach_names[i] + " time to cross: ")))

        cont_processing(noise_threshold, int(scan_time_in), int(scan_error_in))
        match_movements(total_end_time, out_folder, out_file_name, int(scan_time_in))
        window.Element('_CONSOLE_').Update(window.Element('_CONSOLE_').Get() + "----PROCESSING COMPLETE----")
