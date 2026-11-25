# Тренажёр по операционным системам

Тренажёр для подготовки к экзамену. Пока доступна только главная страница.
Проект использует Django 5.2, шаблоны Django и PostgreSQL.

## Запуск в PowerShell

Запустите Docker Desktop с Linux-контейнерами. Из корня проекта выполните:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build -d
docker compose exec web python manage.py migrate
```

Откройте [http://localhost:8000](http://localhost:8000). На странице должен
появиться заголовок «Тренажёр по операционным системам». Значения из
`.env.example` подходят только для локальной разработки.

## Проверка

```powershell
docker compose ps
docker compose exec web python manage.py showmigrations
docker compose exec web python manage.py test
(Invoke-WebRequest -Uri http://localhost:8001/ -UseBasicParsing).Content
```

У сервиса `db` должен быть статус `healthy`, применённые миграции отмечены
`[X]`, а ответ главной страницы содержит ожидаемый заголовок.

Для остановки выполните `docker compose down`. Данные PostgreSQL сохранятся
в именованном томе `postgres_data`.
