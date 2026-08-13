# pref-bot

Telegram-бот для обучения игре в преферанс:
- короткие уроки;
- разбор игровых ситуаций;
- случайная ситуация;
- мини-квиз с объяснением логики.

## 1) Установка (Windows, PowerShell)

Перейди в папку проекта:

```powershell
cd "C:\Users\easym\OneDrive\Рабочий стол\bot\pref-bot"
```

Создай и активируй виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Установи зависимости:

```powershell
pip install -r requirements.txt
```

## 2) Токен бота

1. Создай бота у [@BotFather](https://t.me/BotFather).
2. Скопируй `.env.example` в `.env` и вставь токен:

```powershell
Copy-Item .env.example .env
notepad .env
```

В файле `.env` должно быть:

```
TELEGRAM_BOT_TOKEN=СЮДА_ТОКЕН
```

Файл `.env` не попадает в Git — токен остаётся только на твоём компьютере.

## 3) Запуск

```powershell
python bot.py
```

Если всё ок, в консоли появится `Bot is running.`  
Дальше открой бота в Telegram и нажми `/start`.

## Структура

- `bot.py` — логика бота и меню;
- `content/lessons.json` — уроки;
- `content/situations.json` — игровые ситуации.

## Как добавлять новые ситуации

Добавляй объекты в `content/situations.json` в формате:

```json
{
  "id": "sit-6",
  "title": "Короткий заголовок",
  "text": "Описание ситуации, что делать и почему."
}
```
