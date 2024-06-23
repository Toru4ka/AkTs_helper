from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import asyncio
from leftovers.leftovers_async import run_generation
from invoices.invoice_processor import process_file

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILES_DIR_LEFTOVERS = BASE_DIR / 'leftovers' / 'output_files'
INPUT_FILES_DIR_INVOICES = BASE_DIR / 'invoices' / 'input_files'
OUTPUT_FILES_DIR_INVOICES = BASE_DIR / 'invoices' / 'output_files'

@app.get('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AkTs Helper</title>
        <style>
            /* Стиль для модального окна */
            .modal {
                display: none; 
                position: fixed; 
                z-index: 1; 
                left: 0;
                top: 0;
                width: 100%; 
                height: 100%; 
                overflow: auto; 
                background-color: rgb(0,0,0); 
                background-color: rgba(0,0,0,0.4); 
                padding-top: 60px;
            }
            .modal-content {
                background-color: #fefefe;
                margin: 5% auto;
                padding: 20px;
                border: 1px solid #888;
                width: 80%; 
            }
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
            }
            .close:hover,
            .close:focus {
                color: black;
                text-decoration: none;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>Welcome to AkTs Helper!</h1>
        <button onclick="window.location.href='/venera-carpet-leftovers'">Остатки с venera-carpet.ru</button>
        <button id="uploadBtn">Отформатировать накладную</button>

        <!-- Модальное окно -->
        <div id="myModal" class="modal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <h1>Upload your invoice file</h1>
                <form action="/process-invoice" method="post" enctype="multipart/form-data">
                    <input type="file" name="file">
                    <input type="submit" value="Upload">
                </form>
            </div>
        </div>

        <script>
            // Получить модальное окно
            var modal = document.getElementById("myModal");

            // Получить кнопку, которая открывает модальное окно
            var btn = document.getElementById("uploadBtn");

            // Получить элемент <span>, который закрывает модальное окно
            var span = document.getElementsByClassName("close")[0];

            // Когда пользователь нажимает на кнопку, открыть модальное окно
            btn.onclick = function() {
                modal.style.display = "block";
            }

            // Когда пользователь нажимает на <span> (x), закрыть модальное окно
            span.onclick = function() {
                modal.style.display = "none";
            }

            // Когда пользователь нажимает в любом месте за пределами модального окна, закрыть его
            window.onclick = function(event) {
                if (event.target == modal) {
                    modal.style.display = "none";
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get('/venera-carpet-leftovers')
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

@app.post('/process-invoice')
async def process_invoice(file: UploadFile = File(...)):
    try:
        input_path = INPUT_FILES_DIR_INVOICES / file.filename
        output_path = OUTPUT_FILES_DIR_INVOICES / f'reconstructed_{file.filename}'

        with open(input_path, 'wb') as f:
            f.write(await file.read())

        process_file(input_path, output_path)

        if output_path.exists():
            return FileResponse(path=output_path, filename=f'reconstructed_{file.filename}',
                                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            raise HTTPException(status_code=500, detail="File not found after processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
