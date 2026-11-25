# Тренажёр по операционным системам

Тренажёр для подготовки к экзамену: выберите тему, ответьте на вопросы и
получите балл с разбором ошибок. Проект использует Django 5.2, шаблоны
Django, PostgreSQL и Valkey.

SDD: [спецификация](docs/spec.md), [план реализации](docs/plan.md) и
[задачи с проверками](docs/tasks.md).

## Запуск из чистой копии на Windows

Установите и запустите Docker Desktop в режиме Linux-контейнеров.
Откройте PowerShell в корне проекта (рядом с `compose.yaml`) и выполните:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build -d
docker compose exec web python manage.py migrate
```

Откройте [http://localhost:8001/](http://localhost:8001/). На главной странице
будет список тем с количеством вопросов. Если в базе нет тем, появится
сообщение «Темы пока не добавлены». Значения из `.env.example` подходят
только для локальной разработки.

Compose поднимает `web` после готовности `db` и `valkey`. PostgreSQL хранит
учебные данные, Valkey — только список карточек главной страницы с TTL
60 секунд. Порт Valkey наружу не публикуется.

## Демонстрационные данные

После запуска и применения миграций загрузите две темы с вопросами:

```powershell
docker compose exec web python manage.py loaddata demo.json
```

На главной появятся темы [«Процессы»](http://localhost:8001/topics/processes/)
и [«Память»](http://localhost:8001/topics/memory/), по 5 вопросов в каждой.
Повторная загрузка перезаписывает записи из фикстуры. Если главную уже
открывали, изменения появятся после истечения TTL. Чтобы обновить список
сразу, можно удалить только его ключ, как показано ниже.

## Тесты и ручная проверка

```powershell
docker compose ps
docker compose exec web python manage.py showmigrations
docker compose exec web python manage.py test
```

У сервисов `db` и `valkey` должен быть статус `healthy`, применённые
миграции отмечены `[X]`. Для ручной проверки:

1. Откройте [главную](http://localhost:8001/) и выберите «Процессы».
2. Выберите варианты № 2, 1, 1, 1 и 2 соответственно и нажмите «Проверить
   ответы». Ожидается балл `3/5` и пояснения к вопросам 2 и 4.
3. Нажмите «Пройти ещё раз», выберите те же варианты, но пропустите третий
   вопрос. Возле него должно появиться сообщение «Выберите ответ на этот
   вопрос.», а остальные четыре варианта останутся выбранными.
4. [Несуществующая тема](http://localhost:8001/topics/unknown/) должна
   возвращать HTTP 404.

## Демонстрация Valkey на защите

После загрузки демоданных выполните блок подряд, не открывая главную в
других вкладках. Удаляется только кеш списка тем, данные PostgreSQL не
затрагиваются:

```powershell
$key = 'os-trainer:1:quiz:topics'
$counters = 'cmdstat_(get|set):'
docker compose exec -T valkey valkey-cli PING
docker compose exec -T valkey valkey-cli DEL $key
docker compose exec -T valkey valkey-cli TTL $key
docker compose exec -T valkey valkey-cli INFO commandstats | Select-String $counters

(Invoke-WebRequest -UseBasicParsing -Uri http://localhost:8001/).StatusCode
docker compose exec -T valkey valkey-cli TTL $key
docker compose exec -T valkey valkey-cli INFO commandstats | Select-String $counters

(Invoke-WebRequest -UseBasicParsing -Uri http://localhost:8001/).StatusCode
docker compose exec -T valkey valkey-cli TTL $key
docker compose exec -T valkey valkey-cli INFO commandstats | Select-String $counters
```

Ожидаются `PONG` и начальный TTL `-2` (ключа нет). Первый запрос вернёт
`200`, добавит `GET` и `SET`, а TTL будет около 60 секунд. Второй запрос
вернёт `200` с тем же списком, добавит только `GET` и не продлит TTL.
Счётчики накопительные: сравнивайте значения `calls` до и после запросов.
Если `GET` и `SET` ещё не выполнялись, соответствующих строк может не быть.

Чтобы отдельно показать, что Django сделал **1 SQL-запрос на холодном
кеше и 0 на прогретом**, запустите интеграционные тесты с реальными
PostgreSQL и Valkey. Тесты используют отдельную тестовую БД и ключи кеша:

```powershell
docker compose exec -T web python manage.py test config.tests.TopicCacheTests -v 2
```

Для остановки выполните `docker compose down`. Данные PostgreSQL сохранятся
в именованном томе `postgres_data`.
