import pandas as pd
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / 'configs'
OUTPUT_FILES_DIR = BASE_DIR / 'leftovers' / 'output_files'

# Пример ваших данных
data = {
    "Коллекция": ["AL"] * 30,
    "Рис.": ["Q011A", "Q012A", "Q012A", "Q018A", "Q018A", "Q018A", "Q011A", "Q012A", "Q012A", "Q018A", "Q018A", "Q018A", "Q011A", "Q012A", "Q012A", "Q018A", "Q018A", "Q018A", "Q011A", "Q012A", "Q012A", "Q018A", "Q018A", "Q018A", "Q011A", "Q012A", "Q012A", "Q018A", "Q018A", "Q018A"],
    "Форма": ["ST"] * 30,
    "Цвет": ["BROWN-FDY/CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "BROWN-FDY/CREAM-SHRINK", "BEIGE-FDY,CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "GREY-FDY,CREAM-SHRINK", "BROWN-FDY/CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "BROWN-FDY/CREAM-SHRINK", "BEIGE-FDY,CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "GREY-FDY,CREAM-SHRINK", "BROWN-FDY/CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "BROWN-FDY/CREAM-SHRINK", "BEIGE-FDY,CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "GREY-FDY,CREAM-SHRINK", "BROWN-FDY/CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "BROWN-FDY/CREAM-SHRINK", "BEIGE-FDY,CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "GREY-FDY,CREAM-SHRINK", "BROWN-FDY/CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "BROWN-FDY/CREAM-SHRINK", "BEIGE-FDY,CREAM-SHRINK", "BLUE-FDY,CREAM-SHRINK", "GREY-FDY,CREAM-SHRINK"],
    "Размер": ["0103", "0203", "0303", "0403", "0503", "0603", "0729", "0829", "0929", "1029", "1129", "1229", "1334", "1434", "1534", "2434", "2434", "2434", "3040", "3040", "3040", "3040", "3040", "3040", "3050", "3050", "3050", "3050", "3050", "3050"],
    "кол-во": [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
}

# Создаем DataFrame
data_df = pd.DataFrame(data)


def transform_quantity_with_wight(df, mask, limit):
    df.loc[mask, 'кол-во'] -= limit
    df['кол-во'] = df['кол-во'].clip(lower=0)
    return df


def transform_quantity_with_limits(df, collection_name):
    try:
        with open(CONFIG_DIR / 'collections_limits.yaml', 'r') as file:
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


updated_df = transform_quantity_with_wight(data_df,
                                           (data_df['Размер'].str[:2].astype(int) > 8) & (data_df['Размер'].str[:2].astype(int) <= 12),
                                           1)
print(updated_df)
