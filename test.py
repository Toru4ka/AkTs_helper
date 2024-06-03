import pandas as pd
import yaml
from pathlib import Path
import re
BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / 'configs'
OUTPUT_FILES_DIR = BASE_DIR / 'output_files'

# Пример данных, аналогичный вашему DataFrame
data = {
    'Рис.': ['AC16', 'AC16', 'BD17', 'D979', 'D979', 'D983', 'D983', 'D984', 'D993'],
    'Форма': ['прямоугольник', 'прямоугольник', 'круг', 'прямоугольник', 'прямоугольник', 'прямоугольник', 'овал', 'прямоугольник', 'прямоугольник'],
    'Цвет': ['BEIGE-BLUE', 'BLUE', 'BEIGE-BLUE', 'BEIGE', 'BEIGE-BLUE', 'BEIGE-BLUE', 'BEIGE-BLUE', 'BEIGE', 'CREAM-BLUE'],
    '0.20x0.30': [0, 0, 0, 0, 0, 0, 0, 0, 0],
    '0.80x1.50': [0, 0, 0, 48, 29, 4, 0, 0, 0],
    '1.00x2.00': [0, 0, 0, 76, 52, 8, 10, 21, 1],
    '1.00x2.40': [0, 0, 0, 0, 0, 0, 0, 0, 0]
}

# Создаем DataFrame
df = pd.DataFrame(data)

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


def create_barcode(df):
    #df.insert(0, 'Barcode', None)
    df_melted = df.melt(id_vars=['Рис.', 'Форма', 'Цвет'],
                        var_name='Размер',
                        value_name='кол-во')
    return df_melted


# def transform_size(size):
#     size = size.split('x')
#     print(f'size: {size}')
#     width = size[0]
#     width = width.split('.')
#     width[1] = width[1].replace('00', '0')
#     width[1] = width[1].replace('0', '')
#     width = width[0] + width[1]
#     print(f'width: {width}')
#     height = size[1]
#     height = height.split('.')
#     height[1] = height[1].replace('00', '0')
#     height[1] = height[1].replace('0', '')
#     height = height[0] + height[1]
#     print(f'height: {height}')
#     size = width + height
#     return size

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

def remove_after_last_digit(s):
    pattern = r'(.*\d).*?$'
    match = re.match(pattern, s)
    if match:
        return match.group(1)
    else:
        return s

# df = create_barcode(df)

# 1) 0.80x0.80 -> 0808
# 2) 0.80x1.50 -> 0815
# 3) 1.50x1.90 -> 1519
# 4) 1.35x1.95 -> 135195


print(remove_after_last_digit('DFD0342422jgkv'))