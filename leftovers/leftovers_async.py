import pandas as pd
import aiohttp
import asyncio
import yaml
from io import StringIO
from pathlib import Path
from bs4 import BeautifulSoup
import re
import fake_useragent
import logging
import colorlog
from utils.file_utils import clear_folder

pd.set_option('display.max_rows', 1000,
              'display.max_columns', 1000,
              'display.width', 1000,
              'display.max_colwidth', 1000)

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / 'configs'
OUTPUT_FILES_DIR = BASE_DIR / 'leftovers' / 'output_files'
OUTPUT_FILES_DIR.mkdir(exist_ok=True)

# Настройка логирования с colorlog
log_colors_config = {
    'DEBUG': 'white',
    'INFO': 'white',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}
formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    log_colors=log_colors_config
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logging.basicConfig(level=logging.INFO, handlers=[console_handler])
logger = logging.getLogger(__name__)

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

async def venera_auth(config_file):
    secrets = load_config(config_file)
    session = aiohttp.ClientSession()
    user = fake_useragent.UserAgent().random
    headers = {'user-agent': user}
    data = {
        'auth[email]': secrets['login'],
        'auth[password]': secrets['password']
    }
    async with session.post(secrets['auth_link'], data=data, headers=headers) as response:
        await response.text()
    return session

def clean_cell(cell):
    if pd.isna(cell) or cell == '':
        return 0
    elif isinstance(cell, str):
        return cell.split('  / В корзину')[0]
    return cell

async def get_size_grid_page(url, session):
    async with session.get(url) as response:
        content = await response.text()
    soup = BeautifulSoup(content, 'lxml')
    return soup

def get_size_grid_table(soup):
    table = soup.find('table')
    if table is None:
        raise ValueError("No tables found")
    table_str = str(table)
    tables = pd.read_html(StringIO(table_str))
    df = tables[0]
    print(df)
    df_cleaned = df.map(clean_cell)
    for column in df_cleaned.columns[3:]:
        try:
            df_cleaned[column] = pd.to_numeric(df_cleaned[column])
        except ValueError:
            pass
    if 'Unnamed: 0' in df_cleaned.columns:
        df_cleaned = df_cleaned.drop(columns=['Unnamed: 0'])
    print(df_cleaned)
    return df_cleaned

def multiply_packaging_columns(df):
    pattern = re.compile(r'упаковка по (\d+) шт\.')
    for column in df.columns:
        match = pattern.search(column)
        if match:
            factor = int(match.group(1))
            df[column] = df[column].apply(lambda x: x * factor if pd.notna(x) else x)
    return df

def merge_duplicate_sizes(df):
    columns_to_check = df.columns[3:]
    size_dict = {}

    for col in columns_to_check:
        base_col = col.split(' упаковка по')[0]
        if base_col in size_dict:
            size_dict[base_col].append(col)
        else:
            size_dict[base_col] = [col]

    for base_col, cols in size_dict.items():
        if len(cols) > 1:
            df[base_col] = df[cols].sum(axis=1)
        else:
            df[base_col] = df[cols[0]]

    df = df[[col for col in df.columns if 'упаковка по' not in col]]

    return df

def remove_samples(df):
    df['Рис.'] = df['Рис.'].astype(str)
    df['Форма'] = df['Форма'].astype(str)
    return df[~df['Рис.'].str.contains('Образец', na=False) & ~df['Форма'].str.contains('образец', na=False)]

def remove_after_last_digit(s):
    pattern = r'^(.*)[a-zA-Z]$'
    match = re.match(pattern, s)
    if match:
        return match.group(1)
    else:
        return s

def replace_values(df, column, replacements):
    df[column] = df[column].replace(replacements)
    return df

def transform_form_to_barcode_form(carpet_form):
    with open(CONFIG_DIR / 'users_configs' / 'carpet_properties.yaml', 'r') as file:
        carpet_properties = yaml.safe_load(file)
    carpet_forms = carpet_properties['Форма']
    if carpet_form in carpet_forms:
        carpet_form = carpet_forms[carpet_form]['barcode_form']
    return carpet_form

def transform_size(size):
    size_parts = size.split('x')
    width_parts = size_parts[0].split('.')
    width = width_parts[0] + width_parts[1].replace('00', '0').replace('0', '')
    height_parts = size_parts[1].split('.')
    height = height_parts[0] + height_parts[1].replace('00', '0').replace('0', '')
    if width_parts[1] == '00':
        width += '0'
    if height_parts[1] == '00':
        height += '0'
    transformed_size = width + height
    return transformed_size

def get_size_grid_collection_name(soup):
    collection_name = soup.find_all('span', itemprop="name")[-1].text
    return collection_name

def transform_color(s):
    try:
        s = s.replace(' / ', ',')
        s = s.replace(' ', '-')
    except AttributeError:
        return s
    return s

def insert_name_of_collection_column(df, collection_name):
    df.insert(0, 'Коллекция', collection_name[:2])
    return df

def transform_quantity_with_wight(df, mask, limit):
    df.loc[mask, 'кол-во'] -= limit
    df['кол-во'] = df['кол-во'].clip(lower=0)
    return df

def transform_quantity_with_limits(df, collection_name):
    try:
        with open(CONFIG_DIR / 'users_configs' / 'collections_limits.yaml', 'r') as file:
            collections_limits = yaml.safe_load(file)['collection']
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        return df

    if collection_name in collections_limits:
        collection_limit = collections_limits[collection_name]
        size_first_two_digits = df['Размер'].str[:2].astype(int)

        if 'very_small' in collection_limit:
            very_small_limit = collection_limit['very_small']
            very_small_mask = size_first_two_digits <= 8
            df.loc[very_small_mask, 'кол-во'] -= very_small_limit

        if 'small' in collection_limit:
            small_limit = collection_limit['small']
            small_mask = (size_first_two_digits > 8) & (size_first_two_digits <= 12)
            df.loc[small_mask, 'кол-во'] -= small_limit

        df['кол-во'] = df['кол-во'].clip(lower=0)
    return df

def subtract_one_from_column(df, column_name):
    df[column_name] = df[column_name] - 1
    return df

def create_barcode(df, collection, collection_url):
    collection_name = collection_url.replace(load_config(CONFIG_DIR / 'secrets.yaml')['venera_leftovers_link'], '').replace('.html', '')
    pattern_replacements = load_config(CONFIG_DIR / 'users_configs' / 'pattern_replacements.yaml')['patterns']
    df_melted = df.melt(id_vars=['Рис.', 'Форма', 'Цвет'], var_name='Размер', value_name='кол-во')
    df_melted['Форма'] = list(map(lambda x: transform_form_to_barcode_form(x), df_melted['Форма']))
    df_melted['Размер'] = list(map(lambda x: transform_size(x), df_melted['Размер']))
    df_melted = replace_values(df_melted, 'Рис.', pattern_replacements)
    df_melted['Рис.'] = list(map(lambda x: remove_after_last_digit(x), df_melted['Рис.']))
    df_melted['Цвет'] = list(map(lambda x: transform_color(x), df_melted['Цвет']))
    df_melted = insert_name_of_collection_column(df_melted, collection)
    df_melted = subtract_one_from_column(df_melted, 'кол-во')
    df_melted = transform_quantity_with_limits(df_melted, collection_name)
    df_melted = transform_quantity_with_wight(df_melted, (df_melted['Размер'].str[:2].astype(int) <= 8), 1)
    df_melted = transform_quantity_with_wight(df_melted, (df_melted['Размер'].str[:2].astype(int) > 8) & (df_melted['Размер'].str[:2].astype(int) <= 12), 1)
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

async def process_collection(url_size_grid_page, session, combined_df_list):
    try:
        size_grid_soup = await get_size_grid_page(url_size_grid_page, session)
        collection_name = get_size_grid_collection_name(size_grid_soup)
        df_size_grid_page = get_size_grid_table(size_grid_soup)
        df_size_grid_page = multiply_packaging_columns(df_size_grid_page)
        df_size_grid_page = merge_duplicate_sizes(df_size_grid_page)
        df_size_grid_page = remove_samples(df_size_grid_page)
        df_size_grid_page = create_barcode(df_size_grid_page, collection_name, url_size_grid_page)
        combined_df_list.append(df_size_grid_page)
        logger.info(f'Processed {collection_name}')
    except Exception as e:
        logger.error(f'Error processing collection {url_size_grid_page}: {str(e)}')

async def main(urls):
    session = await venera_auth(CONFIG_DIR / 'secrets.yaml')
    combined_df_list = []
    try:
        tasks = [process_collection(url, session, combined_df_list) for url in urls]
        await asyncio.gather(*tasks)
    finally:
        await session.close()
    return combined_df_list

def remove_blacklisted_barcodes(df):
    blacklist = load_config(CONFIG_DIR / 'users_configs' / 'barcode_blacklist.yaml')
    barcodes = blacklist.get('barcodes', [])
    if not barcodes:
        return df
    df_filtered = df[~df['carpet'].isin(barcodes)]
    return df_filtered

def combine_dataframes(df_list):
    combined_df = pd.concat(df_list, ignore_index=True)
    combined_df = combined_df.set_axis(['carpet', 'count'], axis=1)
    combined_df = remove_blacklisted_barcodes(combined_df)
    combined_df.to_csv(OUTPUT_FILES_DIR / 'leftovers.csv', index=False, sep=';')

def run_generation():
    clear_folder(OUTPUT_FILES_DIR)
    collections = load_config(CONFIG_DIR / 'users_configs' / 'collections.yaml')['collections']
    base_url = load_config(CONFIG_DIR / 'secrets.yaml')['venera_leftovers_link']
    collection_links = [f'{base_url}{collection}.html' for collection in collections]
    combined_df_list = asyncio.run(main(collection_links))
    combine_dataframes(combined_df_list)
