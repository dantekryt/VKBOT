"""
Генерация голосовых сообщений через gTTS + конвертация в OGG Opus.
"""
import os
import subprocess
import tempfile
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)


def text_to_ogg(text: str) -> str:
    """
    Конвертирует текст в OGG Opus файл.
    Возвращает путь к временному файлу (нужно удалить после использования).
    """
    # Генерируем MP3 через gTTS
    mp3_fd, mp3_path = tempfile.mkstemp(suffix=".mp3")
    ogg_fd, ogg_path = tempfile.mkstemp(suffix=".ogg")
    os.close(mp3_fd)
    os.close(ogg_fd)

    try:
        tts = gTTS(text=text, lang="ru", slow=False)
        tts.save(mp3_path)

        # Конвертируем MP3 → OGG Opus через ffmpeg
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", mp3_path,
                "-c:a", "libopus",
                "-b:a", "64k",
                "-vbr", "on",
                "-compression_level", "10",
                ogg_path,
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning("ffmpeg вернул код %d: %s", result.returncode, result.stderr.decode())
            raise RuntimeError("Ошибка конвертации аудио")

        return ogg_path
    finally:
        try:
            os.remove(mp3_path)
        except OSError:
            pass


def generate_voice(peer_id: int, text: str) -> str:
    """
    Генерирует голосовое сообщение и загружает в ВКонтакте.
    Возвращает attachment-строку.
    """
    from vk_client import upload_voice

    ogg_path = text_to_ogg(text)
    try:
        attachment = upload_voice(peer_id, ogg_path)
        return attachment
    finally:
        try:
            os.remove(ogg_path)
        except OSError:
            pass
