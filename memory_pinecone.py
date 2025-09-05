import os
import time
import uuid
import logging
from typing import List, Dict, Any, Tuple

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)

BOT_ID = os.getenv("BOT_ID", "psychologist")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")  
EMBED_TRUNCATE_CHARS = int(os.getenv("EMBED_TRUNCATE_CHARS", "4000"))
DIMENSION = int(os.getenv("DIMENSION", "1536"))

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "psychologist-memory")

RECENT_TAU_SEC = int(os.getenv("RECENT_TAU_SEC", str(6 * 3600)))  
RECENCY_BIAS = float(os.getenv("RECENCY_BIAS", "0.35"))           

_oa = OpenAI()  

_pc = Pinecone(api_key=PINECONE_API_KEY)
_existing = [i.name for i in _pc.list_indexes()]
if PINECONE_INDEX_NAME not in _existing:
    _pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
    )
_index = _pc.Index(PINECONE_INDEX_NAME)

def _now() -> float:
    return time.time()

def _embed_text(text: str):
    if not isinstance(text, str) or not text.strip():
        return None
    payload = text if len(text) <= EMBED_TRUNCATE_CHARS else (text[:EMBED_TRUNCATE_CHARS] + " …")
    try:
        resp = _oa.embeddings.create(model=EMBEDDING_MODEL, input=[payload])
        return resp.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding error: {e}", exc_info=True)
        return None

def _as_ts(meta_ts: Any) -> float:
    try:
        return float(meta_ts)
    except Exception:
        return 0.0

def _recency_weight(ts: float, now_ts: float) -> float:
    if ts <= 0:
        return 0.0
    age = max(0.0, now_ts - ts)
    return pow(2.718281828, -age / max(1.0, RECENT_TAU_SEC))

def save_message(user_id: str, chat_id: str, message: str, role: str) -> bool:
    if not isinstance(message, str) or len(message.strip()) < 2:
        return False

    emb = _embed_text(message)
    if emb is None:
        return False

    ts = str(_now())
    meta = {
        "bot_id": BOT_ID,
        "chat_id": str(chat_id),
        "user_id": str(user_id),
        "role": role,
        "text": message,
        "timestamp": ts,
    }
    vector_id = f"{chat_id}-{int(float(ts)*1000)}-{uuid.uuid4().hex[:8]}"
    try:
        _index.upsert(vectors=[(vector_id, emb, meta)])
        return True
    except Exception as e:
        logger.error(f"Pinecone upsert error: {e}", exc_info=True)
        return False

def get_relevant_history(
    chat_id: str,
    query: str,
    top_k: int = 8,
    max_chars: int = 4000,
    min_score: float = 0.3,
) -> List[Dict[str, Any]]:
    emb = _embed_text(query if isinstance(query, str) else "")
    if emb is None:
        return []

    try:
        raw_k = max(top_k * 3, 24)
        res = _index.query(
            vector=emb,
            filter={"bot_id": BOT_ID, "chat_id": str(chat_id)},
            top_k=raw_k,
            include_metadata=True,
        )

        now_ts = _now()
        scored: List[Tuple[float, float, Dict[str, Any]]] = []
        for m in res.get("matches", []):
            score = float(m.get("score") or 0.0)
            if score < min_score:
                continue
            meta = (m.get("metadata") or {})
            role = meta.get("role")
            text = meta.get("text")
            ts = _as_ts(meta.get("timestamp"))
            if role in ("user", "assistant") and text:
                rec = _recency_weight(ts, now_ts)
                final = (1.0 - RECENCY_BIAS) * score + RECENCY_BIAS * rec
                scored.append((final, ts, {"role": role, "content": text, "ts": ts}))

        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = scored[:top_k]
        chosen.sort(key=lambda x: x[1])

        history, used = [], 0
        for _, _, item in chosen:
            c = item["content"]
            if used + len(c) > max_chars:
                if used == 0:
                    history.append({"role": item["role"], "content": c[:max_chars]})
                break
            history.append({"role": item["role"], "content": c})
            used += len(c)
        return history
    except Exception as e:
        logger.error(f"Pinecone relevant-history error: {e}", exc_info=True)
        return []

def get_recent_history(chat_id: str, limit: int = 3) -> List[Dict[str, Any]]:
    try:
        res = _index.query(
            vector=[0.0] * DIMENSION,  
            filter={"bot_id": BOT_ID, "chat_id": str(chat_id)},
            top_k=max(300, limit * 20),
            include_metadata=True,
        )
        items: List[Tuple[float, Dict[str, Any]]] = []
        for m in res.get("matches", []):
            meta = (m.get("metadata") or {})
            role, text = meta.get("role"), meta.get("text")
            ts = _as_ts(meta.get("timestamp"))
            if role in ("user", "assistant") and text:
                items.append((ts, {"role": role, "content": text}))
        items.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in items[:limit]]
    except Exception as e:
        logger.error(f"Pinecone recent-history error: {e}", exc_info=True)
        return []

def get_recent_user_messages(chat_id: str, limit: int = 3) -> List[Dict[str, Any]]:
    try:
        res = _index.query(
            vector=[0.0] * DIMENSION,
            filter={"bot_id": BOT_ID, "chat_id": str(chat_id), "role": "user"},
            top_k=max(1000, limit * 50),
            include_metadata=True,
        )
        items: List[Tuple[float, Dict[str, Any]]] = []
        for m in res.get("matches", []):
            meta = (m.get("metadata") or {})
            text = meta.get("text")
            ts = _as_ts(meta.get("timestamp"))
            if text:
                items.append((ts, {"role": "user", "content": text}))
        items.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in items[:limit]]
    except Exception as e:
        logger.error(f"Pinecone recent-user error: {e}", exc_info=True)
        return []

def clear_memory(chat_id: str) -> bool:
    try:
        _index.delete(filter={"bot_id": BOT_ID, "chat_id": str(chat_id)})
        return True
    except Exception as e:
        logger.error(f"Pinecone clear error: {e}", exc_info=True)
        return False
