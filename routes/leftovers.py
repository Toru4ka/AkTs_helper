from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import asyncio
# from leftovers.leftovers_async import run_generation
from leftovers.leftovers_module import core as leftovers_module_core
from utils.file_utils import clear_folder
from starlette.background import BackgroundTasks
import utils.file_utils as utils
import logging
router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILES_DIR_LEFTOVERS = BASE_DIR / 'leftovers' / 'output_files'
CONFIG_DIR = BASE_DIR / 'configs' / 'users_configs'

logger = logging.getLogger("uvicorn")

@router.get('/venera-carpet-leftovers/{warehouse_name}')
async def generate(warehouse_name: str, background_tasks: BackgroundTasks):
    config = utils.load_config(CONFIG_DIR / 'warehouses.yaml') # Загрузка конфигурации из YAML файла



    if warehouse_name not in config['warehouses']:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    warehouse_config = config['warehouses'][warehouse_name]
    warehouse_id = warehouse_config['id']

    logger.info(f"warehouse name: {warehouse_name}")
    logger.info(f"warehouse id: {warehouse_id}")

    try:
        # Вызов функции для генерации CSV
        await asyncio.to_thread(leftovers_module_core.run_generation, warehouse_name, warehouse_id)

        # Путь к файлу с результатом
        output_file = OUTPUT_FILES_DIR_LEFTOVERS / f'{warehouse_name}_leftovers.csv'

        if output_file.exists():
            # Очистка папки после генерации
            background_tasks.add_task(clear_folder, OUTPUT_FILES_DIR_LEFTOVERS)
            return FileResponse(path=output_file,
                                filename=f'{warehouse_name}_leftovers.csv',
                                media_type='text/csv')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))