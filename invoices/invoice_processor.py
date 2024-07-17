import pandas as pd
import re
from pathlib import Path
import shutil
from zipfile import ZipFile
from leftovers.leftovers_async import remove_after_last_digit
from leftovers.leftovers_async import transform_color
from leftovers.leftovers_async import load_config

pd.set_option('display.max_rows', 1000,
              'display.max_columns', 1000,
              'display.width', 1000,
              'display.max_colwidth', 1000)

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILES_DIR = BASE_DIR / 'invoices' / 'output_files'
INPUT_FILES_DIR = BASE_DIR / 'invoices' / 'input_files'
CONFIG_DIR = BASE_DIR / 'configs'

def fix_and_resave_excel(input_path):
    # Создаем временную папку
    tmp_folder = Path('temp_folder')
    tmp_folder.mkdir(exist_ok=True)
    try:
        # Распаковываем excel как zip в нашу временную папку
        with ZipFile(input_path, 'r') as excel_container:
            excel_container.extractall(tmp_folder)

        # Путь к файлу с неверным названием
        wrong_file_path = tmp_folder / 'xl' / 'SharedStrings.xml'
        correct_file_path = tmp_folder / 'xl' / 'sharedStrings.xml'

        # Проверка существования файла и его переименование
        if wrong_file_path.exists():
            wrong_file_path.rename(correct_file_path)

        # Запаковываем excel обратно в zip
        output_zip_path = tmp_folder.parent / 'tempfile.zip'
        shutil.make_archive(output_zip_path.stem, 'zip', tmp_folder)

        # Переименовываем обратно в исходный файл
        output_zip_path.with_suffix('.zip').rename(input_path)

        print(f"Файл успешно пересохранен как {input_path}.")
    except Exception as e:
        print(f"Ошибка при пересохранении файла: {e}")
    finally:
        # Удаляем временную папку
        shutil.rmtree(tmp_folder)


def read_excel_with_fix(input_path, **kwargs):
    input_path = Path(input_path)
    try:
        # Попытка чтения файла с использованием pandas
        df = pd.read_excel(input_path, skiprows=kwargs['skiprows'])
        print("Файл успешно прочитан с использованием pandas.")
        return df
    except KeyError as e:
        # Проверяем текст ошибки
        if "There is no item named 'xl/sharedStrings.xml' in the archive" in str(e):
            print("Обнаружена ошибка KeyError. Попытка пересохранить файл...")
            fix_and_resave_excel(input_path)
            try:
                # Повторная попытка чтения пересохраненного файла
                df = pd.read_excel(input_path, skiprows=kwargs['skiprows'])
                print("Файл успешно прочитан с использованием pandas после пересохранения.")
                return df
            except Exception as read_error:
                print(f"Ошибка при чтении пересохраненного файла: {read_error}")
                return None
        else:
            print(f"Обнаружена ошибка KeyError: {e}")
            return None
    except Exception as e:
        print(f"Обнаружена ошибка при чтении файла: {e}")
        return None


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


def deleting_packaging_count_value(row):
    nomenclature = row['Номенклатура']
    quantity = row['Количество, шт']

    # Поиск и обработка строки [упак/x]
    new_nomenclature = []
    for item in nomenclature:
        match = re.search(r'\[упак/(\d+)\]', item)
        if match:
            multiplier = int(match.group(1))
            row['Количество, шт'] = quantity * multiplier
            item = re.sub(r'\s*\[упак/\d+\]', '', item)
        new_nomenclature.append(item)

    row['Номенклатура'] = new_nomenclature
    return row

def calculate_price(row):
    row['Цена'] = row['Сумма'] / row['Количество, шт']
    return row


def replace_pattern(nomenclature, patterns):
    return [patterns.get(item, item) for item in nomenclature]


def process_file(input_path, output_path):
    df = read_excel_with_fix(input_path, skiprows=6)
    df.drop(columns=[col for col in df.columns if col.startswith('Unnamed:')], inplace=True)
    df.dropna(subset=['Ширина'], inplace=True)
    df['Штрихкод'] = df['Штрихкод'].astype(pd.Int64Dtype())
    df = split_string(df, 'Номенклатура')
    df['Номенклатура'] = df['Номенклатура'].apply(remove_second_element)
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: ', '.join(x))
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: x.split(', '))
    patterns = load_config(CONFIG_DIR / 'pattern_replacements.yaml')['patterns']
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: replace_pattern(x, patterns))
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: [x[0], remove_after_last_digit(x[1])] + x[2:])
    df['Номенклатура'] = df.apply(update_nomenclature, axis=1)
    df = df.apply(deleting_packaging_count_value, axis=1)
    df = df.apply(calculate_price, axis=1)
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: x[:-2] + [trim_carpets_forms(x[-2])] + [x[-1]])
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: x[:-1] + [transform_color(x[-1])])
    df['Номенклатура'] = df['Номенклатура'].apply(lambda x: create_akts_barcode(x))
    df.to_excel(output_path, index=False)


