from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi.responses import PlainTextResponse
import os
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

router = APIRouter()


@router.get("/")
def index():
    with open(STATIC_DIR / "index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


@router.get("/version", response_class=PlainTextResponse)
async def get_version():
    version_file = BASE_DIR / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "Version not found"
