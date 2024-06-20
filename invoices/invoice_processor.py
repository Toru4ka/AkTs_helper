import pandas as pd
import re
from pathlib import Path
from leftovers.leftovers_async import remove_after_last_digit
from leftovers.leftovers_async import transform_color

pd.set_option('display.max_rows', 1000,
              'display.max_columns', 1000,
              'display.width', 1000,
              'display.max_colwidth', 1000)

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILES_DIR = BASE_DIR / 'invoices' / 'output_files'


def split_string(df, col):
    split_lambda = lambda s: list(re.match(r'([^<]+)<([^>]+)>\s*\(([^)]+)\)', s).groups()) if re.match(
        r'([^<]+)<([^>]+)>\s*\(([^)]+)\)', s) else [None, None, None]
    df[col] = df[col].apply(split_lambda)
    trim_first_element = lambda arr: [arr[0][:2]] + arr[1:] if arr[0] else arr
    df[col] = df[col].apply(trim_first_element)
    return df


# Применение функции к вторым элементам массивов
def remove_second_element(arr):
    if len(arr) > 1:
        arr.pop(1)
    return arr


def trim_carpets_forms(form):
    form = form[:2]
    if form == 'DA':
        form = 'KG'
    return form


def update_nomenclature(row):
    nomenclature = row['Номенклатура']
    width_length = f"{str(row['Ширина']).replace('.', '')}{str(row['Длина']).replace('.', '')}"
    nomenclature[2] = width_length
    return nomenclature


def create_akts_barcode(arr):
    barcode = f'{arr[1]}-{arr[3]}-{arr[2]}-{arr[0]}-{arr[4]}'
    return barcode


def get_invoice_table(input_path):
    df = pd.read_excel(input_path, skiprows=6)
    df.drop(columns=[col for col in df.columns if col.startswith('Unnamed:')], inplace=True)
    df.dropna(subset=['Ширина'], inplace=True)
    df['Штрихкод'] = df['Штрихкод'].astype(int)
    df = split_string(df, 'Номенклатура')
    df['Номенклатура'] = df['Номенклатура'].apply(remove_second_element)
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: ', '.join(x))
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: x.split(', '))
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: [x[0], remove_after_last_digit(x[1])] + x[2:])
    df['Номенклатура'] = df.apply(update_nomenclature, axis=1)
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: x[:-2] + [trim_carpets_forms(x[-2])] + [x[-1]])
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: x[:-1] + [transform_color(x[-1])])
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: create_akts_barcode(x))
    print(df)


get_invoice_table(OUTPUT_FILES_DIR / 'unreconstructed_invoice.xlsx')
