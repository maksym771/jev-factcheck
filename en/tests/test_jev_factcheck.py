import gzip
import importlib.util
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


excerpt = load_module("excerpt", SCRIPTS / "excerpt.py")
import sys
sys.modules["excerpt"] = excerpt
check_claims = load_module("check_claims", SCRIPTS / "check_claims.py")
fetch_page = load_module("fetch_page", SCRIPTS / "fetch_page.py")


class ExcerptTests(unittest.TestCase):
    def test_read_lines_preserves_exact_text(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "page.txt"
            path.write_text("   1| Alpha\n   2| Beta | pipe\n   3| Gamma\n", encoding="utf-8")
            self.assertEqual(excerpt.read_lines(path, [[1, 2]]), "Alpha\nBeta | pipe")


class CheckClaimsTests(unittest.TestCase):
    def make_source(self, root, meta_status="ok"):
        pages = root / "pages"
        pages.mkdir()
        src = pages / "1.txt"
        src.write_text("   1| Kyiv is the capital of Ukraine.\n", encoding="utf-8")
        Path(str(src) + ".meta.json").write_text(json.dumps({"status": meta_status}), encoding="utf-8")
        return src

    def test_multilingual_and_injection_guard_is_in_question(self):
        text = check_claims.QUESTIONS["relation"]["instructions"]
        self.assertIn("Ukrainian", text)
        self.assertIn("Polish", text)
        self.assertIn("untrusted data", text)

    def test_direct_section_is_rejected_without_calling_jev(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(check_claims, "call_jev") as call:
            row = check_claims.check({"id": 1, "claim": "x", "section": "y"}, Path(td))
            self.assertEqual(row["relation"], "invalid_input")
            call.assert_not_called()

    def test_unavailable_source_is_not_sent_to_jev(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(check_claims, "call_jev") as call:
            root = Path(td)
            self.make_source(root, "unavailable")
            item = {"id": 1, "claim": "x", "source_file": "pages/1.txt", "lines": [[1, 1]]}
            row = check_claims.check(item, root)
            self.assertEqual(row["relation"], "source_unavailable")
            self.assertEqual(row["action"], "manual review")
            call.assert_not_called()

    def test_valid_source_calls_jev_and_returns_english_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_source(root)
            item = {"id": 1, "claim": "Kyiv is the capital of Ukraine", "source_file": "pages/1.txt", "lines": [[1, 1]]}
            fake = {"answers": {"relation": {"choice": "supports", "confidence": 0.97}}, "usage": {"input_tokens": 10, "cost": 0.000001}}
            with mock.patch.object(check_claims, "call_jev", return_value=fake):
                row = check_claims.check(item, root)
            self.assertEqual(row["verdict"], "supports")
            self.assertEqual(row["action"], "automatic")
            self.assertIn("Kyiv", row["section"])


class FetchSafetyTests(unittest.TestCase):
    def fake_dns(self, ip):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))]

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(ValueError):
            fetch_page.validate_url("file:///etc/passwd")

    def test_rejects_localhost(self):
        with self.assertRaises(ValueError):
            fetch_page.validate_url("http://localhost:8080/")

    def test_rejects_private_ip(self):
        with mock.patch.object(fetch_page.socket, "getaddrinfo", return_value=self.fake_dns("10.0.0.5")):
            with self.assertRaises(ValueError):
                fetch_page.validate_url("https://internal.example/")

    def test_accepts_public_ip(self):
        with mock.patch.object(fetch_page.socket, "getaddrinfo", return_value=self.fake_dns("93.184.216.34")):
            parsed = fetch_page.validate_url("https://example.com/")
            self.assertEqual(parsed.hostname, "example.com")

    def test_get_decodes_gzip_content_encoding(self):
        payload = "Python programming language".encode("utf-8")

        class FakeResponse:
            status = 200
            headers = {"Content-Encoding": "gzip"}

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https://example.com/"

            def read(self):
                return gzip.compress(payload)

        class FakeOpener:
            def open(self, request, timeout=30):
                return FakeResponse()

        with mock.patch.object(fetch_page, "validate_url"), mock.patch.object(fetch_page, "OPENER", FakeOpener()):
            status, body, final_url = fetch_page.get("https://example.com/")

        self.assertEqual(status, 200)
        self.assertEqual(body, "Python programming language")
        self.assertEqual(final_url, "https://example.com/")


if __name__ == "__main__":
    unittest.main()
