from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from utils.file_utils import save_uploaded_file, process_file

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILES_DIR_INVOICES = BASE_DIR / 'invoices' / 'input_files'
OUTPUT_FILES_DIR_INVOICES = BASE_DIR / 'invoices' / 'output_files'

@router.post('/process-invoice')
async def process_invoice(file: UploadFile = File(...)):
    try:
        input_path = INPUT_FILES_DIR_INVOICES / file.filename
        output_path = OUTPUT_FILES_DIR_INVOICES / f'reconstructed_{file.filename}'

        await save_uploaded_file(file, input_path)
        process_file(input_path, output_path)

        if output_path.exists():
            return FileResponse(path=output_path, filename=f'reconstructed_{file.filename}',
                                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
