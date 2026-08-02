# ИрГАУ VK Bot

VK Callback API бот с расписанием, AI-помощником на Mistral, голосовыми ответами и советами по учёбе.

## Файлы

- `vk_bot/app.py` — Flask webhook для VK Callback API
- `vk_bot/handlers.py` — обработка входящих сообщений
- `vk_bot/ai_handler.py` — AI-диалог и function calling
- `vk_bot/schedule_parser.py` — чтение Excel-расписаний
- `vk_bot/vk_client.py` — запросы к VK API
- `vk_bot/voice_handler.py` — генерация OGG Opus через gTTS и ffmpeg
- `vk_bot/study_tips.py` — советы и полезные ссылки
- `vk_bot/schedules/` — Excel-файлы расписаний

## Переменные окружения

- `VK_TOKEN` — токен группы VK
- `VK_CONFIRMATION_STRING` — строка подтверждения Callback API
- `MISTRAL_API_KEY` — API-ключ Mistral AI
- `VK_SECRET` — необязательный секрет Callback API

Порт `8000` или значение переменной `PORT`.
