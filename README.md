# 💚 AI Emotional Support Telegram Bot

An empathetic, multilingual emotional-support assistant for Telegram — powered by **OpenAI GPT-4.1-mini**, **Pinecone v2** memory, and **python-telegram-bot**.

📬 Try it: [@margii4_bot](https://t.me/margii4_bot)  
👤 Author: Margarita Viviers • margaritaviviers@gmail.com • [GitHub @Margii4](https://github.com/Margii4)

> ⚠️ This bot is **not** a licensed therapist. It offers **emotional support only** — and gently encourages users to seek help from mental health professionals if needed.

---

## 🌟 Features

- 🌍 **Multilingual:** English, Italian, Russian (auto-detect)  
- 💬 **Emotionally intelligent** replies — empathetic, validating, non-judgmental  
- 🧠 **Contextual memory** (Pinecone v2): remembers previous messages per user  
- 🧹 Commands to **view & clear memory**  
- ❌ **No diagnosis, no advice**: strictly supportive, not medical  
- 🤖 Powered by GPT-4.1-mini + `text-embedding-ada-002`  
- 🐳 Docker-ready deployment

---

## 🛠 Stack

| Component           | Used For                         |
|--------------------|----------------------------------|
| `python-telegram-bot` | Telegram Bot API               |
| `openai`            | GPT & embeddings                |
| `pinecone-client`   | Vector memory (user-specific)   |
| `.env`              | Secrets management              |
| `Docker` + `Compose`| Local deployment                |

---

## 🚀 Getting Started

### 🧪 A. Run Locally (no Docker)

1. **Clone the repo**:
   ```bash
   git clone https://github.com/Margii4/emotional-support-bot.git
   cd emotional-support-bot

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file** from the template:

   ```bash
   cp .env.example .env
   # Fill in your Telegram token, OpenAI key, Pinecone key etc.
   ```

5. **Run the bot**:

   ```bash
   python psychologist_bot.py
   ```

---

### 🐳 B. Run with Docker

> Requires Docker + Docker Compose installed

1. **Build and run**:

   ```bash
   docker compose up --build
   ```

2. To follow logs:

   ```bash
   docker compose logs -f
   ```

📝 The bot uses **polling**, so no public URL or webhook is required.

---

## 📂 Project Structure

```
emotional-support-bot/
├── psychologist_bot.py       # main Telegram logic
├── memory_pinecone.py        # vector memory logic (save/query/delete)
├── Dockerfile                # Docker build file
├── docker-compose.yml        # Compose file
├── requirements.txt
├── .env.example              # Template for environment variables
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
PINECONE_INDEX_NAME=psychologist-memory
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

---

## 🧠 Memory System

* Vector store: **Pinecone v2**
* For each user message, bot saves:

  * `user_id`
  * `role` (user/assistant)
  * `message`
  * `timestamp`
* At reply time, bot retrieves **most relevant past messages** from memory (filtered by `user_id`).
* You can type:

  * **"My recent queries"** — to see what's stored
  * **"Clear my memory"** — to delete only **your** history

---

## 🤖 Commands

| Command             | Description                              |
| ------------------- | ---------------------------------------- |
| `/start`            | Starts interaction                       |
| `What can you do?`  | Shows bot's capabilities                 |
| `My recent queries` | Shows user's message history from memory |
| `Clear my memory`   | Deletes user's memory from Pinecone      |
| `Change language`   | Lets user manually choose a language     |

---

## 🧾 Notes

* System prompts are separated by language (EN / RU / IT)
* Language is **auto-detected**, but can be **manually changed**
* This bot provides **emotional support only**. No diagnoses, therapy, or health advice.

---

## 👩‍💻 Author

Margarita Viviers — AI & Prompt Engineer
📬 [margaritaviviers@gmail.com](mailto:margaritaviviers@gmail.com)
🌐 [GitHub @Margii4](https://github.com/Margii4)

💡 If you want to deploy a version of this bot for your company or team — reach out!

---

## 📌 License

MIT — free to use, modify, and deploy.
Just don't pretend it's a replacement for therapy 😉
