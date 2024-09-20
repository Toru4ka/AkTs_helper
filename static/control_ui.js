// Получить модальные окна
var modal = document.getElementById("myModal");
var settingsModal = document.getElementById("settingsModal");
var editorModal = document.getElementById("editorModal");
var downloadModal = document.getElementById("downloadModal");  // Модальное окно для выбора склада

// Получить кнопки, которые открывают модальные окна
var btn = document.getElementById("uploadBtn");
var settingsBtn = document.getElementById("settingsBtn");
var saveBtn = document.getElementById("saveBtn");
var downloadBtn = document.getElementById("download-btn");  // Кнопка для выгрузки остатков

// Получить элементы <span>, которые закрывают модальные окна
var spans = document.getElementsByClassName("close");

// Когда пользователь нажимает на кнопку, открыть соответствующее модальное окно
btn.onclick = function() {
    modal.style.display = "block";
}
settingsBtn.onclick = function() {
    settingsModal.style.display = "block";
    loadYamlFiles();
}
downloadBtn.onclick = function() {
    downloadModal.style.display = "block";  // Открыть модальное окно для выбора склада
}

// Когда пользователь нажимает на <span> (x), закрыть соответствующее модальное окно
for (var i = 0; i < spans.length; i++) {
    spans[i].onclick = function() {
        this.closest('.modal').style.display = "none";
    }
}

// Когда пользователь нажимает в любом месте за пределами модального окна, закрыть его
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
    if (event.target == settingsModal) {
        settingsModal.style.display = "none";
    }
    if (event.target == editorModal) {
        editorModal.style.display = "none";
    }
    if (event.target == downloadModal) {
        downloadModal.style.display = "none";  // Закрыть окно выбора склада
    }
}

// Функция для загрузки YAML файлов
function loadYamlFiles() {
    fetch('/settings/get-yaml-files')
        .then(response => response.json())
        .then(data => {
            var settingsBody = document.getElementById("settingsBody");
            settingsBody.innerHTML = '';
            data.files.forEach(file => {
                var button = document.createElement("button");
                button.className = "btn btn-outline-primary";
                button.innerText = file.alias; // Используем псевдоним вместо реального имени файла
                button.onclick = function() {
                    openEditor(file.filename); // Используем реальное имя файла для открытия редактора
                }
                settingsBody.appendChild(button);
            });
        });
}

// Функция для открытия редактора файла
function openEditor(filename) {
    fetch('/settings/get-yaml-file/' + filename)
        .then(response => response.json())
        .then(data => {
            document.getElementById("editorTitle").innerText = "Редактор файла: " + data.filename;
            document.getElementById("fileContent").value = data.content;
            document.getElementById("saveBtn").setAttribute("data-filename", data.filename);
            editorModal.style.display = "block";
        })
        .catch(error => {
            console.error('Error fetching the YAML file:', error);
            alert('Error fetching the YAML file.');
        });
}

// Функция для сохранения изменений в файле
saveBtn.onclick = function() {
    var filename = this.getAttribute("data-filename");
    var content = document.getElementById("fileContent").value;
    fetch('/settings/save-yaml-file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filename: filename,
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            alert("Файл успешно сохранен!");
            editorModal.style.display = "none";
        } else {
            alert("Ошибка при сохранении файла.");
        }
    });
}


// Обработка кликов по кнопкам внутри модального окна выбора склада
document.getElementById("mytishchiBtn").addEventListener("click", function() {
    downloadLeftovers('/venera-carpet-leftovers/mytishchi');
});

document.getElementById("vyoshkiBtn").addEventListener("click", function() {
    downloadLeftovers('/venera-carpet-leftovers/vyoshki');
});

document.getElementById("allWarehouseBtn").addEventListener("click", function() {
    downloadLeftovers('/venera-carpet-leftovers/all_warehouses');
});

// Функция для выгрузки остатков
function downloadLeftovers(url) {
    swal("Выгрузка остатков начата, подождите несколько секунд", { buttons: false, timer: 2000,});
    fetch(url)
        .then(response => {
            if (response.ok) {
                response.blob().then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = 'leftovers.csv';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);

                    const audio = document.getElementById('success-sound');
                    audio.currentTime = 0;
                    audio.play();

                    swal({
                        title: 'Success!',
                        text: 'File downloaded successfully!',
                        icon: 'success',
                        confirmButtonText: 'OK'
                    });
                });
            } else {
                swal({
                    title: 'Error!',
                    text: 'Failed to download the file.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            }
        })
        .catch(error => {
            console.error('Ошибка при скачивании файла:', error);
            swal({
                title: 'Error!',
                text: 'Ошибка при скачивании файла.',
                icon: 'error',
                confirmButtonText: 'OK'
            });
        });
}