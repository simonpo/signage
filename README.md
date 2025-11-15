# 🖼️ Samsung Frame TV Signage

Automatically generates and uploads dynamic signage images to your Samsung Frame TV in Art Mode.

---

## 🚀 Features

- Real-time data from Home Assistant (Tesla battery/range)
- Live weather and stock quotes
- 4K image rendering with gradient backgrounds
- Secure uploads via [`samsungtvws`](https://github.com/NickWaterton/samsung-tv-ws-api) (supports 2024+ Samsung Frame)
- Secrets stored in `.env` (never committed to git)

---

## ⚡ Quick Start

1. **Clone the repository**
    ```bash
    git clone https://github.com/simonpo/signage.git
    cd signage
    ```

2. **Set up your environment**
    - Copy the `.env` example and add your configuration:
      ```bash
      cp .env.example .env
      nano .env       # Edit TV_IP, HA_URL, HA_TOKEN, API keys, entities, etc.
      ```

3. **Setup Virtual Environment and Install dependencies**
    ```bash
    python3 -m venv signage-env
    source signage-env/bin/activate
    pip install -r requirements.txt
    ```

4. **Generate & upload images**
    ```bash
    python generate_signage.py   # Generates new images in art_folder/
    python upload_to_frame.py    # Uploads images to your TV
    ```

---

## 📁 Project Structure

- `generate_signage.py` — Create images in `art_folder/`
- `upload_to_frame.py` — Upload images to Frame TV
- `.env` — Your configuration & secrets (**never commit!**)
- `.env.example` — Safe template to copy & edit
- `requirements.txt` — Locked Python dependencies

---

## 🔒 Security

- **Never commit your `.env` file!**
- Use long-lived HA tokens ([Profile → Long-Lived Access Tokens](https://www.home-assistant.io/docs/authentication/#long-lived-access-tokens))
- Rotate API keys regularly

---

## 🙏 Credits

- **Samsung TV WebSocket API**:  
  Thanks to [Nick Waterton’s `samsung-tv-ws-api` fork](https://github.com/NickWaterton/samsung-tv-ws-api) for critical support of 2024+ Frame TV Art Mode.

---
