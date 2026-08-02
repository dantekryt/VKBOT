"""
VK API wrapper — всё взаимодействие с ВКонтакте через этот модуль.
"""
import os
import random
import requests
import logging

logger = logging.getLogger(__name__)

VK_TOKEN = os.environ.get("VK_TOKEN", "")
VK_API_VERSION = "5.199"
VK_API_BASE = "https://api.vk.com/method"


def _call(method: str, **params) -> dict:
    params.update({"access_token": VK_TOKEN, "v": VK_API_VERSION})
    resp = requests.post(f"{VK_API_BASE}/{method}", data=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        logger.error("VK API error %s: %s", method, data["error"])
    return data.get("response", {})


def send_message(peer_id: int, text: str) -> None:
    """Отправить текстовое сообщение."""
    _call(
        "messages.send",
        peer_id=peer_id,
        message=text,
        random_id=random.randint(0, 2**31),
    )


def send_message_with_attachment(peer_id: int, text: str, attachment: str) -> None:
    """Отправить сообщение с вложением (например, голосовым)."""
    _call(
        "messages.send",
        peer_id=peer_id,
        message=text,
        attachment=attachment,
        random_id=random.randint(0, 2**31),
    )


def get_voice_upload_server(peer_id: int) -> str:
    """Получить URL для загрузки голосового сообщения."""
    result = _call(
        "docs.getMessagesUploadServer",
        type="audio_message",
        peer_id=peer_id,
    )
    return result.get("upload_url", "")


def save_voice_doc(file_data: str) -> str:
    """Сохранить загруженный голосовой файл и вернуть attachment-строку."""
    result = _call("docs.save", file=file_data)
    audio_msg = result.get("audio_message") or {}
    if not audio_msg:
        # Fallback: doc type
        doc = result.get("doc") or {}
        owner_id = doc.get("owner_id")
        doc_id = doc.get("id")
        return f"doc{owner_id}_{doc_id}"
    owner_id = audio_msg.get("owner_id")
    doc_id = audio_msg.get("id")
    return f"doc{owner_id}_{doc_id}"


def upload_voice(peer_id: int, ogg_path: str) -> str:
    """Загрузить OGG-файл как голосовое сообщение. Возвращает attachment-строку."""
    upload_url = get_voice_upload_server(peer_id)
    if not upload_url:
        raise RuntimeError("Не удалось получить upload URL")
    with open(ogg_path, "rb") as f:
        resp = requests.post(upload_url, files={"file": ("voice.ogg", f, "audio/ogg")}, timeout=30)
    resp.raise_for_status()
    file_data = resp.json().get("file", "")
    return save_voice_doc(file_data)
