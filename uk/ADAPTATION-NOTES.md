# jev-factcheck — українська адаптація

Дата еталонної збірки: 2026-10-14

Ця версія підготовлена для повторного встановлення та публічного використання без прив’язки до конкретного сервера, користувача чи локальної структури каталогів.

## Що змінено

- Українська мова в `SKILL.md`, CLI-виводі, помилках і verdict labels.
- Jev prompt підтримує українську, польську, російську та англійську.
- Додана явна інструкція ігнорувати prompt injection у `claim`/джерелі.
- OpenRouter — пріоритетний backend (`OPENROUTER_API_KEY`, `typesafe/jev-1.13`); TypeSafe підтримується як fallback.
- Прибрані жорстко задані локальні каталоги. Шлях skill задається через `JEV_FACTCHECK_SKILL_DIR`; generic fallback — `${HERMES_HOME:-$HOME/.hermes}/skills/jev-factcheck`.
- Робочий каталог за замовчуванням: `/tmp/jev-factcheck`.
- `fetch_page.py` створює parent directory до fetch.
- `fetch_page.py` декодує `Content-Encoding: gzip` перед UTF-8 decode.
- `fetch_page.py` пише `.meta.json` зі статусом `ok` / `unavailable`.
- Недоступні джерела не надсилаються у Jev.
- Пряме поле `section` заборонене; provenance зберігається через `source_file + lines`.
- Доданий SSRF-захист: лише http/https, блок localhost/private/link-local/reserved IP та небезпечних redirect targets.
- `excerpt.py` логічно не змінений.
- Додані офлайн unit tests для provenance, unavailable-source, multilingual prompt, URL safety і gzip decode.

## Верифікація

- Офлайн test suite: **10/10 PASS**.
- Реальний gzip-fetch перевірений на публічній HTTPS-сторінці: HTTP 200, `status=ok`, текст коректно декодується.
- Реальний Jev path перевірений через OpenRouter і `typesafe/jev-1.13`: structured verdict + confidence повертаються коректно.

## Перед встановленням

1. Скопіюй каталог skill у дозволену директорію skills твого агента.
2. За потреби встанови `JEV_FACTCHECK_SKILL_DIR`.
3. Передай `OPENROUTER_API_KEY` або `TYPESAFE_API_KEY` через environment / захищений `.env`; не коміть секрети.
4. Запусти офлайн tests.
5. Виконай короткий smoke test на власному джерелі.
