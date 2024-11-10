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
import utils.file_utils as utils  # Убедитесь, что этот модуль определен
from yarl import URL
from dotenv import load_dotenv
import os
from routes.home import index

load_dotenv()

pd.set_option('display.max_rows', 1000,
              'display.max_columns', 1000,
              'display.width', 1000,
              'display.max_colwidth', 1000)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / 'configs'
OUTPUT_FILES_DIR = BASE_DIR / 'leftovers' / 'output_files'
OUTPUT_FILES_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("uvicorn")


# получение пользовательской сессии на сайте путем аутентификации
async def venera_auth(config_file):
    secrets = utils.load_config(config_file)
    session = aiohttp.ClientSession()
    user = fake_useragent.UserAgent().random
    headers = {'user-agent': user}

    # Шаг 1: Выполняем GET-запрос для получения CSRF-токена
    async with session.get(secrets['auth_link'], headers=headers) as response:
        html = await response.text()
        # Извлекаем CSRF-токен из HTML
        soup = BeautifulSoup(html, 'html.parser')
        csrf_token = soup.find('input', {'name': '_csrf_token'})['value']
        logger.debug(f"CSRF token: {csrf_token}")

    # Шаг 2: Выполняем POST-запрос для авторизации, включая CSRF-токен
    data = {
        '_username': os.getenv("VENERA_LOGIN"),
        '_password': os.getenv("VENERA_PASSWORD"),
        '_csrf_token': csrf_token
    }

    async with session.post(secrets['auth_link'], data=data, headers=headers) as response:
        # Выводим статус ответа и текст ответа для отладки
        logger.info(f"Response status of authentication: {response.status}")  # Вывод статуса
        logger.debug(f"Response text: {await response.text()}")  # Вывод текста ответа

    return session  # Возвращаем сессию и ответ для проверки


async def set_warehouses_filters(session, categoryId, warehouses):
    url = "https://venera-carpet.ru/category/all-ajax.html"
    params = {
        'fSt': 'filter',
        'categoryId': f'{categoryId}',
        'word': '',
        'warehouses[]': warehouses
    }
    logger.info(URL(url).with_query(params))
    async with session.get(url, params=params) as response:
        if response.status == 200:
            text = await response.text()
            logger.info(f"Фильтры применены. Ответ сервера: {response.status}")
        else:
            logger.info(f"Ошибка применения фильтров: {response.status}")


async def fetch_table_page(session, url):
    logger.debug(f'Куки перед запросом на таблицу: {session.cookie_jar.filter_cookies(url)}')
    async with session.get(url) as response:
        if response.status == 200:
            html = await response.text()
            logger.debug(f"Страница таблицы загружена: {response.url}")
            return html
        else:
            logger.error(f"Ошибка загрузки таблицы: {response.status}")
            return None


async def get_table_df_and_collection_name(session, collection_url, warehouses):
    # 1. Применяем фильтры
    logger.debug(f'Куки перед фильтром: {session.cookie_jar.filter_cookies("https://venera-carpet.ru")}')
    collection_id = collection_url.replace(utils.load_config(CONFIG_DIR / 'secrets.yaml')['venera_leftovers_link'], '').replace('.html', '').split('_')[-1]
    logger.debug(f'{collection_id}')
    await set_warehouses_filters(session,collection_id, warehouses)
    # 2. Загружаем таблицу
    html = await fetch_table_page(session, collection_url)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        collection_name = get_size_grid_collection_name(soup)
        table = soup.find('table')
        if table:
            logger.debug("Таблица найдена!")
            if table is None:
                return None
                # raise ValueError("No tables found")
            table_str = str(table)
            tables = pd.read_html(StringIO(table_str))
            df = tables[0]
            logger.debug(f'size_grid_table:\n {df} \n {collection_name}')
            if len(df) < 3:
                logger.warning(f"There are no carpets in the collection table: {collection_url} ")
                return None
            return df, collection_name
        else:
            logger.warning(f"Table not found for collection: {collection_url}")
    else:
        logger.error(f"Failed to load table page for collection: {collection_url}")


# получение странички сетки размеров
async def get_size_grid_page(url, session):
    async with session.get(url) as response:
        content = await response.text()
    soup = BeautifulSoup(content, 'lxml')
    logger.debug(f'size grid page: {soup}')
    return soup


def get_size_grid_collection_name(soup):
    collection_name = soup.find_all('h1')[0].text
    return collection_name


def insert_name_of_collection_column(df, collection_name):
    df.insert(0, 'Коллекция', collection_name[:2])
    return df


# извлечение таблицы из странички сетки размеров
def get_size_grid_table(soup):
    table = soup.find('table')
    if table is None:
        raise ValueError("No tables found")
    table_str = str(table)
    tables = pd.read_html(StringIO(table_str))
    df = tables[0]
    logger.debug(f'size_grid_table: {df}')
    return df


# функция для первичного форматирования таблицы с сайта
def size_grid_table_formatting(df):
    df = df.drop(columns=['Фото'])
    df = df.iloc[:-1]  # Оставляем все строки, кроме последней
    df = df.fillna(0)
    cols_after_forma = df.columns[df.columns.get_loc('Форма') + 1:]  # Все колонки после "Форма"
    df[cols_after_forma] = df[cols_after_forma].replace(r'\s.*', '', regex=True)  # Заменяем содержимое после первого пробела
    logger.debug(f'formated_size_grid_table: {df}')
    return df

# функция умножения содержимого в ячейках в зависимости от названия столбца
def multiply_packaging_columns(df):
    pattern = re.compile(r'уп\. (\d+) шт\.')

    # Проходим по каждому столбцу
    for column in df.columns:
        match = pattern.search(column)

        # Проверяем, подходит ли столбец под шаблон и получаем множитель
        if match:
            factor = int(match.group(1))

            # Преобразуем данные в столбце в числовой формат, заменяя нечисловые значения на NaN
            df[column] = pd.to_numeric(df[column], errors='coerce').fillna(0)

            # Применяем умножение
            df[column] = df[column] * factor

    return df


# функция сложения содержимого двух столбцов с одинаковыми названиями
def merge_duplicate_sizes(df):
    columns_to_check = df.columns[3:]
    size_dict = {}

    for col in columns_to_check:
        base_col = col.split(' уп. ')[0]
        if base_col in size_dict:
            size_dict[base_col].append(col)
        else:
            size_dict[base_col] = [col]

    for base_col, cols in size_dict.items():
        if len(cols) > 1:
            # Преобразуем данные в числовой формат
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            df[base_col] = df[cols].sum(axis=1)
        else:
            df[cols[0]] = pd.to_numeric(df[cols[0]], errors='coerce').fillna(0).astype(int)
            df[base_col] = df[cols[0]]

    df = df[[col for col in df.columns if ' уп. ' not in col]]

    return df


# функция для удаления последней буквы в штрихкоде
def remove_after_last_digit(s):
    pattern = r'^(.*)[a-zA-Z]$'
    match = re.match(pattern, s)
    if match:
        return match.group(1)
    else:
        return s


# функция для замены некоторых проблемных рисунков в коллекциях
def replace_values(df, column, replacements):
    df[column] = df[column].replace(replacements)
    return df


# функция для изменения названия формы в вид который используется в штрихкоде (Прямоугольник -> ST)
def transform_form_to_barcode_form(carpet_form):
    with open(CONFIG_DIR / 'users_configs' / 'carpet_properties.yaml', 'r') as file:
        carpet_properties = yaml.safe_load(file)
    carpet_forms = carpet_properties['Форма']
    if carpet_form in carpet_forms:
        carpet_form = carpet_forms[carpet_form]['barcode_form']
    return carpet_form
# df_melted['Форма'] = list(map(lambda x: transform_form_to_barcode_form(x), df_melted['Форма']))


def transform_size(size):
    size_parts = size.split('x')

    # Обработка ширины
    width_parts = size_parts[0].split('.')
    width = width_parts[0]  # целая часть ширины
    if len(width_parts) > 1:
        # обрабатываем дробную часть, если она есть
        width += width_parts[1].replace('00', '0').replace('0', '')
    else:
        width += '0'  # добавляем '0' если дробной части нет

    # Обработка высоты
    height_parts = size_parts[1].split('.')
    height = height_parts[0]  # целая часть высоты
    if len(height_parts) > 1:
        # обрабатываем дробную часть, если она есть
        height += height_parts[1].replace('00', '0').replace('0', '')
    else:
        height += '0'  # добавляем '0' если дробной части нет

    # Обработка случая, когда дробная часть равна '00'
    if len(width_parts) > 1 and width_parts[1] == '00':
        width += '0'
    if len(height_parts) > 1 and height_parts[1] == '00':
        height += '0'

    transformed_size = width + height
    return transformed_size


def replace_pattern(df):
    pattern_replacements = utils.load_config(CONFIG_DIR / 'users_configs' / 'pattern_replacements.yaml')['patterns']
    df = replace_values(df, 'Рис', pattern_replacements)
    return df


def transform_color(color):
    try:
        color = color.replace(' / ', ',')
        color = color.replace(' ', '-')
    except AttributeError:
        return color
    return color


def transform_quantity_with_limits(df, collection_name):
    try:
        # Чтение файла и загрузка лимитов
        with open(CONFIG_DIR / 'users_configs' / 'collections_limits.yaml', 'r') as file:
            collections_limits = yaml.safe_load(file)['collection']

        # Извлекаем лимиты для данной коллекции
        collection_limits = collections_limits.get(collection_name, {})

        # Проверка, что лимиты для коллекции существуют
        if not collection_limits:
            logger.info(f"No limits found for collection: {collection_name}")
            return df  # Если лимитов нет, возвращаем исходный DataFrame без изменений

        # Применение лимитов для категории "very_small" (размер <= 8)
        if 'very_small' in collection_limits:
            limit = collection_limits['very_small']
            mask_very_small = df['Размер'].str[:2].astype(int) <= 8
            df.loc[mask_very_small, 'кол-во'] -= limit

        # Применение лимитов для категории "small" (8 < размер <= 12)
        if 'small' in collection_limits:
            limit = collection_limits['small']
            mask_small = (df['Размер'].str[:2].astype(int) > 8) & (df['Размер'].str[:2].astype(int) <= 12)
            df.loc[mask_small, 'кол-во'] -= limit

        # Обрезаем значения в колонке 'кол-во', чтобы избежать отрицательных значений
        df['кол-во'] = df['кол-во'].clip(lower=0)

    except Exception as e:
        logger.error(f"Error reading configuration file: {e}")

    return df  # Возвращаем измененный DataFrame


def transform_quantity_with_wight(df, mask, limit):
    df.loc[mask, 'кол-во'] -= limit
    df['кол-во'] = df['кол-во'].clip(lower=0)
    return df


def subtract_one_from_column(df, column_name):
    # Преобразуем колонку в числовой тип, неудачные преобразования заменяем на NaN
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    # Заменяем NaN на 0 или любое другое значение по умолчанию
    df[column_name] = df[column_name].fillna(0)
    # Вычитаем 1 из колонки
    df[column_name] = df[column_name] - 1
    return df


#  NEW
def split_columns_pattern_and_color(df):
    df[['Рис', 'Цвет']] = df['Рис. Цвет'].str.split(' ', n=1, expand=True)
    df = df.drop(columns=['Рис. Цвет'])
    df.insert(0, 'Рис', df.pop('Рис'))  # Вставляем 'Рис' в начало
    df.insert(1, 'Цвет', df.pop('Цвет'))  # Вставляем 'Цвет' после 'Рис'
    return df


async def parce_collection(url, session):
    size_grid_soup = await get_size_grid_page(url, session)
    df_original = get_size_grid_table(size_grid_soup)
    df_original = split_columns_pattern_and_color(df_original)
    return df_original


def remove_blacklisted_barcodes(df):
    blacklist = utils.load_config(CONFIG_DIR / 'users_configs' / 'barcode_blacklist.yaml')
    barcodes = blacklist.get('barcodes', [])
    if not barcodes:
        return df
    df_filtered = df[~df['carpet'].isin(barcodes)]
    return df_filtered


async def transform_size_grid_table_to_barcode_quantity_table(session, collection_url, warehouses):
    try:
        collection_name_url = collection_url.replace(utils.load_config(CONFIG_DIR / 'secrets.yaml')['venera_leftovers_link'], '').replace('.html', '')
        df, collection_name = await get_table_df_and_collection_name(session, collection_url, warehouses)
        # Таблица с остатками до форматирования
        df = split_columns_pattern_and_color(df)
        # Разделение колонки Рис. Цвет на Рис и Цвет
        df = size_grid_table_formatting(df)
        # Удаленна колонка Фото, Удалена последняя строчка с размерами, Все ячейки с NaN заменены на 0, Все ячейки очищены от "В корзине Ошибка"
        logger.info(f'df of collection: {collection_url}\n{df}')
        df = multiply_packaging_columns(df)
        # Умножение содержимого в колонках в зависимости от названия колонки
        df = merge_duplicate_sizes(df)
        # Данная функция объединяет одинаковые размеры
        df['Форма'] = list(map(lambda x: transform_form_to_barcode_form(x), df['Форма']))
        # Изменение названий в колонке Форма на те которые используются в штрихкоде
        df = df.melt(id_vars=['Рис', 'Цвет', 'Форма'], var_name='Размер', value_name='кол-во')
        # Формирование таблицы из |Рис|Цвет|Форма|0.8x1.5|...|4x5| в |Рис|Цвет|Форма|Размер|кол-во|
        df['Размер'] = list(map(lambda x: transform_size(x), df['Размер']))
        # Изменение содержимого колонки Размер на то что используются в штрихкоде
        df = replace_pattern(df)
        # Изменение содержимого колонки Рис на правильные рисунки которые используются в штрихкоде
        df['Рис'] = list(map(lambda x: remove_after_last_digit(x), df['Рис']))
        # Удаление последней буквы в рисунке
        df['Цвет'] = list(map(lambda x: transform_color(x), df['Цвет']))
        # Форматирование цвета для штрихкода
        df = insert_name_of_collection_column(df,collection_name)
        # Вставка колонки с названием коллекции
        df = subtract_one_from_column(df, 'кол-во')
        # Вычитание из колонки кол-во 1 ковер
        df = transform_quantity_with_limits(df, collection_name_url)
        # Чтение и вычитание из колонки кол-во лимитов на ковры определенных коллекций прописанных в файле
        df = transform_quantity_with_wight(df, (df['Размер'].str[:2].astype(int) <= 8), 1)
        # Вычитание из колонки кол-во 1 ковер так как он очень маленький
        df = transform_quantity_with_wight(df,  (df['Размер'].str[:2].astype(int) > 8) & (df['Размер'].str[:2].astype(int) <= 12), 1)
        # Вычитание из колонки кол-во 1 ковер так как он маленький
        df['barcode'] = df.apply(lambda row: f'{row["Рис"]}-{row["Форма"]}-{row["Размер"]}-{row["Коллекция"]}-{row["Цвет"]}', axis=1)
        # Генерация штрихкода на основе |Коллекция|Рис|Форма|Цвет|Размер|
        df = df.drop(columns=['Коллекция', 'Рис', 'Форма', 'Цвет', 'Размер'])
        # Удаление колонок |Коллекция|Рис|Форма|Цвет|Размер|
        df = df[['barcode', 'кол-во']]
        # Поменяли местами колонки barcode и кол-во
        logger.info(f'Processed DONE for collection: {collection_url}')
        return df
    except Exception as e:
        logger.error(f'Error processing for collection: {collection_url} | Error: {str(e)}')
        return None  # Возвращаем None в случае ошибки


async def main(urls, warehouses):
    session = await venera_auth(CONFIG_DIR / 'secrets.yaml')
    combined_df_list = []
    try:
        # Создаем задачи для каждой коллекции
        tasks = [transform_size_grid_table_to_barcode_quantity_table(session, url, warehouses) for url in urls]
        results = await asyncio.gather(*tasks)  # Ожидаем все задачи

        # Добавляем только успешные результаты в combined_df_list
        for result in results:
            if result is not None:
                combined_df_list.append(result)
    finally:
        await session.close()
    return combined_df_list


def combine_dataframes(df_list):
    combined_df = pd.concat(df_list, ignore_index=True)
    combined_df = combined_df.set_axis(['carpet', 'count'], axis=1)
    combined_df = remove_blacklisted_barcodes(combined_df)
    logger.info(f'The exported file contains {len(combined_df)} lines')
    return combined_df


def run_generation(warehouse_name, warehouses):
    utils.clear_folder(OUTPUT_FILES_DIR)
    collections = utils.load_config(CONFIG_DIR / 'users_configs' / 'collections.yaml')['collections']
    base_url = utils.load_config(CONFIG_DIR / 'secrets.yaml')['venera_leftovers_link']
    collection_links = [f'{base_url}{collection}.html' for collection in collections]
    combined_df_list = asyncio.run(main(collection_links,warehouses))
    combine_dataframes(combined_df_list).to_csv(OUTPUT_FILES_DIR / f'{warehouse_name}_leftovers.csv', index=False, sep=';')

