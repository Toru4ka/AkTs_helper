# AkTs_helper

### Запуск проекта в контейнере
- **Сборка контейнера**: Перейдите в каталог с Dockerfile и выполните команду для сборки контейнера:
```shell
docker build -t akts_helper .
```
- **Запуск контейнера**: После сборки контейнера, запустите его:
```shell
docker run -p 8080:8080 akts_helper
```
- Если вы используете docker-compose, просто выполните:
```shell
docker-compose up --build
```
