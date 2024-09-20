from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import asyncio
from leftovers.leftovers_async import run_generation
from utils.file_utils import clear_folder
from starlette.background import BackgroundTasks

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILES_DIR_LEFTOVERS = BASE_DIR / 'leftovers' / 'output_files'


@router.get('/venera-carpet-leftovers/mytishchi')
async def generate(background_tasks: BackgroundTasks):
    warehouse = "?warehouses%5B%5D=4"
    try:
        await asyncio.to_thread(run_generation, warehouse)
        output_file = OUTPUT_FILES_DIR_LEFTOVERS / 'leftovers.csv'
        if output_file.exists():
            background_tasks.add_task(clear_folder, OUTPUT_FILES_DIR_LEFTOVERS)
            return FileResponse(path=output_file,
                                filename='leftovers.csv',
                                media_type='text/csv')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/venera-carpet-leftovers/vyoshki')
async def generate(background_tasks: BackgroundTasks):
    warehouse = "?warehouses%5B%5D=80"
    try:
        await asyncio.to_thread(run_generation, warehouse)
        output_file = OUTPUT_FILES_DIR_LEFTOVERS / 'leftovers.csv'
        if output_file.exists():
            background_tasks.add_task(clear_folder, OUTPUT_FILES_DIR_LEFTOVERS)
            return FileResponse(path=output_file,
                                filename='leftovers.csv',
                                media_type='text/csv')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/venera-carpet-leftovers/all_warehouses')
async def generate(background_tasks: BackgroundTasks):
    warehouse = "?warehouses%5B%5D=4&warehouses%5B%5D=80&warehouseType=many"
    try:
        await asyncio.to_thread(run_generation, warehouse)
        output_file = OUTPUT_FILES_DIR_LEFTOVERS / 'leftovers.csv'
        if output_file.exists():
            background_tasks.add_task(clear_folder, OUTPUT_FILES_DIR_LEFTOVERS)
            return FileResponse(path=output_file,
                                filename='leftovers.csv',
                                media_type='text/csv')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

