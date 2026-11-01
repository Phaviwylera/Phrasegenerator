import os
import io
import secrets
import hashlib
from flask import Flask, request, render_template_string, send_file, abort

app = Flask(__name__)

MAX_COUNT = 100000  # safety cap so one request can't crash the server
_wordlist = None


def get_wordlist():
    """Load the official BIP-39 English wordlist (2048 words)."""
    global _wordlist
    if _wordlist is not None:
        return _wordlist

    local_path = os.path.join(os.path.dirname(__file__), "english.txt")
    with open(local_path, "r", encoding="utf-8") as f:
        words = f.read().split()

    if len(words) != 2048:
        raise RuntimeError(f"Expected 2048 BIP-39 words, got {len(words)}")
    _wordlist = words
    return _wordlist


def generate_phrase(wordlist):
    """Generate one valid BIP-39 12-word mnemonic with correct checksum."""
    entropy = secrets.token_bytes(16)  # 128 bits -> 12 words
    digest = hashlib.sha256(entropy).digest()
    entropy_bits = "".join(format(b, "08b") for b in entropy)
    checksum_bits = format(digest[0], "08b")[:4]  # 4-bit checksum
    combined = entropy_bits + checksum_bits  # 132 bits total

    words = []
    for i in range(0, 132, 11):
        chunk = combined[i : i + 11]
        index = int(chunk, 2)
        words.append(wordlist[index])
    return " ".join(words)


HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BIP-39 Phrase Generator</title>
<style>
  body { font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 48px auto; padding: 0 20px; }
  h1 { font-size: 1.5rem; margin-bottom: 16px; }
  form { display: flex; gap: 8px; align-items: center; margin-bottom: 24px; }
  input[type="number"] { padding: 10px; font-size: 1rem; width: 140px; }
  button { padding: 10px 20px; font-size: 1rem; cursor: pointer; background: #0066cc; color: white; border: none; border-radius: 6px; }
  button:hover { background: #0052a3; }
  .warning { background: #fff3cd; border: 1px solid #ffd299; color: #7a5a00; padding: 12px; border-radius: 6px; margin-top: 24px; font-size: 0.9rem; }
  .warning strong { color: #856404; }
</style>
</head>
<body>
  <h1>BIP-39 12-Word Phrase Generator</h1>
  <form method="post">
    <label for="count">Number of phrases:</label>
    <input type="number" id="count" name="count" min="1" max="{{ max_count }}" value="10" required>
    <button type="submit">Generate &amp; Download TXT</button>
  </form>
  <div class="warning">
    <strong>Security warning:</strong> These phrases are generated on demand. Do NOT use them for real cryptocurrency wallets unless you trust this deployment and generate them privately. Anyone who obtains a phrase can steal the associated funds. For real wallets, generate your seed phrase offline with your own wallet software.
  </div>
</body>
</html>
"""


@app.get("/health")
def health():
    get_wordlist()
    return "ok\n"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            count = int(request.form.get("count", "0"))
        except (TypeError, ValueError):
            abort(400, "Invalid count")

        if count < 1 or count > MAX_COUNT:
            abort(400, f"Count must be between 1 and {MAX_COUNT}")

        wordlist = get_wordlist()
        lines = [generate_phrase(wordlist) for _ in range(count)]
        content = "\n".join(lines) + "\n"

        buf = io.BytesIO(content.encode("utf-8"))
        buf.seek(0)
        return send_file(
            buf,
            mimetype="text/plain",
            as_attachment=True,
            download_name=f"bip39_{count}_phrases.txt",
        )

    return render_template_string(HTML_PAGE, max_count=MAX_COUNT)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
