from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AkTs Helper</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h1 class="mt-5">Welcome to AkTs Helper!</h1>
            <div class="mt-3">
                <button class="btn btn-primary" onclick="window.location.href='/venera-carpet-leftovers'">Остатки с venera-carpet.ru</button>
                <button id="uploadBtn" class="btn btn-secondary">Отформатировать накладную</button>
            </div>
        </div>

        <!-- Модальное окно -->
        <div id="myModal" class="modal" tabindex="-1" role="dialog">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Upload your invoice file</h5>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <form action="/process-invoice" method="post" enctype="multipart/form-data">
                            <div class="form-group">
                                <input type="file" class="form-control-file" name="file">
                            </div>
                            <button type="submit" class="btn btn-primary">Upload</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        <script src="/static/scripts.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
