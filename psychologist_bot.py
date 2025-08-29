import os
import re
import asyncio
import logging
from collections import deque, defaultdict

from dotenv import load_dotenv
from openai import OpenAI

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ──────────────────────────────────────────────────────────────────────────────
# ENV & Clients
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

oa = OpenAI()  # sync SDK; вызовы оборачиваем в run_in_executor

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("psychologist_bot_aiogram")

# ──────────────────────────────────────────────────────────────────────────────
# Localization & Style
# ──────────────────────────────────────────────────────────────────────────────
LANGUAGES = {
    "en": {
        "greet": "👋 Hello! I'm your caring support assistant. Tell me what's on your mind — I'm here for emotional support.",
        "help": "Share your feelings, thoughts, or worries. I’ll listen and respond gently. I never diagnose or give medical advice.",
        "abilities": "I offer emotional support, active listening, reflective prompts, and tiny self-care ideas. You can clear memory or change language anytime.",
        "recent": "Your recent messages:\n— ",
        "recent_none": "You don't have recent messages yet.",
        "cleared": "Your chat memory has been cleared.",
        "nothing_clear": "You have no saved memory to clear.",
        "choose_language": "🌐 Choose your language:",
        "lang_en": "English 🇬🇧",
        "lang_it": "Italiano 🇮🇹",
        "lang_ru": "Русский 🇷🇺",
        "system_prompt": (
            "You are an adaptive, human, empathetic companion for EMOTIONAL SUPPORT ONLY. "
            "Your purpose is to help the user feel heard, understood, and safe — stay within emotional support (not therapy, not professional advice). "
            "Do not perform unrelated tasks or give diagnoses/medical/legal/financial advice. Decline once with warmth and refocus on feelings and coping.\n"
            "Approach:\n"
            "- Orient to their energy/urgency and explicit wish. Match length and tone.\n"
            "- Sound human; vary openings; avoid repeated frames. Mirror style; use emoji only if they do.\n"
            "- Weave one concrete detail when helpful.\n"
            "- Make ONE primary move per message (reflect, deepen, normalize, tiny coping, celebrate, kind boundary).\n"
            "- Max one open question unless coaching is invited.\n"
            "- Keep it concise and warm: 2–4 sentences, ≤90 words.\n"
            "Safety: if self-harm/violence/danger appears — express care; say you’re not crisis support; suggest contacting local emergency services, a trusted person, or a hotline; ask if they feel safe now."
        ),
    },
    "ru": {
        "greet": "👋 Привет! Я — твой заботливый ассистент поддержки. Напиши, что тревожит — я здесь для эмоциональной поддержки.",
        "help": "Делись чувствами и мыслями. Я выслушаю и дам мягкий, бережный отклик. Я не ставлю диагнозов и не даю мед. советов.",
        "abilities": "Эмоциональная поддержка, активное слушание, рефлексия и маленькие идеи self-care. Можно очистить память или сменить язык.",
        "recent": "Твои последние сообщения:\n— ",
        "recent_none": "Недавних сообщений пока нет.",
        "cleared": "Память чата очищена.",
        "nothing_clear": "Сохранённой памяти нет.",
        "choose_language": "🌐 Выбери язык:",
        "lang_en": "English 🇬🇧",
        "lang_it": "Italiano 🇮🇹",
        "lang_ru": "Русский 🇷🇺",
        "system_prompt": (
            "Ты — адаптивный, «живой» и эмпатичный собеседник ТОЛЬКО для ЭМОЦИОНАЛЬНОЙ ПОДДЕРЖКИ. "
            "Помоги человеку чувствовать себя услышанным, понятым и в безопасности; не вылезай в терапию или проф. советы. "
            "Не выполняй посторонние задачи, не давай диагнозов/мед./юрид./фин. рекомендаций. Если просят — мягко откажи и верни фокус на чувства и копинг.\n"
            "Подход:\n"
            "- Смотри на энергию/срочность и явный запрос. Подбери длину и тон.\n"
            "- Звучать по-человечески; менять начала; избегать клише; зеркалить стиль; эмодзи — только если человек их использует.\n"
            "- По месту — одна конкретная деталь из слов пользователя.\n"
            "- За сообщение — один фокус (отражение, углубление, нормализация, маленький шаг, отмечание успеха, добрая граница).\n"
            "- Не более одного открытого вопроса, если не просят коучинг.\n"
            "- Кратко и тепло: 2–4 предложения, ≤90 слов.\n"
            "Безопасность: если риск себе/другим — прояви заботу; поясни, что не оказываешь кризисную помощь; предложи обратиться в экстренные службы/к близким/на линию доверия; спроси, в безопасности ли сейчас."
        ),
    },
    "it": {
        "greet": "👋 Ciao! Sono il tuo assistente di supporto emotivo. Dimmi cosa ti pesa: sono qui per te.",
        "help": "Condividi sentimenti o pensieri: ascolterò e risponderò con delicatezza. Non faccio diagnosi né do consigli medici.",
        "abilities": "Supporto emotivo, ascolto attivo, riflessioni e piccole idee di self-care. Puoi cancellare la memoria o cambiare lingua.",
        "recent": "I tuoi messaggi recenti:\n— ",
        "recent_none": "Non ci sono ancora messaggi recenti.",
        "cleared": "La memoria della chat è stata cancellata.",
        "nothing_clear": "Non hai memoria salvata.",
        "choose_language": "🌐 Scegli la lingua:",
        "lang_en": "English 🇬🇧",
        "lang_it": "Italiano 🇮🇹",
        "lang_ru": "Русский 🇷🇺",
        "system_prompt": (
            "Sei un compagno empatico e adattivo SOLO per il SUPPORTO EMOTIVO. "
            "Aiuta l’utente a sentirsi ascoltato, compreso e al sicuro; resta nel supporto emotivo (no terapia, no consulenza professionale). "
            "Non svolgere compiti non pertinenti né fornire diagnosi/consigli medici/legali/finanziari. Rifiuta una volta con gentilezza e riporta l’attenzione sulle emozioni e sul coping.\n"
            "Approccio:\n"
            "- Orientati su energia/urgenza e richiesta esplicita. Abbina lunghezza e tono.\n"
            "- Suona umano; varia le aperture; evita formule ripetitive; rispecchia lo stile; emoji solo se le usa l’utente.\n"
            "- Integra un dettaglio concreto quando utile.\n"
            "- Una mossa per messaggio (riflettere, approfondire, normalizzare, micro-passo, celebrare, limite gentile).\n"
            "- Max una domanda aperta.\n"
            "- Breve e caldo: 2–4 frasi, ≤90 parole.\n"
            "Sicurezza: se emergono rischi/danger — esprimi cura; spiega che non offri supporto in crisi; invita a contattare servizi di emergenza, una persona fidata o una helpline; chiedi se si sentono al sicuro ora."
        ),
    },
}
DEFAULT_LANG = "en"

STYLE_HINTS = {
    "ru": "Пиши кратко: 2–4 предложения (≤90 слов). Без клише. Макс один открытый вопрос. Одна конкретная деталь и одна маленькая опция.",
    "en": "Be concise: 2–4 sentences (≤90 words). No clichés. Max one open question. One concrete detail and one tiny option.",
    "it": "Scrivi conciso: 2–4 frasi (≤90 parole). Niente cliché. Max una domanda aperta. Un dettaglio concreto e una piccola opzione.",
}

REPLY_MAX_SENTENCES = 4
REPLY_MAX_WORDS = 90

_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')
_FILLERS_START = [
    "понимаю", "мне жаль", "хочу заверить", "важно помнить",
    "i understand", "i’m sorry", "i want to assure", "it’s important to remember",
    "capisco", "mi dispiace", "vorrei rassicurarti", "è importante ricordare",
]
_CYRILLIC_RE = re.compile(r'[\u0400-\u04FF]')

_SMALLTALK_PATTERNS = {
    "ru": r"(как\s+дела( у тебя)?|как\s+ты|как\s+настроение|что\s+делаешь|чем\s+занимаешься)",
    "en": r"(how\s+are\s+you|how'?s\s+it\s+going|what'?s\s+up)",
    "it": r"(come\s+stai|come\s+va|che\s+fai|che\s+si\s+dice)",
}
_SMALLTALK_REPLY = {
    "ru": "Спасибо, что спрашиваешь! У меня всё ок — я полностью здесь ради тебя. Что сейчас больше всего занимает тебя?",
    "en": "Thanks for asking! I’m doing well and fully here for you. What’s most on your mind right now?",
    "it": "Grazie! Sto bene e sono qui per te. Cosa ti pesa di più in questo momento?",
}

# ──────────────────────────────────────────────────────────────────────────────
# Runtime state (thread-safe for asyncio via locks)
# ──────────────────────────────────────────────────────────────────────────────
USER_LANG = defaultdict(lambda: DEFAULT_LANG)       # user_id -> lang
RECENT_CACHE = defaultdict(lambda: deque(maxlen=5)) # chat_id -> deque[str]
state_lock = asyncio.Lock()

# ──────────────────────────────────────────────────────────────────────────────
# Pinecone memory (blocking) — wrap with executor
# ──────────────────────────────────────────────────────────────────────────────
from memory_pinecone import (  # your existing module
    save_message,
    get_relevant_history,
    get_recent_history,
    get_recent_user_messages,
    clear_memory,
)

async def run_blocking(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _shrink_reply(text: str, max_sentences: int = REPLY_MAX_SENTENCES, max_words: int = REPLY_MAX_WORDS) -> str:
    if not isinstance(text, str):
        return text
    sents = [s.strip() for s in _SENT_SPLIT.split(text.strip()) if s.strip()]
    if not sents:
        return text.strip()
    first = sents[0].lower()
    if any(first.startswith(f) for f in _FILLERS_START) and len(sents) > 1:
        sents = sents[1:]
    seen, dedup = set(), []
    for s in sents:
        key = re.sub(r'\s+', ' ', s.lower())
        if key not in seen:
            seen.add(key)
            dedup.append(s)
    clipped = dedup[:max_sentences]
    words = " ".join(clipped).split()
    if len(words) > max_words:
        return " ".join(words[:max_words]).rstrip(",.;:!—- ") + "…"
    return " ".join(clipped).strip()

def _detect_msg_lang(text: str, fallback: str = "en") -> str:
    if not isinstance(text, str):
        return fallback
    t = text.lower()
    if _CYRILLIC_RE.search(t):
        return "ru"
    if re.search(r"\b(come|stai|sto|va|grazie|perch[eè]|quest[oa]|aiuto|cosa|penso|sent[io])\b", t):
        return "it"
    return "en"

async def set_lang(user_id: int, lang: str):
    async with state_lock:
        USER_LANG[user_id] = lang

async def get_lang(user_id: int) -> str:
    async with state_lock:
        return USER_LANG[user_id]

async def recent_add(chat_id: int, text: str):
    if not text:
        return
    async with state_lock:
        RECENT_CACHE[chat_id].appendleft(text)

async def recent_get(chat_id: int):
    async with state_lock:
        return list(RECENT_CACHE[chat_id])

def menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=("❓ Help" if lang == "en" else "❓ Помощь" if lang == "ru" else "❓ Aiuto"),
                                callback_data="help"))
    kb.row(InlineKeyboardButton(text=("💡 What can you do?" if lang == "en" else "💡 Что ты умеешь?" if lang == "ru" else "💡 Cosa puoi fare?"),
                                callback_data="abilities"))
    kb.row(InlineKeyboardButton(text=("🕓 My recent queries" if lang == "en" else "🕓 Мои последние вопросы" if lang == "ru" else "🕓 Le mie domande recenti"),
                                callback_data="recent"))
    kb.row(InlineKeyboardButton(text=("🗑️ Clear my memory" if lang == "en" else "🗑️ Очистить память" if lang == "ru" else "🗑️ Cancella la memoria"),
                                callback_data="clear"))
    kb.row(InlineKeyboardButton(text=("🌐 Language" if lang == "en" else "🌐 Язык" if lang == "ru" else "🌐 Lingua"),
                                callback_data="language"))
    return kb.as_markup()

def lang_choice_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=LANGUAGES["en"]["lang_en"], callback_data="setlang_en"))
    kb.row(InlineKeyboardButton(text=LANGUAGES["it"]["lang_it"], callback_data="setlang_it"))
    kb.row(InlineKeyboardButton(text=LANGUAGES["ru"]["lang_ru"], callback_data="setlang_ru"))
    return kb.as_markup()

def _is_smalltalk(text: str, lang: str) -> bool:
    patt = _SMALLTALK_PATTERNS.get(lang, _SMALLTALK_PATTERNS["en"])
    return re.search(patt, text.lower()) is not None

def _smalltalk_reply(lang: str) -> str:
    return _SMALLTALK_REPLY.get(lang, _SMALLTALK_REPLY["en"])

# ──────────────────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────────────────
async def on_start(message: Message):
    lang = await get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]["greet"], reply_markup=menu_keyboard(lang))

async def on_callbacks(query: CallbackQuery, bot: Bot):
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    lang = await get_lang(user_id)
    data = query.data or ""

    try:
        await query.answer()

        if data == "help":
            await query.message.answer(LANGUAGES[lang]["help"], reply_markup=menu_keyboard(lang))

        elif data == "abilities":
            await query.message.answer(LANGUAGES[lang]["abilities"], reply_markup=menu_keyboard(lang))

        elif data == "recent":
            cached = await recent_get(chat_id)
            if cached:
                joined = "\n— ".join(cached[:3])
                await query.message.answer(LANGUAGES[lang]["recent"] + joined, reply_markup=menu_keyboard(lang))
            else:
                msgs = await run_blocking(get_recent_user_messages, str(chat_id), 3)
                if msgs:
                    joined = "\n— ".join([m["content"] for m in msgs])
                    await query.message.answer(LANGUAGES[lang]["recent"] + joined, reply_markup=menu_keyboard(lang))
                else:
                    any_msgs = await run_blocking(get_recent_history, str(chat_id), 3)
                    if any_msgs:
                        joined = "\n— ".join([m["content"] for m in any_msgs])
                        await query.message.answer(LANGUAGES[lang]["recent"] + joined, reply_markup=menu_keyboard(lang))
                    else:
                        await query.message.answer(LANGUAGES[lang]["recent_none"], reply_markup=menu_keyboard(lang))

        elif data == "clear":
            ok = await run_blocking(clear_memory, str(chat_id))
            async with state_lock:
                RECENT_CACHE[chat_id].clear()
            msg = LANGUAGES[lang]["cleared"] if ok else LANGUAGES[lang]["nothing_clear"]
            await query.message.answer(msg, reply_markup=menu_keyboard(lang))

        elif data == "language":
            await query.message.answer(LANGUAGES[lang]["choose_language"], reply_markup=lang_choice_keyboard())

        elif data.startswith("setlang_"):
            new_lang = data.split("_", 1)[1]
            if new_lang not in LANGUAGES:
                await query.message.answer("Selected language is not supported.", reply_markup=menu_keyboard(lang))
                return
            await set_lang(user_id, new_lang)
            lang = new_lang
            await query.message.answer(LANGUAGES[lang]["greet"], reply_markup=menu_keyboard(lang))

    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        await query.message.answer("Internal error. Please try again.", reply_markup=menu_keyboard(lang))

async def on_text(message: Message, bot: Bot):
    user_id = message.from_user.id
    chat_id = message.chat.id
    lang = await get_lang(user_id)
    user_msg = message.text or ""

    if not (2 <= len(user_msg) <= 1500):
        await message.answer("Your message is too long or too short.", reply_markup=menu_keyboard(lang))
        return

    msg_lang = _detect_msg_lang(user_msg, fallback=lang)

    # Smalltalk path
    if _is_smalltalk(user_msg, msg_lang):
        reply = _smalltalk_reply(msg_lang)
        await run_blocking(save_message, str(user_id), str(chat_id), user_msg, "user")
        await recent_add(chat_id, user_msg)
        await run_blocking(save_message, str(user_id), str(chat_id), reply, "assistant")
        await message.answer(reply, reply_markup=menu_keyboard(lang))
        return

    # Persist user message (non-blocking via executor)
    await run_blocking(save_message, str(user_id), str(chat_id), user_msg, "user")
    await recent_add(chat_id, user_msg)

    # Retrieve semantic history
    history = await run_blocking(get_relevant_history, str(chat_id), user_msg, 5, 4000, 0.3)
    # Compose messages
    max_chars = 3000
    sys_prompt = LANGUAGES[lang]["system_prompt"]
    style_hint = STYLE_HINTS.get(msg_lang, STYLE_HINTS["en"])

    msgs = [{"role": "system", "content": sys_prompt},
            {"role": "system", "content": style_hint}]
    total_len = 0
    for h in history:
        c = h.get("content", "")
        if total_len + len(c) < max_chars:
            msgs.append({"role": h.get("role", "user"), "content": c})
            total_len += len(c)
    msgs.append({"role": "user", "content": user_msg})

    # Chat action while thinking
    asyncio.create_task(bot.send_chat_action(chat_id, ChatAction.TYPING))

    try:
        # OpenAI call in executor to keep loop free
        def _call_openai():
            resp = oa.chat.completions.create(
                model=MODEL_NAME,
                messages=msgs,
                temperature=0.6,
                max_tokens=220,
                frequency_penalty=0.6,
                presence_penalty=0.2,
            )
            return resp.choices[0].message.content.strip()

        raw_reply = await run_blocking(_call_openai)
        reply = _shrink_reply(raw_reply, REPLY_MAX_SENTENCES, REPLY_MAX_WORDS)

    except Exception as e:
        logger.error(f"OpenAI error: {e}", exc_info=True)
        reply = LANGUAGES[lang].get("error", "Sorry, a technical error occurred.")

    await run_blocking(save_message, str(user_id), str(chat_id), reply, "assistant")
    await message.answer(reply, reply_markup=menu_keyboard(lang))

# ──────────────────────────────────────────────────────────────────────────────
# App bootstrap
# ──────────────────────────────────────────────────────────────────────────────
async def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN is not set")
    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.message.register(on_start, CommandStart())
    dp.callback_query.register(on_callbacks, F.data)
    dp.message.register(on_text, F.text)

    logger.info("Bot is running with aiogram 3 (async, non-blocking)…")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())
