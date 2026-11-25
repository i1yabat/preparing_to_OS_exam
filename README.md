# Тренажёр по операционным системам

Тренажёр для подготовки к экзамену. Доступны список тем и страницы тем с
количеством вопросов. Прохождение тестов пока не реализовано.
Проект использует Django 5.2, шаблоны Django и PostgreSQL.

## Запуск в PowerShell

Запустите Docker Desktop с Linux-контейнерами. Из корня проекта выполните:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build -d
docker compose exec web python manage.py migrate
```

Откройте [http://localhost:8001/](http://localhost:8001/). На главной странице
появится заголовок «Тренажёр по операционным системам». Если база ещё пуста,
страница покажет «Темы пока не добавлены». Значения из `.env.example`
подходят только для локальной разработки.

## Демонстрационные данные

После запуска и применения миграций загрузите две темы с вопросами:

```powershell
docker compose exec web python manage.py loaddata demo.json
```

На главной появятся темы [«Процессы»](http://localhost:8001/topics/processes/)
и [«Память»](http://localhost:8001/topics/memory/), по 5 вопросов в каждой.
Повторная загрузка перезаписывает записи этой фикстуры.
Адрес [неизвестной темы](http://localhost:8001/topics/unknown/) вернёт HTTP 404,
если такой темы нет в базе.

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
