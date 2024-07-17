from fastapi import UploadFile
from pathlib import Path

async def save_uploaded_file(file: UploadFile, destination: Path):
    with open(destination, 'wb') as f:
        f.write(await file.read())
