# Catalog Scraper

![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.52+-2EAD33?logo=playwright&logoColor=white)
![Camoufox](https://img.shields.io/badge/Browser-Camoufox-orange)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)

Веб-скрапер каталога торгового дома с антидетект-обходом, cookie warmup, lazy loading, интерактивным взаимодействием с интерфейсом через playwright и валидацией данных через Pydantic v2. На выходе - структурированный JSON-каталог товаров с характеристиками, описанием, отзывами и вопросами-ответами.

## Workflow

```mermaid
flowchart TD
    A["🔍 Google Search"] -->|"реферальный трафик"| B["🍪 Cookie Warmup"]
    B --> C["📂 Root Catalog"]
    C --> D["🔀 Recursive DFS"]
    D -->|"подкатегория"| D
    D --> E["📄 Product Page"]
    E --> F["💰 Price"]
    E --> G["📋 Properties"]
    E --> H["💬 Comments"]
    E --> I["❓ Q&A"]
    E --> J["📝 Description"]
    F & G & H & I & J --> K["✅ Pydantic Validation"]
    K --> L["💾 catalog.json"]

    style A fill:#4285f4,color:#fff
    style B fill:#fbbc05,color:#333
    style K fill:#2ea043,color:#fff
    style L fill:#6e40c9,color:#fff
```

## Особенности

- **Антифингерпринт** - [Camoufox](https://github.com/nicegoodthings/Camoufox) на базе Firefox с `humanize=True`, рандомизированными движениями мыши, плавным скроллом с переменной скоростью и случайными задержками между запросами
- **Симуляция реферального трафика** - переход через Google Search перед целевым доменом формирует естественную картину трафика и разогревает cookie
- **Персистентные сессии** - профиль браузера и cookies сохраняются между запусками через `persistent_context`
- **Рекурсивный обход** - автоматическое обнаружение и спуск во вложенные подкатегории с поддержкой пагинации
- **Pydantic v2** - строгая типизация и валидация каждой извлечённой карточки товара
- **Идентификация товаров по URL**  исключает повторный обход уже собранных товаров
- автоматические повторные попытки при ошибках

## Быстрый старт

**1.** Указать целевой домен в `src/crawler.py`:

```python
DOMAIN = 'https://example.ru'
```

**2.** Установить зависимости и запустить:

```bash
pip install -r requirements.txt
python -m src.main
```

Результат появится в `catalog/catalog.json`.

## Структура проекта

```
src/
├── main.py          # Точка входа — запуск Camoufox, инициализация обхода
├── browser.py       # Google-реферал и разогрев cookie
├── crawler.py       # Рекурсивный обход каталога и извлечение данных
├── models.py        # Pydantic v2 модели (Product, Catalog)
├── catalog.py       # JSON-persistence с дедупликацией
├── utils.py         # Retry-декоратор, имитация скролла, подавление ошибок
├── chrome.py        # Резолв пути профиля Chrome (macOS)
└── logger.py        # Цветное логирование с поддержкой PyCharm
```

## Лицензия

[GPL-3.0](LICENSE)
