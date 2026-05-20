# 📊 Log Analyzer Pro

Log Analyzer Pro — это мощный анализатор веб-логов на базе Streamlit + SQLite для быстрого исследования трафика, ботов, URL, IP-адресов и поведения пользователей.

Подходит для:
- SEO-специалистов
- DevOps
- системных администраторов
- аналитики серверных логов
- анализа поисковых ботов Google/Yandex/Bing/Ahrefs/Semrush

---

# 🚀 Возможности

## ✅ Импорт логов
- Быстрая загрузка `.log` файлов
- Батчевый импорт в SQLite
- WAL режим для высокой скорости
- Поддержка больших логов

---

## 🔍 Конструктор SQL-фильтров
Визуальный builder условий через:
- URL
- User-Agent
- IP
- Referer
- Status Code
- Тип трафика
- Domain

Поддерживаются:
- Contains
- Equals
- AND / OR
- LIKE фильтрация

---

## 📈 Аналитика трафика
- Графики запросов по времени
- Топ URL
- Количество запросов
- Уникальные IP

---

## 🕷️ Анализ ботов
Автоматическое определение:
- Googlebot
- YandexBot
- Bingbot
- AhrefsBot
- SemrushBot
- DotBot
- MJ12Bot
- других crawler/spider bot

Для каждого бота:
- User-Agent
- IP
- динамика посещений
- количество hits

---

## 📄 Просмотр сырых данных
- SQL WHERE отображение
- DataFrame таблица
- последние запросы
- фильтрация в реальном времени

---

# ⚙️ Технологии

- Python
- Streamlit
- SQLite
- Pandas
- Regex Parsing
- streamlit-condition-tree

---



---

## 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

---

## 3. Запуск приложения

```bash
streamlit run app.py
```

---

# 📁 Структура проекта

```bash
project/
│
├── app.py
├── logs.db
├── requirements.txt
└── *.log
```

---

# 🧠 Поддерживаемый формат логов

Поддерживаются стандартные access.log форматы:

```log
127.0.0.1 - - [10/May/2026:13:55:36 +0300] "GET / HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
```

---

# ⚡ Производительность

Оптимизации:
- SQLite WAL
- Batch insert
- Индексы по datetime и ua_type
- Быстрый regex parser
- Минимальная нагрузка RAM

---

# 🔥 Пример сценариев использования

## SEO
- Анализ crawl budget
- Поиск мусорных URL
- Анализ активности Googlebot

## DevOps
- Мониторинг трафика
- Поиск аномалий
- Анализ нагрузки

## Security
- Подозрительные IP
- Спам-боты
- Необычные User-Agent

---

# 📷 Интерфейс

- Sidebar импорт
- Визуальные графики
- Таблицы
- Конструктор условий
- Аналитика ботов

---

# 🛠️ Возможные улучшения

Планируемые функции:
- GeoIP анализ
- Экспорт CSV/Excel
- ClickHouse поддержка
- AI-анализ аномалий
- Live monitoring
- Apache/Nginx presets

---

