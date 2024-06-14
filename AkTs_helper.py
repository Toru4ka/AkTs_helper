from fastapi import FastAPI, HTTPException,  UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import asyncio
from leftovers.leftovers_async import run_generation
from invoices.invoice_processor import process_file

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILES_DIR_LEFTOVERS = BASE_DIR / 'leftovers' / 'output_files'
OUTPUT_FILES_DIR_INVOICES = BASE_DIR / 'invoices' / 'output_files'

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
        <button onclick="window.location.href='/upload-invoice'">Отформатировать накладную</button>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get('/venera-carpet-leftovers')
async def generate():
    try:
        # Запускаем основной скрипт генерации
        await asyncio.to_thread(run_generation)

        output_file = OUTPUT_FILES_DIR_LEFTOVERS / 'leftovers.csv'
        if output_file.exists():
            return FileResponse(path=output_file, filename='leftovers.csv', media_type='text/csv')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/upload-invoice')
def upload_invoice_form():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload Invoice</title>
    </head>
    <body>
        <h1>Upload your invoice file</h1>
        <form action="/process-invoice" method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post('/process-invoice')
async def process_invoice(file: UploadFile = File(...)):
    try:
        input_path = OUTPUT_FILES_DIR_INVOICES / file.filename
        output_path = OUTPUT_FILES_DIR_INVOICES / 'reconstructed_invoice.xlsx'

        # Save the uploaded file to disk
        with open(input_path, 'wb') as f:
            f.write(await file.read())

        # Process the file using the imported module
        process_file(input_path, output_path)

        # Return the processed file
        if output_path.exists():
            return FileResponse(path=output_path, filename='reconstructed_invoice.xlsx',
                                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))