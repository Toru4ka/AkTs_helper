# AkTs_helper

### Запуск проекта в контейнере
- **Сборка контейнера**: Перейдите в каталог с Dockerfile и выполните команду для сборки контейнера:
```shell
docker build -t akts_helper:ver .
```
- **Запуск контейнера**: После сборки контейнера, запустите его:
```shell
docker run -d --name akts_helper -p 8080:8080 toru4ka/akts_helper:ver
```
