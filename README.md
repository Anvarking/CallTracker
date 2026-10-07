# 📊 CallTracker v2.0

Веб-приложение для учета и анализа ежедневной производительности сотрудников контакт-центра.

CallTracker позволяет фиксировать план и фактическое количество обработанных звонков, отслеживать выполнение плана, анализировать показатели за выбранный период и экспортировать данные.

## 🚀 Возможности

### 📈 Dashboard

* Общая статистика по рабочим дням
* План и факт
* Разница между планом и фактом
* Процент выполнения
* Количество выполненных и невыполненных дней
* График план/факт
* Фильтрация по произвольному периоду
* Автоматическое определение выходных дней

### 👤 Пользователи

* Авторизация
* Безопасное хранение паролей
* Роли `user` и `admin`
* Добавление пользователей
* Редактирование пользователей
* Активация и деактивация пользователей
* Удаление пользователей
* Защита последнего администратора

### 📤 Экспорт

* Экспорт данных в CSV
* Экспорт данных в Excel

## 🛠 Технологии

* Python 3
* Flask
* PostgreSQL
* psycopg2
* Bootstrap 5
* Chart.js
* OpenPyXL
* python-dotenv
* Werkzeug

## 📁 Структура проекта

```text
CallTracker v2.0/
│
├── templates/
│   ├── add.html
│   ├── add_user.html
│   ├── base.html
│   ├── delete.html
│   ├── edit.html
│   ├── edit_user.html
│   ├── index.html
│   ├── login.html
│   └── users.html
│
├── database.py
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Установка

Клонировать репозиторий:

```bash
git clone <repository-url>
cd "CallTracker v2.0"
```

Создать виртуальное окружение:

```bash
python3 -m venv .venv
```

Активировать:

```bash
source .venv/bin/activate
```

Установить зависимости:

```bash
pip install -r requirements.txt
```

## 🔐 Настройка `.env`

Создать файл `.env` в корне проекта:

```env
DB_NAME=calltracker
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432

SECRET_KEY=your_secret_key
```

Файл `.env` не должен добавляться в Git.

## 🗄️ PostgreSQL

Создать базу данных:

```sql
CREATE DATABASE calltracker;
```

Основная таблица:

```sql
CREATE TABLE daily_performance (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    plan INTEGER NOT NULL,
    fact INTEGER NOT NULL
);
```

Таблица пользователей:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(20) NOT NULL DEFAULT 'user'
);
```

## ▶️ Запуск

Запустить приложение:

```bash
python main.py
```

После запуска открыть:

```text
http://127.0.0.1:5000
```

## 🔒 Безопасность

* Пароли пользователей хранятся в виде хешей.
* Данные подключения к PostgreSQL хранятся в `.env`.
* `.env` добавлен в `.gitignore`.
* Административные функции защищены ролью `admin`.
* Последнего администратора нельзя удалить или лишить роли администратора.
* Неактивные пользователи не могут войти в систему.

## 🎯 Цель проекта

Проект создан как практическое Python/Flask-приложение для автоматизации учета производительности контакт-центра и изучения разработки веб-приложений с PostgreSQL.

## 👨‍💻 Автор

**Anvar**

Проект разработан в рамках практического изучения Python, Flask, PostgreSQL и веб-разработки.
