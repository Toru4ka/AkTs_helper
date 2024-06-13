from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import asyncio
from leftovers.leftovers_async import run_generation

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILES_DIR = BASE_DIR / 'leftovers' / 'output_files'

@app.get('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AkTs Helper</title>
    </head>
    <body>
        <h1>Welcome to AkTs Helper!</h1>
        <button onclick="window.location.href='/venera-carpet-leftovers'">Остатки с venera-carpet.ru</button>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get('/venera-carpet-leftovers')
async def generate():
    try:
        # Запускаем основной скрипт генерации
        await asyncio.to_thread(run_generation)

        output_file = OUTPUT_FILES_DIR / 'leftovers.csv'
        if output_file.exists():
            return FileResponse(path=output_file, filename='leftovers.csv', media_type='text/csv')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
