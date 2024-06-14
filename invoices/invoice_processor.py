# Данный скрипт перепиывается для увеличения производительности системы а так же для увеличения скорости модификации и поддрежки
import time
import numpy
import pandas as pd
import re
from datetime import datetime
import os
from pathlib import Path

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


def get_invoice_table(input_path):
    df = pd.read_excel(input_path, skiprows=6)
    df.drop(columns=[col for col in df.columns if col.startswith('Unnamed:')], inplace=True)
    df.dropna(subset=['Ширина'], inplace=True)
    df['Штрихкод'] = df['Штрихкод'].astype(int)
    df = split_string(df, 'Номенклатура')
    # TODO второй элемент массива в Номенклатура мы удаляем
    # TODO для кода цвета применяем регулярку
    # TODO для размера нужно что бы было 0815 (0,8*1,5) и 1020 (1*2)
    # TODO для формы ну стандартно
    # TODO для цвета супер стандартно
    # TODO птомо это все реиндексируем и делаем - между элементами массива и получаем на выходе строку с штрихкодом AkTs
    print(df)


get_invoice_table(OUTPUT_FILES_DIR / 'unreconstructed_invoice.xlsx')
