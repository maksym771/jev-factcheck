# jev-factcheck — English adaptation

Reference build date: 2026-10-14

This version is prepared for repeat installation and public use without tying it to a specific server, user, or local directory layout.

## Changes in this adaptation

- English language in `SKILL.md`, CLI output, errors, and verdict labels.
- The Jev prompt supports Ukrainian, Polish, Russian, and English claims / excerpts.
- Explicit prompt-injection defense for `claim` and source content.
- OpenRouter is the preferred backend (`OPENROUTER_API_KEY`, `typesafe/jev-1.13`); TypeSafe is supported as a fallback.
- Removed hard-coded local paths. The skill path can be provided with `JEV_FACTCHECK_SKILL_DIR`; generic fallback is `${HERMES_HOME:-$HOME/.hermes}/skills/jev-factcheck`.
- Default work directory is `/tmp/jev-factcheck`.
- `fetch_page.py` creates the parent directory before fetching.
- `fetch_page.py` decodes `Content-Encoding: gzip` before UTF-8 decoding.
- `fetch_page.py` writes `.meta.json` with `ok` / `unavailable` status.
- Unavailable sources are not sent to Jev.
- Direct `section` input is rejected; provenance is preserved through `source_file + lines`.
- SSRF defense: only http/https, with localhost/private/link-local/reserved IPs and unsafe redirect targets blocked.
- `excerpt.py` behavior is unchanged.
- Offline unit tests cover provenance, unavailable sources, multilingual prompt behavior, URL safety, and gzip decoding.

## Verification

- Offline test suite: **10/10 PASS**.
- The gzip-fix is covered by a regression test that simulates a compressed HTTP response.
- The same implementation path has been validated against OpenRouter + `typesafe/jev-1.13` in the corresponding reference adaptation.

## Before installation

1. Copy the skill directory into an allowed skills directory for your agent.
2. Set `JEV_FACTCHECK_SKILL_DIR` if needed.
3. Provide `OPENROUTER_API_KEY` or `TYPESAFE_API_KEY` through the environment / protected `.env`; never commit secrets.
4. Run the offline tests.
5. Run a short smoke test against a source you control or trust.
