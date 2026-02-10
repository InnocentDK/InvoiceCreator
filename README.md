# InvoiceCreator (RU legal invoices)

Производственное веб-приложение для создания счетов на оплату с автонумерацией, хранением контрагентов, выбором DOCX-шаблона по типу услуг и экспортом в PDF.

## Структура

```text
invoice_app/
  backend/
    main.py
    database.py
    models.py
    init_db.py
    requirements.txt
    services/
      invoice_generator.py
      templates_mapper.py
      numbering.py
    templates/
      # DOCX templates are runtime assets (not stored in git)
  frontend/
    index.html
    create_invoice.html
    app.js
    styles.css
  invoices/
```

## Возможности

- Список созданных счетов с кнопками View / DOCX / PDF.
- Создание счета с блоками:
  - выбор организации;
  - контрагент с поиском по ИНН и автозаполнением;
  - мультиуслуги (кол-во, цена, описание);
  - динамические поля заметок по услуге.
- Автоподбор DOCX-шаблона по выбранной услуге.
- Автонумерация: `001`, `002`, `003`...
- Дата формата `DD.MM.YYYY`.
- Сохранение в SQLite с SQLAlchemy (архитектурно готово к PostgreSQL).
- Генерация DOCX по переменным `{{...}}`.
- Конвертация PDF через `docx2pdf`, fallback на LibreOffice headless.

## Установка (локально)

1. Установите Python 3.11.
2. Создайте и активируйте venv.
3. Установите зависимости:
   ```bash
   cd invoice_app/backend
   pip install -r requirements.txt
   ```
4. Инициализируйте БД (опционально, также происходит на старте):
   ```bash
   python init_db.py
   ```
5. Запуск dev-сервера (по требованию):
   ```bash
   uvicorn main:app --reload
   ```
6. Откройте в браузере: `http://127.0.0.1:8000`.

## Развертывание на VPS/hosting

- Рекомендуется запуск через `systemd` + `uvicorn` (или `gunicorn -k uvicorn.workers.UvicornWorker`).
- Статические файлы фронтенда отдаются самим FastAPI (маршрут `/frontend`).
- Для PDF убедитесь, что установлен хотя бы один вариант:
  - `docx2pdf` (Windows/macOS),
  - `libreoffice` (Linux, режим `--headless`).
- Папка `invoice_app/invoices` должна быть доступна на запись.
- DOCX-шаблоны должны быть размещены при деплое в `invoice_app/backend/templates` (в репозитории не хранятся).

## Миграция к PostgreSQL

- Замените `DATABASE_URL` в `backend/database.py` на PostgreSQL DSN.
- Для production рекомендуется добавить Alembic миграции.

## API (кратко)

- `GET /api/organizations`
- `GET /api/services`
- `GET /api/contractors/search?inn=...`
- `GET /api/invoices`
- `GET /api/invoices/{id}`
- `GET /api/invoices/{id}/docx`
- `GET /api/invoices/{id}/pdf`
- `POST /api/invoices`

## Примечания

- Если в счете выбраны услуги из разных групп шаблонов, API вернет ошибку валидации.
- Если PDF-конвертер недоступен, создается диагностический `.pdf`-файл-заглушка с описанием ошибки.
