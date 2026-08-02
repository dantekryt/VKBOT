import os
import json
import logging
from openai import OpenAI  # DeepSeek совместим с OpenAI SDK

from schedule_parser import (
    DIRECTIONS, DAY_ALIASES, DAYS_RU,
    list_directions, get_schedule, get_free_windows,
    search_by_teacher, get_num_groups,
)
from study_tips import get_random_tip, get_all_tips, get_links

logger = logging.getLogger(__name__)

# ─── Клиент ───────────────────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.environ["MISTRAL_API_KEY"],
    base_url="https://api.mistral.ai/v1",
)

MAX_HISTORY = 20          # сколько сообщений помним (пар user+assistant)
MODEL       = "mistral-small-latest"



_state: dict[int, dict] = {}


def _s(peer_id: int) -> dict:
    if peer_id not in _state:
        _state[peer_id] = {"direction": None, "course": None, "group": None,
                           "voice": False, "history": []}
    return _state[peer_id]


def get_voice_mode(peer_id: int) -> bool:
    return _s(peer_id)["voice"]


# Описание инструментов
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": (
                "Возвращает расписание для указанного направления, курса и группы. "
                "period: 'today'|'tomorrow'|'week' или название дня ('ПОНЕДЕЛЬНИК', 'ВТОРНИК', …). "
                "Если direction/course/group не переданы — берёт из профиля пользователя."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "description": "Код направления: 09.03.03 / 38.05.01 / 38.03.02 / 38.03.01"},
                    "course":    {"type": "integer", "description": "Номер курса (1–5)"},
                    "group":     {"type": "integer", "description": "Номер группы (1 или 2)"},
                    "period":    {"type": "string",  "description": "today / tomorrow / week / ПОНЕДЕЛЬНИК / ВТОРНИК / …"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_free_windows",
            "description": "Возвращает свободные окна (промежутки между парами).",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string"},
                    "course":    {"type": "integer"},
                    "group":     {"type": "integer"},
                    "period":    {"type": "string", "description": "today / tomorrow / week"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_teacher",
            "description": "Ищет все пары указанного преподавателя во всех направлениях.",
            "parameters": {
                "type": "object",
                "properties": {
                    "surname": {"type": "string", "description": "Фамилия преподавателя"},
                },
                "required": ["surname"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directions",
            "description": "Возвращает список всех доступных направлений подготовки.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_user_prefs",
            "description": (
                "Сохраняет профиль пользователя: направление, курс, группа. "
                "Передавай только те поля, которые нужно изменить."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string"},
                    "course":    {"type": "integer"},
                    "group":     {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "switch_mode",
            "description": "Переключает режим ответов: 'voice' — голосовые сообщения, 'text' — текстовые.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["voice", "text"]},
                },
                "required": ["mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_study_tips",
            "description": "Возвращает советы по учёбе.",
            "parameters": {
                "type": "object",
                "properties": {
                    "many": {"type": "boolean", "description": "true — несколько советов, false — один"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_links",
            "description": "Возвращает полезные учебные ссылки. category: 'информатика' / 'экономика' / пусто (все).",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                },
                "required": [],
            },
        },
    },
]


# Выполнение инструментов

def _resolve(peer_id: int, d, c, g):
    st = _s(peer_id)
    direction = d or st["direction"]
    course    = c or st["course"]
    group     = g or st["group"]

    # Для одногрупповых направлений группа всегда 1
    if direction and course:
        ng = get_num_groups(direction, course)
        if ng == 1:
            group = 1

    return direction, course, group


def _call_tool(peer_id: int, name: str, args: dict) -> str:
    st = _s(peer_id)

    if name == "get_schedule":
        direction, course, group = _resolve(
            peer_id, args.get("direction"), args.get("course"), args.get("group"))
        period = args.get("period", "week")

        if not direction:
            return list_directions() + "\nСкажи мне своё направление, и я покажу расписание."
        if not course:
            return "Укажи свой курс (1, 2, 3…)"
        if not group:
            return "Укажи свою группу (1 или 2)."

        if args.get("direction"):
            st["direction"] = direction
        if args.get("course"):
            st["course"] = course
        if args.get("group"):
            st["group"] = group

        return get_schedule(direction, course, group, period)

    elif name == "get_free_windows":
        direction, course, group = _resolve(
            peer_id, args.get("direction"), args.get("course"), args.get("group"))
        period = args.get("period", "today")

        if not direction:
            return list_directions() + "\nСкажи мне своё направление."
        if not course:
            return "Укажи курс."
        if not group:
            return "Укажи группу."

        return get_free_windows(direction, course, group, period)

    elif name == "search_by_teacher":
        return search_by_teacher(args["surname"])

    elif name == "list_directions":
        return list_directions()

    elif name == "set_user_prefs":
        if "direction" in args and args["direction"]:
            st["direction"] = args["direction"]
        if "course" in args and args["course"]:
            st["course"] = int(args["course"])
        if "group" in args and args["group"]:
            st["group"] = int(args["group"])

        d = st["direction"] or "не задано"
        dname = DIRECTIONS.get(d, {}).get("name", "") if d != "не задано" else ""
        return (f"✅ Профиль сохранён!\n"
                f"  Направление: {d} {dname}\n"
                f"  Курс: {st['course'] or 'не задан'}\n"
                f"  Группа: {st['group'] or 'не задана'}")

    elif name == "switch_mode":
        mode = args.get("mode", "text")
        st["voice"] = (mode == "voice")
        if st["voice"]:
            return "🎤 Голосовой режим включён. Теперь все ответы — голосовыми сообщениями."
        else:
            return "💬 Текстовый режим включён."

    elif name == "get_study_tips":
        if args.get("many"):
            return get_all_tips()
        return get_random_tip()

    elif name == "get_links":
        return get_links(args.get("category"))

    return f"[неизвестный инструмент: {name}]"


# Системный промпт

def _system_prompt(peer_id: int) -> str:
    st = _s(peer_id)
    d  = st["direction"]
    dname = DIRECTIONS.get(d, {}).get("name", "") if d else ""
    return f"""Ты — виртуальный помощник студентов ИрГАУ (Иркутский государственный аграрный университет).
Тебя зовут «ИрГАУ-бот».

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ (уже сохранён):
  Направление: {d or 'не задано'} {dname}
  Курс: {st['course'] or 'не задан'}
  Группа: {st['group'] or 'не задана'}
  Режим ответов: {'голосовой 🎤' if st['voice'] else 'текстовый 💬'}

ТВОИ ЗАДАЧИ — только:
1. Расписание пар (по дням, неделе, конкретным дням) — через инструмент get_schedule
2. Свободные окна между парами — через get_free_windows
3. Поиск пар по преподавателю — через search_by_teacher
4. Сохранение профиля пользователя (направление, курс, группа) — через set_user_prefs
5. Советы по учёбе и полезные ссылки — через get_study_tips / get_links
6. Переключение режима голос/текст — через switch_mode

ПРАВИЛА:
- Отвечай ТОЛЬКО на вопросы об учёбе, расписании, учебном процессе ИрГАУ.
- На вопросы не по теме отвечай: «Я помогаю только с расписанием и учебными вопросами ИрГАУ 🎓»
- Всегда используй инструменты для данных о расписании — никогда не выдумывай расписание сам.
- Если профиль не заполнен — спроси направление и курс, потом вызови set_user_prefs.
- Общайся дружелюбно и по-русски. Отвечай кратко и по делу.
- Когда пользователь говорит «голосовой режим», «хочу голос», «включи голос» и т.п. — вызови switch_mode(mode='voice').
- Когда пользователь говорит «текстовый», «отключи голос», «пиши текстом» — вызови switch_mode(mode='text').
- Если в профиле уже есть направление/курс/группа — используй их автоматически без лишних вопросов.

Отвечай на русском языке. Будь как умный старшекурсник — помогаешь, но по делу."""


# ─── Главная функция ──────────────────────────────────────────────────────────

def ai_reply(peer_id: int, user_text: str) -> str:
    """
    Обрабатывает сообщение пользователя через GPT с function calling.
    Возвращает текст ответа (отправку голоса делает handlers.py).
    """
    st = _s(peer_id)
    history: list[dict] = st["history"]

    # Добавляем сообщение пользователя
    history.append({"role": "user", "content": user_text})

    # Обрезаем историю (MAX_HISTORY пар = MAX_HISTORY*2 сообщений)
    if len(history) > MAX_HISTORY * 2:
        history[:] = history[-(MAX_HISTORY * 2):]

    messages = [{"role": "system", "content": _system_prompt(peer_id)}] + history

    # Цикл function calling (GPT может вызвать несколько инструментов подряд)
    for _ in range(6):  # максимум 6 итераций
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1000,
            temperature=0.7,
        )

        choice = resp.choices[0]
        msg = choice.message

        # Если GPT хочет вызвать инструменты
        if choice.finish_reason == "tool_calls" and msg.tool_calls:
            messages.append(msg)  # добавляем assistant-сообщение с tool_calls

            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                logger.info("Tool call: %s(%s)", tc.function.name, args)
                result = _call_tool(peer_id, tc.function.name, args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            continue  # следующая итерация — GPT формирует финальный ответ

        # Финальный текстовый ответ
        reply = (msg.content or "").strip()
        if reply:
            history.append({"role": "assistant", "content": reply})
        return reply

    return "❌ Не смог обработать запрос. Попробуй переформулировать."
