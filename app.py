import os
import secrets
import hashlib
from flask import Flask, request, render_template_string, Response, abort

app = Flask(__name__)

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
<script src="/static/address-export.js" defer></script>
<style>
  body { font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 48px auto; padding: 0 20px; }
  h1 { font-size: 1.5rem; margin-bottom: 16px; }
  form { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 24px; }
  input[type="number"] { padding: 10px; font-size: 1rem; width: 140px; }
  input[type="file"] { max-width: 100%; }
  input[type="text"] { padding: 10px; font-size: 1rem; width: min(100%, 440px); box-sizing: border-box; }
  section { border-top: 1px solid #ddd; padding-top: 16px; margin-top: 24px; }
  h2 { font-size: 1.2rem; }
  .note { color: #444; line-height: 1.5; }
  #export-status, #lookup-status { min-height: 1.5em; }
  button:disabled { opacity: 0.6; cursor: wait; }
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
    <input type="number" id="count" name="count" min="1" step="1" value="10" required>
    <button type="submit">Generate &amp; Download TXT</button>
  </form>
  <section aria-labelledby="address-title">
    <h2 id="address-title">Download public addresses from a phrase TXT file</h2>
    <p class="note">Select the TXT file downloaded above (one 12-word phrase per line). The smaller CSV contains only two unique addresses per valid phrase: one native SegWit Bitcoin address and one EVM (0x) address. Use the EVM address on Ethereum, BNB Smart Chain, or Base; balances are separate on each network. This does not check balances.</p>
    <form id="address-export-form">
      <label for="phrase-file">Phrase TXT file:</label>
      <input type="file" id="phrase-file" accept=".txt,text/plain" required>
      <button id="address-export-button" type="submit">Derive &amp; Download Addresses CSV</button>
    </form>
    <p id="export-status" role="status" aria-live="polite"></p>
    <p class="note">Address derivation happens entirely in your browser; the selected TXT file is never uploaded to the server. Invalid lines are skipped; valid CSV rows keep their original TXT line numbers. The CSV contains public addresses only, not recovery phrases or private keys. Large files may take longer than a minute.</p>
    <h2>Find a phrase in your TXT by public address</h2>
    <p class="note">Select your <strong>original phrase TXT</strong> above, then enter a BTC address or an Ethereum/BNB Smart Chain/Base address from the CSV. The browser checks the phrases in your file and downloads the first match as a sensitive TXT. It cannot recover words from an address alone, or from the addresses CSV without the original phrase TXT.</p>
    <form id="phrase-lookup-form">
      <label for="lookup-address">Public address:</label>
      <input type="text" id="lookup-address" placeholder="bc1q… or 0x…" autocomplete="off" spellcheck="false" required>
      <button id="phrase-lookup-button" type="submit">Find &amp; Download Matching Phrase</button>
    </form>
    <p id="lookup-status" role="status" aria-live="polite"></p>
  </section>
  <div class="warning">
    <strong>Security warning:</strong> These phrases are generated on demand. Do NOT use them for real cryptocurrency wallets unless you trust this deployment and generate them privately. Anyone who obtains a phrase can steal the associated funds. For real wallets, generate your seed phrase offline with your own wallet software. Do not import a real wallet's recovery phrase into this hosted site.
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

        if count < 1:
            abort(400, "Count must be at least 1")

        wordlist = get_wordlist()

        def phrase_chunks():
            remaining = count
            while remaining:
                batch_size = min(remaining, 256)
                yield "".join(generate_phrase(wordlist) + "\n" for _ in range(batch_size))
                remaining -= batch_size

        return Response(
            phrase_chunks(),
            mimetype="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="bip39_{count}_phrases.txt"',
                "Cache-Control": "no-store",
            },
        )

    return render_template_string(HTML_PAGE)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
