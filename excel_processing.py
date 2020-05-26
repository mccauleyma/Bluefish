import xlsxwriter as xlw
import pandas as pd

""" create_excel_from_csv(input_file_path, output_path, output_name)
input_file_path = full input file path (including extension)
output_path = output folder path
output_name = output file name (without extension)
Given a csv file location, will create an Excel file at the desired output location."""


def create_excel_from_csv(input_file_path, output_path, output_name):
    file = pd.read_csv(input_file_path)
    writer = pd.ExcelWriter(output_path + output_name + '.xlsx', engine='xlsxwriter')
    file.to_excel(writer, sheet_name='Data')
    writer.save()
    # TODO: May have to remove column/realign something
    return output_path + output_name + '.xlsx', len(file.values), len(file.values[0])


""" create_excel_from_df(df, output_path, output_name)
df = DataFrame containing the data
output_path = output folder path
output_name = output file name (without extension)
Given a DataFrame, will create an Excel file at the desired output location."""


def create_excel_from_df(df, output_path, output_name):
    writer = pd.ExcelWriter(output_path + output_name + '.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Data')
    writer.save()
    # TODO: May have to remove column/realign something
    return output_path + output_name + '.xlsx', len(df.values), len(df.values[0])


def format_excel(file_path):
    workbook = xlw.Workbook(file_path)
    worksheet = workbook.get_worksheet_by_name('Data')

    worksheet.freeze_panes(1, 0)

