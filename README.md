# BIP-39 Phrase Generator (Render)

A small Flask app that generates valid BIP-39 12-word seed phrases and downloads them as a `.txt` file. The official English wordlist is bundled in `english.txt` so generation does not depend on a runtime network request.

## Deploy to Render

The repository includes a Render Blueprint (`render.yaml`). To deploy with it:

1. Push the branch you want to deploy to GitHub.
2. In the [Render dashboard](https://dashboard.render.com/), select **New** → **Blueprint** and connect this repository. Select the branch containing `render.yaml` if prompted.
3. Review the proposed `bip39-generator` web service and apply the Blueprint. Render will install `requirements.txt`, run Gunicorn bound to Render's `PORT`, and check `/health`.
4. Open the service URL shown by Render. `/health` should respond with `ok`, and the home page should show the generator.

Alternatively, choose **New** → **Web Service**, connect this repository, and select the branch you want to deploy. Use **Python** as the runtime, `pip install -r requirements.txt` as the build command, and `gunicorn --worker-class gthread --threads 4 --bind 0.0.0.0:${PORT:-10000} app:app` as the start command. Set the health check path to `/health`. A manually created Web Service does **not** automatically apply the settings in `render.yaml`.

If deploying from a feature branch, make sure Render is configured to deploy that branch; changing the GitHub default branch alone will not deploy these changes to an existing service.

## Local check

```sh
pip install -r requirements.txt
python -m unittest discover -s tests
PORT=5000 sh -c 'gunicorn --worker-class gthread --threads 4 --bind 0.0.0.0:${PORT:-10000} app:app'
```

Visit `http://localhost:5000/health` to check readiness, or `http://localhost:5000/` to generate a text file.

## Usage

Open the deployed URL, enter a positive number, and download the phrases as `bip39_N_phrases.txt`. There is no application-imposed maximum; the download streams in batches instead of buffering every phrase in memory. Extremely large downloads can still be interrupted by hosting, browser, or network time and resource limits.

## ⚠️ Security warning

**Do not use phrases from a hosted website for real funds.** Anyone who obtains a seed phrase can steal the wallet derived from it. For real crypto, use trusted wallet software offline and store your seed phrase securely. The bundled English wordlist comes from [bitcoin/bips, bip-0039/english.txt](https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt) (SHA-256: `2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda`).
