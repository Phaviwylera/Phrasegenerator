import unittest
from unittest.mock import patch

from app import app, generate_phrase, get_wordlist


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_wordlist_and_known_bip39_vector(self):
        words = get_wordlist()
        self.assertEqual(len(words), 2048)
        self.assertEqual(words[0], "abandon")
        self.assertEqual(words[-1], "zoo")
        with patch("app.secrets.token_bytes", return_value=b"\0" * 16):
            self.assertEqual(generate_phrase(words), "abandon " * 11 + "about")

    def test_health_and_home(self):
        self.assertEqual(self.client.get("/health").data, b"ok\n")
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_download(self):
        response = self.client.post("/", data={"count": "2"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("bip39_2_phrases.txt", response.headers["Content-Disposition"])
        self.assertEqual(len(response.data.decode().strip().splitlines()), 2)

    def test_invalid_counts(self):
        for count in ("not-a-number", "0", "100001"):
            with self.subTest(count=count):
                self.assertEqual(self.client.post("/", data={"count": count}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
