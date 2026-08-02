"""
Основной Flask-сервер для VK Callback API.

Установите переменные окружения:
  VK_TOKEN               — токен группы ВКонтакте
  VK_CONFIRMATION_STRING — строка подтверждения Callback API
  VK_SECRET              — секретный ключ Callback API (опционально)

Укажите в настройках ВКонтакте (Управление группой → Работа с API → Callback API):
  URL сервера: https://<ваш-replit-домен>/callback
"""
import os
import json
import logging
from flask import Flask, request, jsonify, Response
from handlers import handle_message

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

VK_CONFIRMATION_STRING = os.environ.get("VK_CONFIRMATION_STRING", "")
VK_SECRET = os.environ.get("VK_SECRET", "")


@app.route("/", methods=["GET"])
def index():
    return "✅ VK Bot (09.03.03 ИрГАУ) работает!", 200


@app.route("/callback", methods=["GET", "POST"])
def callback():
    if request.method == "GET":
        return "VK Callback endpoint готов", 200

    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        return "ok", 200

    event_type = data.get("type", "")
    logger.info("VK event: %s", event_type)

    # Шаг 1: подтверждение сервера
    if event_type == "confirmation":
        if not VK_CONFIRMATION_STRING:
            logger.error("VK_CONFIRMATION_STRING не задан!")
            return "error", 500
        return VK_CONFIRMATION_STRING, 200

    # Проверка секретного ключа (если задан)
    if VK_SECRET and data.get("secret") != VK_SECRET:
        logger.warning("Неверный secret key")
        return "forbidden", 403

    # Шаг 2: входящее сообщение
    if event_type == "message_new":
        obj = data.get("object", {})
        message = obj.get("message", obj)  # API v5.103+
        handle_message(message)

    # VK ждёт строку "ok" в ответ на любое событие
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info("Запуск VK Bot на порту %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
