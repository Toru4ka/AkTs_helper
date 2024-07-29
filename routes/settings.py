from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import yaml

router = APIRouter()

# Путь к папке с конфигурационными файлами
BASE_DIR = Path(__file__).resolve().parent.parent
config_path = BASE_DIR / 'configs' / 'users_configs'
# Путь к файлу псевдонимов
aliases_file = BASE_DIR / 'configs' / "aliases.yaml"

@router.get("/get-yaml-files")
async def get_yaml_files():
    if not config_path.exists() or not config_path.is_dir():
        raise HTTPException(status_code=404, detail="Config directory not found")

    yaml_files = list(config_path.glob("*.yaml"))
    files = [file.name for file in yaml_files]

    # Чтение псевдонимов
    if aliases_file.exists():
        with open(aliases_file, 'r', encoding='utf-8') as f:
            aliases = yaml.safe_load(f)
    else:
        aliases = {}

    # Создание списка файлов с псевдонимами
    files_with_aliases = [{"filename": file, "alias": aliases.get(file, file)} for file in files]

    return JSONResponse(content={"files": files_with_aliases})

@router.get("/get-yaml-file/{filename}")
async def get_yaml_file(filename: str):
    file_path = config_path / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return JSONResponse(content={"filename": filename, "content": content})

@router.post("/save-yaml-file")
async def save_yaml_file(data: dict):
    filename = data.get("filename")
    content = data.get("content")

    if not filename or not content:
        raise HTTPException(status_code=400, detail="Invalid request")

    file_path = config_path / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return JSONResponse(content={"status": "success"})
