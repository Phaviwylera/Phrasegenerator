# BIP-39 Phrase Generator (Render)

A tiny Flask app that generates valid BIP-39 12-word seed phrases and lets you download them as a `.txt` file.

## Deploy to Render

1. Push this folder to a GitHub repository.
2. Log in to [Render](https://render.com).
3. Click **New +** → **Web Service**.
4. Connect your GitHub repo and select this folder.
5. Render will detect `render.yaml` automatically, or you can set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
6. Deploy.

## Usage

Open the deployed URL, enter a number, and download the phrases as `bip39_N_phrases.txt`.

## ⚠️ Security warning

Phrases generated here are **not safe for real funds** unless you self-host this privately and generate them offline. Anyone who sees a phrase can steal the wallet derived from it. For real crypto, use your own wallet software to generate a seed phrase offline and write it down on paper/metal.
