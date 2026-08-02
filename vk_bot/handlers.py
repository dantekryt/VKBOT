"""
Обработчик входящих сообщений VK-бота ИрГАУ.
Все запросы теперь идут через AI (ИИ + function calling).
"""
import logging
import threading

from vk_client import send_message, send_message_with_attachment
from ai_handler import ai_reply, get_voice_mode
from voice_handler import generate_voice

logger = logging.getLogger(__name__)


def handle_message(message: dict) -> None:
    peer_id = message.get("peer_id") or message.get("from_id")
    text    = message.get("text", "").strip()
    if not peer_id or not text:
        return

    def run():
        try:
            # Получаем ответ от ИИ
            reply = ai_reply(peer_id, text)
            if not reply:
                return

            # Отправка голосом или текстом в зависимости от режима
            if get_voice_mode(peer_id):
                try:
                    att = generate_voice(peer_id, reply)
                    send_message_with_attachment(peer_id, "", att)
                except Exception as e:
                    logger.error("Голосовое: %s", e)
                    # Fallback на текст если голос не сработал
                    send_message(peer_id, reply)
            else:
                send_message(peer_id, reply)

        except Exception as e:
            logger.exception("Ошибка peer_id=%s: %s", peer_id, e)
            try:
                send_message(peer_id, "❌ Что-то пошло не так. Попробуй ещё раз.")
            except Exception:
                pass

    threading.Thread(target=run, daemon=True).start()
