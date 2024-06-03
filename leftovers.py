import pandas as pd
import requests
import fake_useragent
from bs4 import BeautifulSoup
import yaml
from io import StringIO
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / 'configs'
OUTPUT_FILES_DIR = BASE_DIR / 'leftovers' / 'output_files'
link = 'https://old.venera-carpet.ru/category/grid/armina_972.html'


def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config


def venera_auth(config_file):
    secrets = load_config(config_file)
    session = requests.Session()
    user = fake_useragent.UserAgent().random
    header = {'user-agent': user}
    data = {
        'auth[email]': secrets['login'],
        'auth[password]': secrets['password']
    }
    response = session.post(secrets['auth_link'], data=data, headers=header).text
    return session


def clean_cell(cell):
    if pd.isna(cell) or cell == '':
        return 0
    elif isinstance(cell, str):
        return cell.replace(' / В корзину', '')
    return cell


def get_size_grid_page(url, session):
    r = session.get(url, headers=session.headers)
    soup = BeautifulSoup(r.content, 'lxml')
    return soup


def get_size_grid_table(soup):
    table = soup.find('table')
    table_str = str(table)
    tables = pd.read_html(StringIO(table_str))
    df = tables[0]
    df_cleaned = df.map(clean_cell)
    for column in df_cleaned.columns:
        try:
            df_cleaned[column] = pd.to_numeric(df_cleaned[column])
        except ValueError:
            pass
    if 'Unnamed: 0' in df_cleaned.columns:
        df_cleaned = df_cleaned.drop(columns=['Unnamed: 0'])

    return df_cleaned


def multiply_packaging_columns(df):
    # Регулярное выражение для поиска колонок вида "упаковка по X шт."
    pattern = re.compile(r'упаковка по (\d+) шт\.')
    # Перебор всех колонок DataFrame
    for column in df.columns:
        match = pattern.search(column)
        if match:
            # Извлечение числа X из названия колонки
            factor = int(match.group(1))
            # Умножение содержимого ячеек на X
            df[column] = df[column].apply(lambda x: x * factor if pd.notna(x) else x)
    return df


def merge_duplicate_sizes(df):
    columns_to_check = df.columns[3:]  # Игнорируем первые три колонки
    size_dict = {}

    # Создаем словарь для хранения уникальных размеров и соответствующих колонок
    for col in columns_to_check:
        base_col = col.split(' упаковка по')[0]
        if base_col not in size_dict:
            size_dict[base_col] = []
        size_dict[base_col].append(col)

    # Объединяем колонки с одинаковыми размерами и суммируем их содержимое
    for base_col, cols in size_dict.items():
        if len(cols) > 1:
            df[base_col] = df[cols].sum(axis=1)
        else:
            df[base_col] = df[cols[0]]

    # Удаляем все колонки, которые содержат "упаковка по"
    df = df[[col for col in df.columns if 'упаковка по' not in col]]

    return df


def remove_samples(df):
    df['Рис.'] = df['Рис.'].astype(str)
    df['Форма'] = df['Форма'].astype(str)
    return df[~df['Рис.'].str.contains('Образец', na=False) & ~df['Форма'].str.contains('образец', na=False)]


def remove_after_last_digit(s):
    pattern = r'(.*\d).*?$'
    match = re.match(pattern, s)
    if match:
        return match.group(1)
    else:
        return s


def transform_form_to_barcode_form(carpet_form):
    # чтение файла конфигурации свойств ковров
    with open(CONFIG_DIR / 'carpet_properties.yaml', 'r') as file:
        carpet_properties = yaml.safe_load(file)
    # выбор свойства
    carpet_forms = carpet_properties['Форма']
    # проверка наличия формы ковра
    if carpet_form in carpet_forms:
        carpet_form = carpet_forms[carpet_form]['barcode_form']
    return carpet_form


def transform_size(size):
    size_parts = size.split('x')
    # Обработка ширины
    width_parts = size_parts[0].split('.')
    width = width_parts[0] + width_parts[1].replace('00', '0').replace('0', '')
    # Обработка высоты
    height_parts = size_parts[1].split('.')
    height = height_parts[0] + height_parts[1].replace('00', '0').replace('0', '')
    # Если первая часть после точки пустая, добавляем ноль
    if width_parts[1] == '00':
        width += '0'
    if height_parts[1] == '00':
        height += '0'
    transformed_size = width + height
    return transformed_size


def get_get_size_grid_collection_name(soup):
    collection_name = soup.find_all('span', itemprop="name")[-1].text
    return collection_name


def transform_color(s):
    s = s.replace(' / ', ',')
    s = s.replace(' ', '-')
    return s


def insert_name_of_collection_column(df, collection_name):
    df.insert(0, 'Коллекция', collection_name[:2])
    return df


def create_barcode(df, collection):
    df_melted = df.melt(id_vars=['Рис.', 'Форма', 'Цвет'], var_name='Размер', value_name='кол-во')
    df_melted['Форма'] = list(map(lambda x: transform_form_to_barcode_form(x), df_melted['Форма']))
    df_melted['Размер'] = list(map(lambda x: transform_size(x), df_melted['Размер']))
    df_melted['Рис.'] = list(map(lambda x: remove_after_last_digit(x), df_melted['Рис.']))
    df_melted['Цвет'] = list(map(lambda x: transform_color(x), df_melted['Цвет']))
    df_melted = insert_name_of_collection_column(df_melted, collection)
    df_melted['barcode'] = df_melted.apply(lambda row:
                                           f'{row["Рис."]}-'
                                           f'{row["Форма"]}-'
                                           f'{row["Размер"]}-'
                                           f'{row["Коллекция"]}-'
                                           f'{row["Цвет"]}',
                                           axis=1)
    df_melted = df_melted.drop(columns=['Коллекция', 'Рис.', 'Форма', 'Цвет', 'Размер'])
    df_melted = df_melted[['barcode', 'кол-во']]
    return df_melted


# рис-форма-размер-коллекция-цвет
def main(url_size_grid_page):
    session = venera_auth(CONFIG_DIR / 'secrets.yaml')
    size_grid_soup = get_size_grid_page(url_size_grid_page, session)
    collection_name = get_get_size_grid_collection_name(size_grid_soup)
    df_size_grid_page = get_size_grid_table(size_grid_soup)
    df_size_grid_page = multiply_packaging_columns(df_size_grid_page)
    df_size_grid_page = merge_duplicate_sizes(df_size_grid_page)
    df_size_grid_page = remove_samples(df_size_grid_page)
    df_size_grid_page = create_barcode(df_size_grid_page, collection_name)
    df_size_grid_page.to_csv(OUTPUT_FILES_DIR / 'output_grid_page.xlsx')
    print(df_size_grid_page)


if __name__ == '__main__':
    main(link)
