import pytest
import pandas as pd
import numpy as np
import pandas.testing as pdt
from leftovers_module import core as leftovers_module_core

collection = 'antep_1640'
collection_url = f'https://venera-carpet.ru/category/grid/{collection}.html'
warehouses = [4, 92]
data = {
    'Фото': [np.nan, np.nan, np.nan, np.nan],
    'Рис. Цвет': ['F410 BEIGE', 'F410 CREAM', 'F410 BEIGE', 'F410 CREAM'],
    'Форма': ['Овал', 'Овал', 'Прямоугольник', 'Прямоугольник'],
    '0.8x1.5 уп. 2 шт.': [np.nan, np.nan, np.nan, '1 В корзине Ошибка'],
    '0.8x1.5 уп. 4 шт.': ['3 В корзине Ошибка', '1 В корзине Ошибка', '6 В корзине Ошибка', '3 В корзине Ошибка'],
    '1.6x2.3': ['3 В корзине Ошибка', '12 В корзине Ошибка', '6 В корзине Ошибка', '9 В корзине Ошибка'],
    '1.6x3': [np.nan, '1 В корзине Ошибка', '1 В корзине Ошибка', np.nan],
    '2x4': [np.nan, np.nan, '2 В корзине Ошибка', np.nan],
    '3x5': [np.nan, np.nan, np.nan, '3 В корзине Ошибка']
}
df_original = pd.DataFrame(data)

# # большой отладочный тест для проверки всех функций формировния таблицы штрихкодов и остатков
@pytest.mark.asyncio
async def test_parce_collection():
    session = await leftovers_module_core.venera_auth(leftovers_module_core.CONFIG_DIR / 'secrets.yaml')
    collection_name_url = collection_url.replace(leftovers_module_core.utils.load_config(leftovers_module_core.CONFIG_DIR / 'secrets.yaml')['venera_leftovers_link'],'').replace('.html', '')
    df, collection_name = await leftovers_module_core.get_table_df_and_collection_name(session, collection_url, warehouses)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table before formating\n'
          f'1. Таблица с остатками до форматирования:\n{df}')

    df = leftovers_module_core.split_columns_pattern_and_color(df)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after split_columns_pattern_and_color\n'
          f'1. Разделение колонки Рис. Цвет на Рис и Цвет:\n{df}')

    df = leftovers_module_core.size_grid_table_formatting(df)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after size_grid_table_formatting\n'
          f'1. Удаленна колонка Фото\n'
          f'2. Удалена последняя строчка с размерами\n'
          f'3. Все ячейки с NaN заменены на 0\n'
          f'4. Все ячейки очищены от \"В корзине Ошибка\":\n{df}')

    df = leftovers_module_core.multiply_packaging_columns(df)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after multiply_packaging_columns\n'
          f'1. Умножение содержимого в колонках в зависимости от названия колонки\n'
          f'Пример: 0.8x1.5 уп. 4 шт. значит кол-во х 4:\n{df}')

    df = leftovers_module_core.merge_duplicate_sizes(df)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after merge_duplicate_sizes\n'
          f'1. Данная функция объединяет одинаковые размеры\n'
          f'Пример: Объединит два столбика 0.8x1.5 уп. 4 шт. и 0.8x1.5 в один 0.8x1.5:\n{df}')

    df['Форма'] = list(map(lambda x: leftovers_module_core.transform_form_to_barcode_form(x), df['Форма']))
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after transform_form_to_barcode_form\n'
          f'1. Изменение названий в колонке Форма на те которые используются в штрихкоде\n'
          f'Пример: (Прямоугольник -> ST):\n{df}')

    df = df.melt(id_vars=['Рис', 'Цвет', 'Форма'], var_name='Размер', value_name='кол-во')
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after melt\n'
          f'1. Формирование таблицы:\n'
          f'из вида |Рис|Цвет|Форма|0.8x1.5|...|4x5|\n'
          f'в вид   |Рис|Цвет|Форма|Размер |кол-во |:\n{df}')

    df['Размер'] = list(map(lambda x: leftovers_module_core.transform_size(x), df['Размер']))
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after transform_size\n'
          f'Изменение содержимого колонки Размер на то что используются в штрихкоде:\n{df}')

    df = leftovers_module_core.replace_pattern(df)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after replace_pattern\n'
          f'Изменение содержимого колонки Рис на правильные рисунки которые используются в штрихкоде:\n{df}')

    df['Рис'] = list(map(lambda x: leftovers_module_core.remove_after_last_digit(x), df['Рис']))
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after replace_pattern\n'
          f'Удаление последней буквы в штрихкоде:\n{df}')

    df['Цвет'] = list(map(lambda x: leftovers_module_core.transform_color(x), df['Цвет']))
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after transform_color\n'
          f'Форматирование цвета для штрихкода:\n{df}')

    df = leftovers_module_core.insert_name_of_collection_column(df,collection_name)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after insert_name_of_collection_column\n'
          f'Вставка колонки с название коллекции:\n{df}')

    df = leftovers_module_core.subtract_one_from_column(df, 'кол-во')
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after subtract_one_from_column\n'
          f'Вычитание из колонки кол-во 1 ковер:\n{df}')

    df = leftovers_module_core.transform_quantity_with_limits(df, collection_name_url)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after transform_quantity_with_limits\n'
          f'Чтение и вычитание из колонки кол-во лимитов на ковры определенных коллекций прописанных в файле :\n{df}')

    df = leftovers_module_core.transform_quantity_with_wight(df, (df['Размер'].str[:2].astype(int) <= 8), 1)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after transform_quantity_with_wight\n'
          f'Вычитание из колонки кол-во 1 ковер так как он очень маленький:\n{df}')

    df = leftovers_module_core.transform_quantity_with_wight(df,
                                                             (df['Размер'].str[:2].astype(int) > 8) &
                                                             (df['Размер'].str[:2].astype(int) <= 12), 1)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after transform_quantity_with_wight\n'
          f'Вычитание из колонки кол-во 1 ковер так как он маленький:\n{df}')

    df['barcode'] = df.apply(lambda row: f'{row["Рис"]}-'
                                         f'{row["Форма"]}-'
                                         f'{row["Размер"]}-'
                                         f'{row["Коллекция"]}-'
                                         f'{row["Цвет"]}',
                                         axis=1)
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after df[\'barcode\']\n'
          f'Генерация штрихкода на основе |Коллекция|Рис|Форма|Цвет|Размер|:\n{df}')

    df = df.drop(columns=['Коллекция', 'Рис', 'Форма', 'Цвет', 'Размер'])
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after df.drop(columns)\n'
          f'Удаление колонок |Коллекция|Рис|Форма|Цвет|Размер|:\n{df}')

    df = df[['barcode', 'кол-во']]
    print(f'\n-----------------------------------------------\n'
          f'size_grid_table after df)\n'
          f'Поменяли местами колонки barcode и кол-во:\n{df}')
