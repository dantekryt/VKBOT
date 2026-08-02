"""
Советы по учёбе и полезные ссылки.
"""
import random

STUDY_TIPS = [
    "📌 Делай конспекты своими словами — так информация запоминается в 2 раза лучше, чем дословное переписывание.",
    "📌 Используй метод Помодоро: 25 минут работы → 5 минут отдыха. После 4 циклов — длинный перерыв 15-30 минут.",
    "📌 Повторяй материал через 1 день, 3 дня, 7 дней и 21 день после изучения — это кривая Эббингауза, она реально работает.",
    "📌 Решай задачи вслух или объясняй тему воображаемому собеседнику. Если не можешь объяснить — не понял.",
    "📌 Учи в одном и том же месте: мозг начнёт ассоциировать это место с концентрацией.",
    "📌 За 30 минут до сна отложи телефон. Мозг во сне закрепляет выученное — не мешай ему.",
    "📌 Делай краткие планы перед каждой учебной сессией: 3-5 конкретных задач, не «поучить математику», а «решить задачи 5.1–5.8».",
    "📌 Не читай учебник пассивно — задавай вопросы к каждому абзацу: «Зачем это нужно? Где это применяется?»",
    "📌 Группируй темы по смыслу, а не по датам. Связи между темами помогают лучше, чем зубрёжка по порядку.",
    "📌 Высыпайся перед экзаменом — ночное повторение материала менее эффективно, чем 7-8 часов сна.",
    "📌 Сразу после лекции трать 5 минут на восстановление конспекта по памяти. Это моментально укрепляет запоминание.",
    "📌 Если застрял на задаче больше 20 минут — сделай перерыв. Подсознание продолжит работу, пока ты отдыхаешь.",
]

USEFUL_LINKS = {
    "🎓 Учёба и наука": [
        ("Научная электронная библиотека eLibrary", "https://elibrary.ru"),
        ("КиберЛенинка — открытая научная библиотека", "https://cyberleninka.ru"),
        ("Гугл Академия — поиск научных статей", "https://scholar.google.com"),
        ("Открытое образование — онлайн-курсы российских вузов", "https://openedu.ru"),
    ],
    "💻 Информатика и программирование": [
        ("Stepik — бесплатные курсы по программированию", "https://stepik.org"),
        ("Python для начинающих", "https://pythontutor.ru"),
        ("Habr — статьи по IT и технологиям", "https://habr.com"),
        ("GeeksforGeeks — алгоритмы и структуры данных", "https://www.geeksforgeeks.org"),
        ("Документация Python на русском", "https://docs-python.ru"),
    ],
    "📊 Экономика и менеджмент": [
        ("Экономический словарь", "https://dic.academic.ru/contents.nsf/econ_dict/"),
        ("РБК — деловые новости", "https://www.rbc.ru"),
        ("Coursera — курсы по экономике и менеджменту", "https://www.coursera.org"),
        ("Harvard Business Review Russia", "https://hbr-russia.ru"),
    ],
    "🔬 Общие ресурсы": [
        ("Академик — энциклопедии и словари", "https://dic.academic.ru"),
        ("Khan Academy — бесплатное образование", "https://ru.khanacademy.org"),
        ("Лекториум — видеолекции российских вузов", "https://www.lectorium.ru"),
        ("Wolframalpha — математические вычисления", "https://www.wolframalpha.com"),
    ],
}


def get_random_tip() -> str:
    return random.choice(STUDY_TIPS)


def get_all_tips() -> str:
    tips = random.sample(STUDY_TIPS, min(5, len(STUDY_TIPS)))
    return "💡 Советы по учёбе:\n\n" + "\n\n".join(tips)


def get_links(category: str | None = None) -> str:
    if category:
        cat_lower = category.lower()
        for cat_name, links in USEFUL_LINKS.items():
            if any(w in cat_name.lower() for w in cat_lower.split()):
                lines = [f"{cat_name}:"]
                for name, url in links:
                    lines.append(f"  • {name}\n    {url}")
                return "\n".join(lines)

    # Все ссылки
    lines = ["📚 Полезные ресурсы для учёбы:\n"]
    for cat_name, links in USEFUL_LINKS.items():
        lines.append(cat_name)
        for name, url in links:
            lines.append(f"  • {name}\n    {url}")
        lines.append("")
    return "\n".join(lines).strip()
