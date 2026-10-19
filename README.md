# jev-factcheck

Source-grounded fact-checking skill for AI agents using **Jev**. The agent checks whether a **specific source excerpt supports a specific claim**, while preserving provenance down to the source file and line ranges.

```text
claim + verbatim source excerpt
              ↓
             Jev
              ↓
supports / contradicts / says_nothing + confidence
```

## Why this exists

LLMs can answer from memory or general knowledge, but that is not the same as checking what a cited source actually says. `jev-factcheck` narrows the task to one auditable question:

> Does this exact source excerpt support this exact claim?

That makes it useful for research agents, technical documentation checks, article review, quote verification, and pre-publication fact-checking.

## Installation

Copy the contents of `en/` into your agent's skill directory as `jev-factcheck`.

The English edition includes `SKILL.md`, `ADAPTATION-NOTES.md`, supporting scripts, and tests.

## How it works

1. The agent extracts atomic, checkable claims.
2. `fetch_page.py` downloads a source and stores numbered text plus metadata.
3. The agent selects the relevant line ranges.
4. `claims.json` stores `claim`, `source_url`, `source_file`, and `lines`.
5. `check_claims.py` reconstructs the verbatim excerpt and sends the claim/excerpt pair to Jev.
6. The result reports the Jev verdict, confidence, and provider usage data when available.

## Provider

The preferred backend is OpenRouter:

```bash
export OPENROUTER_API_KEY=...
```

Default model:

```text
typesafe/jev-1.13
```

`TYPESAFE_API_KEY` is also supported as a fallback.

**Never commit `.env` files or API keys.**

## Safety and provenance

The English edition includes:

- provenance through `source_file + lines`;
- no direct free-form `section` injection;
- separate handling for unavailable sources;
- prompt-injection guidance for fetched content and claims;
- `http` / `https` only;
- localhost, private, link-local, and reserved IP blocking;
- redirect target validation;
- `Content-Encoding: gzip` support.

## Verification

Reference build: **2026-10-14**

The English edition passes the offline suite:

```text
10/10 tests PASS
```

A real end-to-end smoke test was also validated through OpenRouter with `typesafe/jev-1.13`.

## Important limitation

Jev is **not an oracle of absolute truth**. It evaluates the relationship between one claim and one source excerpt. Result quality still depends on source quality, claim formulation, and excerpt selection. Low-confidence results should be escalated for manual review.

## Licensing

No new license is added by this repository.
