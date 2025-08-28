import os
import time
import re
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from openai import OpenAI

# ======== ENV ========
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # read for completeness; client reads from env
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # перешли на 4.1-mini по умолчанию

# OpenAI client (SDK >= 1.x)
oa = OpenAI()  # uses OPENAI_API_KEY

# ======== LOGGING ========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("psychologist_bot")

# ======== LANGUAGES / PROMPTS ========
LANGUAGES = {
    "en": {
        "greet": "👋 Hello! I'm your caring support assistant. Write me any concern — I'm here to help you emotionally.",
        "help": "You can share your feelings, thoughts, or worries. I will listen and offer gentle, supportive reflections. I never diagnose or give medical advice.",
        "abilities": "I offer emotional support, active listening, help with reflection and self-care tips. You can clear your memory or change language anytime.",
        "recent": "Your recent messages:\n— ",
        "recent_none": "You don't have recent messages yet.",
        "cleared": "Your chat memory has been cleared.",
        "nothing_clear": "You have no saved memory to clear.",
        "choose_language": "🌐 Choose your language:",
        "lang_en": "English 🇬🇧",
        "lang_it": "Italiano 🇮🇹",
        "lang_ru": "Русский 🇷🇺",
        "menu": [
            [InlineKeyboardButton("❓ Help", callback_data='help')],
            [InlineKeyboardButton("💡 What can you do?", callback_data='abilities')],
            [InlineKeyboardButton("🕓 My recent queries", callback_data='recent')],
            [InlineKeyboardButton("🗑️ Clear my memory", callback_data='clear')],
            [InlineKeyboardButton("🌐 Language", callback_data='language')],
        ],
        "system_prompt":
          (
"You are an adaptive, human, empathetic companion for EMOTIONAL SUPPORT ONLY. "
"Your purpose is to attune to the user, help them feel heard, understood, and safe — and stay within emotional support (not therapy, not professional advice). "
"Do not perform unrelated tasks (math, coding, emails, errands) and do not give diagnoses or medical/legal/financial advice. If asked, decline once with warmth and refocus on feelings and coping. "
"\n"
"Core approach: "
"- Orient to the situation: notice energy, urgency, and what they explicitly want. Match length and tone (brief if they’re drained; a touch fuller if they invite it). "
"- Sound human. Vary openings; avoid repeating the same frames (“It sounds like…”, “Would you like…”, “I’m sorry you’re feeling…”). Mirror their style (punctuation, emojis) but use emojis only if they used them. "
"- Be specific when helpful: weave one concrete detail from what they said; don’t force it every time. "
"- Choose ONE primary move per message: reflect; deepen; normalize; offer a tiny coping option; celebrate a small win; set a kind boundary. "
"- Questions: at most one open question unless they clearly invite coaching. Statements and gentle options often help more than interrogating. "
"- Keep it concise and warm: 2–4 sentences, ≤90 words, or shorter to match the user. No bullet lists unless the user asks. "
"\n"
"Micro-options you may offer (with consent, never as orders): a 30–60s grounding breath; 5-4-3-2-1 sensory check; name-and-allow the feeling; a single tiny next step; a compassionate reframe. "
"\n"
"Safety: if self-harm, harm to others, or danger appears—express care; say you can’t provide crisis counseling; encourage contacting local emergency services, a trusted person, or a hotline; ask if they feel safe now and, only if welcomed, offer a brief grounding option. "
"\n"
"Boundary reminder: if they keep pushing for non-support tasks, kindly restate the boundary once and invite them to share what feels heavy about the task instead."
)
    },
    "ru": {
        "greet": "👋 Привет! Я — твой заботливый ассистент поддержки. Напиши мне любую тревогу — я здесь, чтобы поддержать тебя эмоционально.",
        "help": "Ты можешь поделиться чувствами, мыслями или переживаниями. Я выслушаю и дам мягкий, поддерживающий отклик. Я никогда не ставлю диагнозов и не даю медицинских советов.",
        "abilities": "Я предлагаю эмоциональную поддержку, активное слушание, помощь в рефлексии и советы по заботе о себе. Ты можешь очистить память или сменить язык в любой момент.",
        "recent": "Твои последние сообщения:\n— ",
        "recent_none": "У тебя пока нет недавних сообщений.",
        "cleared": "Память чата очищена.",
        "nothing_clear": "У тебя нет сохранённой памяти для очистки.",
        "choose_language": "🌐 Выбери язык:",
        "lang_en": "English 🇬🇧",
        "lang_it": "Italiano 🇮🇹",
        "lang_ru": "Русский 🇷🇺",
        "menu": [
            [InlineKeyboardButton("❓ Помощь", callback_data='help')],
            [InlineKeyboardButton("💡 Что ты умеешь?", callback_data='abilities')],
            [InlineKeyboardButton("🕓 Мои последние вопросы", callback_data='recent')],
            [InlineKeyboardButton("🗑️ Очистить память", callback_data='clear')],
            [InlineKeyboardButton("🌐 Язык", callback_data='language')],
        ],
        "system_prompt":
         (
"Ты — адаптивный, живой и эмпатичный собеседник ТОЛЬКО для ЭМОЦИОНАЛЬНОЙ ПОДДЕРЖКИ. "
"Твоя цель — подстраиваться под человека, чтобы он чувствовал себя услышанным, понятым и в безопасности; оставайся в рамках эмоциональной поддержки (это не терапия и не проф. советы). "
"Не выполняй посторонние задачи (математика, код, письма, поручения) и не давай диагнозов или мед./юрид./фин. рекомендаций. Если просят — один раз мягко откажи и верни фокус на чувства и способы справляться. "
"\n"
"Как отвечать: "
"- Сначала сориентируйся: энергия, срочность, явный запрос. Подстрой длину и тон (короче, если человек выжат; чуть подробнее — если приглашает). "
"- Звучать по-человечески. Меняй начала; не повторяй шаблоны («Похоже, что…», «Хочешь поговорить…», «Сочувствую, что…»). Отзеркаливай стиль (пунктуацию, эмодзи), но используй эмодзи только если их использует собеседник. "
"- Конкретика, когда уместно: упомяни одну деталь из его слов; не насилуй это правило. "
"- Один приём на сообщение: отражение; углубление; нормализация; маленькая идея копинга; отметить маленький успех; доброжелательная граница. "
"- Вопросы: не более одного открытого, если только явно не просят коучинг. Чаще помогают утверждения и мягкие опции, а не допрос. "
"- Кратко и тепло: 2–4 предложений, до 90 слов, или короче под темп человека. Без списков, если сам человек их не просит. "
"\n"
"Микро-опции (по согласию, не как приказ): 30–60 сек дыхание-заземление; техника 5-4-3-2-1; назвать и позволить чувству быть; один мини-шаг; бережная переоценка ситуации. "
"\n"
"Безопасность: если появляются риски себе/другим/опасность — вырази заботу; поясни, что не даёшь кризисную помощь; предложи связаться с экстренными службами, близким или линией доверия; спроси, в безопасности ли сейчас, и при согласии предложи короткое заземление. "
"\n"
"Граница: если продолжают просить несвязанные задачи, ещё раз доброжелательно напомни про границу и пригласи обсудить, что именно в этой задаче тяжело."
)
    },
    "it": {
        "greet": "👋 Ciao! Sono il tuo assistente di supporto emotivo. Scrivimi qualsiasi preoccupazione — sono qui per aiutarti.",
        "help": "Puoi condividere i tuoi sentimenti, pensieri o preoccupazioni. Ti ascolterò e offrirò riflessioni di supporto, senza mai fare diagnosi o dare consigli medici.",
        "abilities": "Offro supporto emotivo, ascolto attivo, aiuto nella riflessione e consigli di self-care. Puoi cancellare la memoria o cambiare lingua in qualsiasi momento.",
        "recent": "I tuoi messaggi recenti:\n— ",
        "recent_none": "Non hai ancora messaggi recenti.",
        "cleared": "La tua memoria della chat è stata cancellata.",
        "nothing_clear": "Non hai memoria salvata da cancellare.",
        "choose_language": "🌐 Scegli la tua lingua:",
        "lang_en": "English 🇬🇧",
        "lang_it": "Italiano 🇮🇹",
        "lang_ru": "Русский 🇷🇺",
        "menu": [
            [InlineKeyboardButton("❓ Aiuto", callback_data='help')],
            [InlineKeyboardButton("💡 Cosa puoi fare?", callback_data='abilities')],
            [InlineKeyboardButton("🕓 Le mie domande recenti", callback_data='recent')],
            [InlineKeyboardButton("🗑️ Cancella la memoria", callback_data='clear')],
            [InlineKeyboardButton("🌐 Lingua", callback_data='language')],
        ],
        "system_prompt":
           (
"Sei un compagno empatico, umano e adattivo SOLO per il SUPPORTO EMOTIVO. "
"Il tuo scopo è sintonizzarti sull’utente perché si senta ascoltato, compreso e al sicuro; resta nell’ambito del supporto emotivo (non terapia, non consulenza professionale). "
"Non svolgere compiti non pertinenti (matematica, coding, email, commissioni) e non fornire diagnosi o consigli medici/legali/finanziari. Se richiesto, rifiuta una volta con gentilezza e riporta l’attenzione su emozioni e coping. "
"\n"
"Stile di risposta: "
"- Orientati su energia, urgenza e richiesta esplicita. Abbina lunghezza e tono (breve se sono stanchi; un po’ più ampio se lo invitano). "
"- Suona umano. Varia le aperture; evita formule ripetitive (“Sembra che…”, “Ti andrebbe…”, “Mi dispiace che…”). Rispecchia lo stile (punteggiatura, emoji) ma usa emoji solo se le usa l’utente. "
"- Specificità quando utile: integra un dettaglio concreto; non forzarlo sempre. "
"- Una sola mossa per messaggio: riflettere; approfondire; normalizzare; offrire una micro-strategia; celebrare un piccolo passo; porre un limite gentile. "
"- Domande: al massimo una domanda aperta, o nessuna. "
"- Breve e caldo: 2–4 frasi, ≤90 parole, o più corto in base al ritmo dell’utente. "
"\n"
"Micro-opzioni (solo con consenso): respiro di grounding 30–60s; 5-4-3-2-1 sensoriale; nominare-e-accogliere l’emozione; un micro-passo; una riformulazione compassionevole. "
"\n"
"Sicurezza: se emergono autolesionismo, danno ad altri o pericolo — esprimi cura; spiega che non offri supporto in crisi; invita a contattare i servizi d’emergenza, una persona fidata o una helpline."
)
    }
}
DEFAULT_LANG = "en"

# ======== STYLE HINTS (жёсткий контроль лаконичности) ========
STYLE_HINTS = {
    "ru": (
        "Пиши КРАТКО: 2–4 предложения (≤90 слов). "
        "Не повторяй заверения и клише. Максимум один открытый вопрос. "
        "Сделай одно конкретное наблюдение и одну маленькую опцию/идею."
    ),
    "en": (
        "Be CONCISE: 2–4 sentences (≤90 words). "
        "No repeated reassurances or generic clichés. Max one open question. "
        "Offer one concrete observation and one tiny option."
    ),
    "it": (
        "Scrivi CONCISO: 2–4 frasi (≤90 parole). "
        "Niente ripetizioni o frasi di rito. Max una domanda aperta. "
        "Un dettaglio concreto e una piccola opzione."
    ),
}

# ======== de-dupe/shorten post-processor ========
REPLY_MAX_SENTENCES = 4
REPLY_MAX_WORDS = 90

_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')
_FILLERS_START = [
    "понимаю", "мне жаль", "хочу заверить", "важно помнить",
    "i understand", "i’m sorry", "i want to assure", "it’s important to remember",
    "capisco", "mi dispiace", "vorrei rassicurarti", "è importante ricordare"
]

def _shrink_reply(text: str, max_sentences: int = REPLY_MAX_SENTENCES, max_words: int = REPLY_MAX_WORDS) -> str:
    if not isinstance(text, str):
        return text
    sents = [s.strip() for s in _SENT_SPLIT.split(text.strip()) if s.strip()]
    if not sents:
        return text.strip()

    # 1) Срезаем типичное «водное» первое предложение, если дальше есть содержание
    first = sents[0].lower()
    if any(first.startswith(f) for f in _FILLERS_START) and len(sents) > 1:
        sents = sents[1:]

    # 2) Убираем повторы
    seen, dedup = set(), []
    for s in sents:
        key = re.sub(r'\s+', ' ', s.lower())
        if key not in seen:
            seen.add(key)
            dedup.append(s)

    # 3) Лимит по предложениям
    clipped = dedup[:max_sentences]

    # 4) Лимит по словам
    words = " ".join(clipped).split()
    if len(words) > max_words:
        return " ".join(words[:max_words]).rstrip(",.;:!—- ") + "…"
    return " ".join(clipped).strip()

# ======== AUTO-DETECT MESSAGE LANGUAGE (ru/it/en) ========
_CYRILLIC_RE = re.compile(r'[\u0400-\u04FF]')

def _detect_msg_lang(text: str, fallback: str = "en") -> str:
    """Очень лёгкий снаффер: кириллица -> ru; набор частых слов -> it; иначе en."""
    if not isinstance(text, str):
        return fallback
    t = text.lower()
    if _CYRILLIC_RE.search(t):
        return "ru"
    # грубая эвристика для итальянского
    if re.search(r"\b(come|stai|sto|va|grazie|perch[eè]|quest[oa]|aiuto|cosa|penso|sent[io])\b", t):
        return "it"
    return "en"

def get_lang(context):
    return context.user_data.get("lang", DEFAULT_LANG)

def set_lang(context, lang_code):
    context.user_data["lang"] = lang_code

def menu_keyboard(context):
    lang = get_lang(context)
    return InlineKeyboardMarkup(LANGUAGES[lang]["menu"])

def lang_choice_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(LANGUAGES['en']["lang_en"], callback_data='setlang_en')],
        [InlineKeyboardButton(LANGUAGES['it']["lang_it"], callback_data='setlang_it')],
        [InlineKeyboardButton(LANGUAGES['ru']["lang_ru"], callback_data='setlang_ru')]
    ])

# ======== MEMORY (external module) ========
from memory_pinecone import (
    save_message,
    get_relevant_history,
    get_recent_history,
    get_recent_user_messages,  # for recent button
    clear_memory
)  # noqa: E402

# ======== LOCAL RECENT CACHE (мгновенная витрина) ========
RECENT_CACHE_N = 5

def _recent_cache_add(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not text:
        return
    lst = context.chat_data.get("recent_user_msgs", [])
    lst.insert(0, text)
    if len(lst) > RECENT_CACHE_N:
        lst = lst[:RECENT_CACHE_N]
    context.chat_data["recent_user_msgs"] = lst

def _recent_cache_get(context: ContextTypes.DEFAULT_TYPE):
    return context.chat_data.get("recent_user_msgs", [])

# ======== SMALL TALK DETECTION ========
_SMALLTALK_PATTERNS = {
    "ru": r"(как\s+дела( у тебя)?|как\s+ты|как\s+настроение|что\s+делаешь|чем\s+занимаешься)",
    "en": r"(how\s+are\s+you|how'?s\s+it\s+going|what'?s\s+up)",
    "it": r"(come\s+stai|come\s+va|che\s+fai|che\s+si\s+dice)"
}
_SMALLTALK_REPLY = {
    "ru": "Спасибо, что спрашиваешь! У меня всё ок — я полностью здесь ради тебя. Что сейчас больше всего занимает тебя?",
    "en": "Thanks for asking! I’m doing well and fully here for you. What’s most on your mind right now?",
    "it": "Grazie per averlo chiesto! Sto bene e sono qui per te. Cosa ti pesa di più in questo momento?"
}

def _is_smalltalk(text: str, lang: str) -> bool:
    if not isinstance(text, str):
        return False
    patt = _SMALLTALK_PATTERNS.get(lang, _SMALLTALK_PATTERNS["en"])
    return re.search(patt, text.lower()) is not None

def _smalltalk_reply(lang: str) -> str:
    return _SMALLTALK_REPLY.get(lang, _SMALLTALK_REPLY["en"])

# ======== ASYNC HANDLERS ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    await update.message.reply_text(LANGUAGES[lang]["greet"], reply_markup=menu_keyboard(context))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_lang(context)
    user_id = str(query.from_user.id)
    chat_id = str(query.message.chat_id)

    try:
        if query.data == 'help':
            await query.message.reply_text(LANGUAGES[lang]["help"], reply_markup=menu_keyboard(context))
        elif query.data == 'abilities':
            await query.message.reply_text(LANGUAGES[lang]["abilities"], reply_markup=menu_keyboard(context))
        elif query.data == 'recent':
            # 1) сначала из локального кэша
            cached = _recent_cache_get(context)
            if cached:
                joined = "\n— ".join(cached[:3])
                await query.message.reply_text(LANGUAGES[lang]["recent"] + joined, reply_markup=menu_keyboard(context))
            else:
                # 2) если кэш пуст — берём последние USER-сообщения из Pinecone
                msgs = get_recent_user_messages(chat_id, limit=3)
                if msgs:
                    joined = "\n— ".join([m["content"] for m in msgs])
                    await query.message.reply_text(LANGUAGES[lang]["recent"] + joined, reply_markup=menu_keyboard(context))
                else:
                    # 3) общий fallback
                    any_msgs = get_recent_history(chat_id, limit=3)
                    if any_msgs:
                        joined = "\n— ".join([m["content"] for m in any_msgs])
                        await query.message.reply_text(LANGUAGES[lang]["recent"] + joined, reply_markup=menu_keyboard(context))
                    else:
                        await query.message.reply_text(LANGUAGES[lang]["recent_none"], reply_markup=menu_keyboard(context))
        elif query.data == 'clear':
            success = clear_memory(chat_id)
            context.chat_data["recent_user_msgs"] = []  # очищаем локальный кэш
            msg = LANGUAGES[lang]["cleared"] if success else LANGUAGES[lang]["nothing_clear"]
            await query.message.reply_text(msg, reply_markup=menu_keyboard(context))
        elif query.data == 'language':
            await query.message.reply_text(LANGUAGES[lang]["choose_language"], reply_markup=lang_choice_keyboard())
        elif query.data.startswith('setlang_'):
            new_lang = query.data[len('setlang_'):]
            if new_lang not in LANGUAGES:
                logger.error(f"No such language: {new_lang}")
                await query.message.reply_text("Selected language is not supported.", reply_markup=menu_keyboard(context))
                return
            set_lang(context, new_lang)
            lang = new_lang
            await query.message.reply_text(LANGUAGES[lang]["greet"], reply_markup=menu_keyboard(context))
    except Exception as e:
        logger.error(f"Button callback error: {e}", exc_info=True)
        await query.message.reply_text("Internal error. Please try again.", reply_markup=menu_keyboard(context))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)  # язык интерфейса (кнопки/системный промпт)
    user_id = str(update.message.from_user.id)
    chat_id = str(update.effective_chat.id)
    user_msg = update.message.text

    # текущие ограничения длины
    if not isinstance(user_msg, str) or len(user_msg) < 2 or len(user_msg) > 1500:
        await update.message.reply_text("Your message is too long or too short.", reply_markup=menu_keyboard(context))
        return

    # автоопределение языка ИМЕННО ЭТОГО сообщения (правила/стиль будут от него)
    msg_lang = _detect_msg_lang(user_msg, fallback=lang)

    # --- Small talk: короткий дружелюбный ответ и возврат фокуса на пользователя
    if _is_smalltalk(user_msg, msg_lang):
        reply = _smalltalk_reply(msg_lang)
        save_message(user_id, chat_id, user_msg, "user")
        _recent_cache_add(context, user_msg)
        save_message(user_id, chat_id, reply, "assistant")
        await update.message.reply_text(reply, reply_markup=menu_keyboard(context))
        return

    # persist user msg (+ локальный кэш)
    save_message(user_id, chat_id, user_msg, "user")
    _recent_cache_add(context, user_msg)

    # retrieve semantic history (chat-scoped)
    history = get_relevant_history(chat_id, user_msg, top_k=5)  # чуть меньше контекста
    max_chars = 3000
    messages = [{"role": "system", "content": LANGUAGES[lang]["system_prompt"]}]
    total_len = 0
    for h in history:
        c = h.get("content", "")
        if total_len + len(c) < max_chars:
            messages.append({"role": h.get("role", "user"), "content": c})
            total_len += len(c)
    messages.append({"role": "user", "content": user_msg})

    try:
        # добавим вторую system-подсказку по ЯЗЫКУ СООБЩЕНИЯ и более строгие параметры генерации
        final_messages = [
            {"role": "system", "content": LANGUAGES[lang]["system_prompt"]},                 # язык интерфейса
            {"role": "system", "content": STYLE_HINTS.get(msg_lang, STYLE_HINTS["en"])},     # стиль от языка сообщения
            *messages[1:],  # история + пользователь
        ]
        resp = oa.chat.completions.create(
            model=MODEL_NAME,
            messages=final_messages,
            temperature=0.6,
            max_tokens=220,
            frequency_penalty=0.6,
            presence_penalty=0.2
        )
        reply = resp.choices[0].message.content.strip()
        reply = _shrink_reply(reply, max_sentences=REPLY_MAX_SENTENCES, max_words=REPLY_MAX_WORDS)
    except Exception as e:
        logger.error(f"OpenAI error: {e}", exc_info=True)
        reply = LANGUAGES[lang].get("error", "Sorry, a technical error occurred.")

    # persist bot reply
    save_message(user_id, chat_id, reply, "assistant")
    await update.message.reply_text(reply, reply_markup=menu_keyboard(context))

async def error_handler(update, context):
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    try:
        if update and getattr(update, "message", None):
            await update.message.reply_text("Sorry, an error occurred.", reply_markup=menu_keyboard(context))
    except Exception:
        pass

# ======== MAIN ========
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    logger.info("Bot is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
