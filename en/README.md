# 🇬🇧 jev-factcheck

English adaptation of a fact-checking skill for **Jev**, with each verdict tied to a specific excerpt from a specific source.

The idea is simple: the agent does not ask “is this generally true?” It asks **whether this exact source excerpt supports this exact claim**.

```text
claim + verbatim source excerpt
              ↓
             Jev
              ↓
supports / contradicts / says_nothing + confidence
```

## What it is for

Useful for Researcher / analytical agents when you need to:

- fact-check an article, report, or research note;
- verify a technical claim against documentation;
- check a quote or public statement;
- preserve the exact source excerpt behind a conclusion;
- distinguish “the source does not support this” from “the source could not be retrieved”.

## How it works

1. The agent extracts atomic, checkable claims.
2. `fetch_page.py` downloads the source and creates numbered text plus a `.meta.json` sidecar.
3. The agent selects the relevant line ranges.
4. `claims.json` stores `claim`, `source_url`, `source_file`, and `lines`.
5. `check_claims.py` reconstructs the verbatim excerpt and sends the pair to Jev.
6. The result contains the verdict, confidence, latency, token usage, and cost when the provider returns them.

## Repository layout

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

## Installation

Copy this repository / directory into your agent's skills directory. If the install path is non-standard, set:

```bash
export JEV_FACTCHECK_SKILL_DIR=/path/to/jev-factcheck
```

Generic fallback used in `SKILL.md`:

```bash
${HERMES_HOME:-$HOME/.hermes}/skills/jev-factcheck
```

### Provider key

OpenRouter:

```bash
export OPENROUTER_API_KEY=...
```

Default model:

```text
typesafe/jev-1.13
```

`TYPESAFE_API_KEY` is also supported as a fallback. **Never commit `.env` files or API keys to Git.**

## Quick start

```bash
SKILL_DIR=/path/to/jev-factcheck
RUN_DIR=$(mktemp -d /tmp/jev-factcheck.XXXXXX)
mkdir -p "$RUN_DIR/pages"

python3 "$SKILL_DIR/scripts/fetch_page.py" \
  "https://www.python.org/about/" \
  "$RUN_DIR/pages/python.txt"
```

Find the relevant lines and create `claims.json`:

```json
[
  {
    "id": 1,
    "claim": "Python is a programming language",
    "source_url": "https://www.python.org/about/",
    "source_file": "pages/python.txt",
    "lines": [[80, 80]]
  }
]
```

Then run:

```bash
cd "$RUN_DIR"
python3 "$SKILL_DIR/scripts/check_claims.py" claims.json
```

## Security properties

This adaptation:

- allows only `http` / `https` URLs;
- blocks localhost, private, link-local, and reserved IPs;
- validates redirect targets again;
- treats source text and claims as untrusted data;
- keeps unavailable sources separate from `says_nothing`;
- preserves provenance through `source_file + lines`;
- supports `Content-Encoding: gzip`.

## Tests

```bash
python3 tests/test_jev_factcheck.py
```

Reference build: **10/10 tests PASS**.

## Important limitation

Jev is **not an oracle of absolute truth**. It evaluates the relationship between **a specific claim and a specific source excerpt**. Result quality depends on source quality, claim formulation, and whether the selected excerpt is actually relevant. Low-confidence results should be escalated for manual review.

## Licensing

This public build does not add a new license on top of the upstream code. Before redistribution or commercial use, verify the license / permission terms of the upstream version this adaptation was derived from.
