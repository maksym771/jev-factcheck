#!/usr/bin/env python3
"""
fetch_page.py: downloads a public source and stores its text with line numbers.

    python3 fetch_page.py <url> <out.txt>

Also creates <out.txt>.meta.json with status="ok" or status="unavailable".
Only http/https URLs are allowed. localhost, private/link-local/reserved addresses,
and redirects to them are blocked so the fetcher cannot access internal services.
"""

import gzip
import html
import ipaddress
import json
import re
import socket
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (jev-factcheck)"}


def validate_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("only http/https URLs are allowed")
    if not parsed.hostname:
        raise ValueError("URL has no hostname")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed")

    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("local hostnames are not allowed")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"hostname resolution failed: {exc}") from exc

    if not infos:
        raise ValueError("hostname has no IP addresses")

    for info in infos:
        raw_ip = info[4][0].split("%", 1)[0]
        ip = ipaddress.ip_address(raw_ip)
        if not ip.is_global:
            raise ValueError(f"non-public IP address is not allowed: {ip}")
    return parsed


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = urllib.request.build_opener(SafeRedirectHandler())


def get(url, accept=None):
    validate_url(url)
    headers = dict(UA)
    if accept:
        headers["Accept"] = accept
    with OPENER.open(urllib.request.Request(url, headers=headers), timeout=30) as resp:
        final_url = resp.geturl()
        validate_url(final_url)
        body = resp.read()
        content_encoding = (resp.headers.get("Content-Encoding") or "").lower()
        if "gzip" in content_encoding:
            body = gzip.decompress(body)
        return resp.status, body.decode("utf-8", errors="replace"), final_url


def html_to_text(raw):
    raw = re.sub(r"(?is)<(script|style|noscript|svg|template)[^>]*>.*?</\1>", " ", raw)
    main = re.search(r"(?is)<article[^>]*>(.*)</article>", raw) or re.search(r"(?is)<main[^>]*>(.*)</main>", raw)
    if main:
        raw = main.group(1)
    else:
        raw = re.sub(r"(?is)<(nav|header|footer|aside)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr|td|th|section|pre|blockquote|table|ul|ol)>", "\n", raw)
    raw = re.sub(r"(?i)<li[^>]*>", "\n- ", raw)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    return [line for line in lines if line]


def github(url):
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/(issues|pull)/(\d+)", url)
    if match:
        owner, repo, _, num = match.groups()
        _, body, _ = get(f"https://api.github.com/repos/{owner}/{repo}/issues/{num}", "application/vnd.github+json")
        issue = json.loads(body)
        parts = [
            f"# {issue.get('title', '')}",
            f"(issue #{num}, author {issue.get('user', {}).get('login')}, status {issue.get('state')}, created {issue.get('created_at')})",
            issue.get("body") or "",
        ]
        _, body, _ = get(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{num}/comments?per_page=100",
            "application/vnd.github+json",
        )
        for comment in json.loads(body):
            parts += [
                f"--- comment {comment.get('user', {}).get('login')} {comment.get('created_at')}",
                comment.get("body") or "",
            ]
        return "\n".join(parts).splitlines(), "github_api"

    match = re.match(r"https://github\.com/([^/]+)/([^/#?]+)/?$", url)
    if match:
        owner, repo = match.groups()
        _, body, _ = get(f"https://api.github.com/repos/{owner}/{repo}/readme", "application/vnd.github.raw")
        return body.splitlines(), "github_api"
    return None, None


def write_meta(out, payload):
    meta = Path(str(out) + ".meta.json")
    meta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 fetch_page.py <url> <out.txt>")

    url, out = sys.argv[1], Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        validate_url(url)
        lines, source_type = github(url)
        final_url = url
        http_status = 200
        if lines is None:
            http_status, raw, final_url = get(url)
            lines = html_to_text(raw)
            source_type = "html"
    except Exception as exc:  # noqa: BLE001
        out.write_text("", encoding="utf-8")
        write_meta(
            out,
            {
                "status": "unavailable",
                "source_url": url,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        print(f"Could not open: {url} ({type(exc).__name__}: {exc}). Source marked unavailable.")
        raise SystemExit(2) from exc

    lines = [line.rstrip() for line in lines]
    out.write_text("\n".join(f"{i:4d}| {line}" for i, line in enumerate(lines, 1)) + "\n", encoding="utf-8")
    words = sum(len(line.split()) for line in lines)
    write_meta(
        out,
        {
            "status": "ok",
            "source_url": url,
            "final_url": final_url,
            "http_status": http_status,
            "source_type": source_type,
            "lines": len(lines),
            "words": words,
        },
    )

    print(f"Saved: {out} ({len(lines)} lines, {words} words). Preview:")
    for i, line in enumerate(lines[:6], 1):
        print(f"{i:4d}| {line[:160]}")


if __name__ == "__main__":
    main()
