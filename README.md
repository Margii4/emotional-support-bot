# 💚 AI Emotional Support Telegram Bot

An empathetic, multilingual emotional-support assistant for Telegram — powered by **OpenAI GPT-4.1-mini**, **Pinecone v2** memory, and **aiogram 3.x** (fully async, non-blocking).

📬 Try it: [@margii4_bot](https://t.me/margii4_bot)  
👤 Author: Margarita Viviers • margaritaviviers@gmail.com • [GitHub @Margii4](https://github.com/Margii4)

> ⚠️ This bot is **not** a licensed therapist. It offers **emotional support only** — and gently encourages users to seek help from mental health professionals if needed.

---

## 🌟 Features

- 🌍 **Multilingual:** English, Italian, Russian (auto-detect)
- 🤗 Emotionally intelligent replies — empathetic, validating, non-judgmental
- 🧠 **Contextual memory** via Pinecone v2 (user-specific)
- 💬 Menu options to view and clear memory
- 🔐 **No diagnosis, no advice** — strictly emotional support
- ⚡ Built with **async aiogram 3.x** for parallel, responsive interactions
- 🐳 Docker-ready for clean and fast deployment

---

## 🛠 Stack

| Component         | Used For                        |
|------------------|---------------------------------|
| `aiogram` 3.x     | Telegram bot API (async)        |
| `openai`         | GPT replies + embeddings         |
| `pinecone-client`| Vector memory (per user)         |
| `.env`           | API keys & config                |
| `Docker`         | Containerized deployment         |

---

## 🚀 Getting Started

### 🧪 Option A: Run Locally (no Docker)

1. **Clone the repo**
   ```bash
   git clone https://github.com/Margii4/emotional-support-bot.git
   cd emotional-support-bot

2. **Create virtual environment**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**

   ```bash
   cp .env.example .env
   # Then fill in your OpenAI key, Telegram token, etc.
   ```

5. **Run the bot**

   ```bash
   python psychologist_bot.py
   ```

---

### 🐳 Option B: Run with Docker

> Requires: Docker & Docker Compose

1. **Build and run**

   ```bash
   docker compose up -d --build
   ```

2. **Check logs**

   ```bash
   docker compose logs -f
   ```

💡 During development, you can mount your code:

```yaml
volumes:
  - ./:/app
```

🧠 The bot uses polling (no public URL or webhook needed).

---

## 📂 Project Structure

```
emotional-support-bot/
├── psychologist_bot.py       # main async bot logic
├── memory_pinecone.py        # vector DB handling
├── requirements.txt
├── .env.example              # environment variable template
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── .dockerignore
```

---

## ⚙️ Environment Variables (`.env`)

```env
# Telegram
TELEGRAM_TOKEN=your_telegram_token

# OpenAI
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4.1-mini

# Pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=psychologist-bot
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

---

## 🧠 Memory Logic

* Embedding model: `text-embedding-3-small` (configurable)
* Vector DB: Pinecone v2
* For each message:

  * saves `chat_id`, `user_id`, role, content
  * retrieves most relevant 3–5 items per response
* Auto-clearing per user supported

🔎 Commands:

* `My recent queries` → shows message history
* `Clear my memory` → removes memory from Pinecone
* `Change language` → switch manually

---

## 🤖 UI Flow

* `/start` launches welcome message + menu
* Users can type anything — bot responds with 2–4 sentence support
* No advice. No therapy. Only emotional acknowledgment and grounding.

---

## 🧾 Notes

* System prompts vary by language (EN / RU / IT)
* Language is **auto-detected**, but can be **changed manually**
* Async replies use `ChatAction.TYPING`
* `parse_mode=HTML` is set via `DefaultBotProperties` (aiogram ≥ 3.7+)

---

## 👩‍💻 Author

Margarita Viviers — AI & Prompt Engineer
📬 [margaritaviviers@gmail.com](mailto:margaritaviviers@gmail.com)
🔗 [GitHub @Margii4](https://github.com/Margii4)

---

## 📄 License

MIT — free to use, modify, and deploy.
Just don’t pretend it replaces therapy 😉


