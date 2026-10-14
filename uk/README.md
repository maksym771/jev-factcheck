# 🇺🇦 jev-factcheck

Українська адаптація skill для фактчекінгу тверджень через **Jev** з прив’язкою до конкретного фрагмента джерела.

Ідея: агент перевіряє не «чи правда це взагалі», а **чи підтверджує конкретний фрагмент конкретного джерела конкретну тезу**.

```text
теза + дослівний фрагмент джерела
              ↓
             Jev
              ↓
supports / contradicts / says_nothing + confidence
```

## Для чого

Підходить для Researcher/аналітичних агентів, коли треба:

- перевірити факти у статті, звіті або дослідженні;
- звірити технічне твердження з документацією;
- перевірити цитату або заяву;
- зафіксувати, який саме фрагмент джерела підтримує висновок;
- відокремити «джерело не підтверджує» від «джерело недоступне».

## Як працює

1. Агент виділяє перевірювані тези.
2. `fetch_page.py` завантажує джерело та створює нумерований текст + `.meta.json`.
3. Агент вибирає релевантні рядки.
4. У `claims.json` зберігаються `claim`, `source_url`, `source_file`, `lines`.
5. `check_claims.py` формує дослівний excerpt і відправляє пару в Jev.
6. Результат містить verdict, confidence, час, токени та вартість (коли провайдер їх повертає).

## Структура

```text
.
├── README.md
├── SKILL.md
├── ADAPTATION-NOTES.md
├── scripts/
│   ├── check_claims.py
│   ├── fetch_page.py
│   └── excerpt.py
└── tests/
    └── test_jev_factcheck.py
```

## Встановлення

Скопіюй репозиторій/каталог у директорію skills твого агента. Для нестандартного шляху задай:

```bash
export JEV_FACTCHECK_SKILL_DIR=/path/to/jev-factcheck
```

Generic fallback у `SKILL.md`:

```bash
${HERMES_HOME:-$HOME/.hermes}/skills/jev-factcheck
```

### Ключ провайдера

OpenRouter:

```bash
export OPENROUTER_API_KEY=...
```

За замовчуванням використовується модель:

```text
typesafe/jev-1.13
```

Також підтримується `TYPESAFE_API_KEY` як fallback. **Не коміть `.env` або API-ключі в Git.**

## Швидкий запуск

```bash
SKILL_DIR=/path/to/jev-factcheck
RUN_DIR=$(mktemp -d /tmp/jev-factcheck.XXXXXX)
mkdir -p "$RUN_DIR/pages"

python3 "$SKILL_DIR/scripts/fetch_page.py" \
  "https://www.python.org/about/" \
  "$RUN_DIR/pages/python.txt"
```

Знайди потрібні рядки, створи `claims.json`:

```json
[
  {
    "id": 1,
    "claim": "Python є мовою програмування",
    "source_url": "https://www.python.org/about/",
    "source_file": "pages/python.txt",
    "lines": [[80, 80]]
  }
]
```

Потім:

```bash
cd "$RUN_DIR"
python3 "$SKILL_DIR/scripts/check_claims.py" claims.json
```

## Безпека

У цій адаптації:

- URL дозволені лише через `http` / `https`;
- блокуються localhost, private, link-local і reserved IP;
- redirect targets повторно перевіряються;
- вміст джерела та claim вважаються недовіреними даними;
- недоступне джерело не перетворюється на `says_nothing`;
- provenance зберігається через `source_file + lines`;
- підтримується `Content-Encoding: gzip`.

## Тести

```bash
python3 tests/test_jev_factcheck.py
```

Еталонна збірка: **10/10 tests PASS**.

## Важливе обмеження

Jev не є «арбітром абсолютної істини». Він оцінює відповідність **конкретної тези конкретному фрагменту джерела**. Якість результату залежить від якості джерела, правильності claim і релевантності вибраного excerpt. Низький confidence треба віддавати на ручну перевірку.

## Ліцензування

Ця публічна збірка не додає нову ліцензію поверх upstream-коду. Перед повторним розповсюдженням або комерційним використанням перевір умови ліцензії/дозволу upstream-версії, з якої зроблена адаптація.
