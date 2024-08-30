document.getElementById('download-btn').addEventListener('click', function() {
    //Swal.fire("Выгрузка остатков начата, подождите несколько секунд", { buttons: false, timer: 1000,});
    swal("Выгрузка остатков начата, подождите несколько секунд", { buttons: false, timer: 2000,});
    fetch('/venera-carpet-leftovers')
        .then(response => {
            if (response.ok) {
                // Создаем ссылку для скачивания файла
                response.blob().then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = 'file.txt';  // Имя файла, под которым он будет сохранен
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);

                    // Воспроизведение звука
                    const audio = document.getElementById('success-sound');
                    audio.currentTime = 0;  // Перематываем звук в начало
                    audio.play();
                    //document.getElementById('success-sound').play();

                    // Отображение уведомления
                    //alert('Файл успешно скачан!');
                    //toastr
                    //toastr.success('File downloaded successfully!', 'Success');
                    // Swal.fire({
                    //     title: 'Success!',
                    //     text: 'File downloaded successfully!',
                    //     icon: 'success',
                    //     confirmButtonText: 'OK'
                    // });
                    swal({
                        title: 'Success!',
                        text: 'File downloaded successfully!',
                        icon: 'success',
                        confirmButtonText: 'OK'
                    });
                });
            }
        })
        .catch(error => console.error('Ошибка при скачивании файла:', error));
});