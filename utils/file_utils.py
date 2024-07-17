from fastapi import UploadFile
from pathlib import Path
import logging
import shutil


async def save_uploaded_file(file: UploadFile, destination: Path):
    with open(destination, 'wb') as f:
        f.write(await file.read())


async def delete_file(file_path: Path):
    try:
        file_path.unlink()
        logging.info(f"File {file_path} has been deleted.")
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {e}")


def clear_folder(output_folder):
    # Удаляем все файлы и папки в указанной директории
    for item in output_folder.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
