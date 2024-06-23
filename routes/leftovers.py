from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import asyncio
from leftovers.leftovers_async import run_generation

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILES_DIR_LEFTOVERS = BASE_DIR / 'leftovers' / 'output_files'

@router.get('/venera-carpet-leftovers')
async def generate():
    try:
        await asyncio.to_thread(run_generation)

        output_file = OUTPUT_FILES_DIR_LEFTOVERS / 'leftovers.csv'
        if output_file.exists():
            return FileResponse(path=output_file, filename='leftovers.csv', media_type='text/csv')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
