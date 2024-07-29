// Получить модальные окна
var modal = document.getElementById("myModal");
var settingsModal = document.getElementById("settingsModal");
var editorModal = document.getElementById("editorModal");

// Получить кнопки, которые открывают модальные окна
var btn = document.getElementById("uploadBtn");
var settingsBtn = document.getElementById("settingsBtn");
var saveBtn = document.getElementById("saveBtn");

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
