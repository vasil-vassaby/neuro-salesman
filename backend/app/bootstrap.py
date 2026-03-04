import csv
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import yaml
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, check_connection, engine, init_pgvector_extension, session_scope
from .models import (
    KbArticle,
    KbEmbedding,
    LostReason,
    Offer,
    ReplyTemplate,
)


logger = logging.getLogger(__name__)


COMPLIANCE_RULES: Dict[str, object] = {}


def _load_csv(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(row)
    return rows


def _ensure_lost_reasons(session: Session) -> None:
    defaults: List[Tuple[str, str]] = [
        ("no_response", "Клиент перестал отвечать"),
        ("price_too_high", "Клиенту дорого"),
        ("not_relevant", "Не релевантно запросу"),
        ("went_to_other", "Ушел к другому специалисту"),
    ]
    created = 0
    for code, title in defaults:
        existing = session.execute(
            select(LostReason).where(LostReason.code == code),
        ).scalar_one_or_none()
        if existing is None:
            lost = LostReason(code=code, title=title)
            session.add(lost)
            created += 1
    if created:
        logger.info("Seeded %s lost reasons.", created)


def load_offers_seed(session: Session, seeds_dir: str) -> None:
    path = os.path.join(seeds_dir, "offers_seed.csv")
    if not os.path.exists(path):
        logger.warning("Offers seed file not found: %s", path)
        return
    rows = _load_csv(path)
    created = 0
    for row in rows:
        title = row.get("title") or ""
        if not title:
            continue
        existing = session.execute(
            select(Offer).where(Offer.title == title),
        ).scalar_one_or_none()
        if existing:
            continue
        tags_raw = row.get("tags") or ""
        tags = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]
        offer = Offer(
            title=title,
            description=row.get("description") or "",
            price_min=float(row["price_min"]) if row.get("price_min") else None,
            price_max=float(row["price_max"]) if row.get("price_max") else None,
            duration_minutes=int(row["duration_minutes"])
            if row.get("duration_minutes")
            else None,
            active=(row.get("active") or "true").lower() == "true",
            tags=tags,
        )
        session.add(offer)
        created += 1
    logger.info("Imported %s offers (idempotent).", created)


def load_kb_articles_seed(session: Session, seeds_dir: str) -> None:
    path = os.path.join(seeds_dir, "kb_articles_seed.csv")
    if not os.path.exists(path):
        logger.warning("KB articles seed file not found: %s", path)
        return
    rows = _load_csv(path)
    created = 0
    updated = 0
    for row in rows:
        title = row.get("title") or ""
        if not title:
            continue
        article = session.execute(
            select(KbArticle).where(KbArticle.title == title),
        ).scalar_one_or_none()
        content = row.get("content") or ""
        category = row.get("category") or "general"
        active = (row.get("active") or "true").lower() == "true"
        if article is None:
            article = KbArticle(
                title=title,
                category=category,
                content=content,
                active=active,
            )
            session.add(article)
            created += 1
        else:
            article.category = category
            article.content = content
            article.active = active
            updated += 1
    logger.info(
        "Seeded KB articles: created=%s updated=%s (idempotent).",
        created,
        updated,
    )


def load_reply_templates_seed(session: Session, seeds_dir: str) -> None:
    path = os.path.join(seeds_dir, "reply_templates_seed.csv")
    if not os.path.exists(path):
        logger.warning("Reply templates seed file not found: %s", path)
        return
    rows = _load_csv(path)
    created = 0
    updated = 0
    for row in rows:
        key = row.get("key") or ""
        if not key:
            continue
        template = session.execute(
            select(ReplyTemplate).where(ReplyTemplate.key == key),
        ).scalar_one_or_none()
        base_data = {
            "title": row.get("title") or "",
            "text": row.get("text") or "",
            "channel": row.get("channel") or None,
            "intent": row.get("intent") or "other",
            "risk_level": row.get("risk_level") or "low",
            "active": (row.get("active") or "true").lower() == "true",
        }
        if template is None:
            template = ReplyTemplate(key=key, **base_data)
            session.add(template)
            created += 1
        else:
            for field, value in base_data.items():
                setattr(template, field, value)
            updated += 1
    logger.info(
        "Seeded reply templates: created=%s updated=%s (idempotent).",
        created,
        updated,
    )


def load_compliance_rules(seeds_dir: str) -> None:
    global COMPLIANCE_RULES
    path = os.path.join(seeds_dir, "compliance_rules.json")
    if not os.path.exists(path):
        logger.warning("Compliance rules file not found: %s", path)
        COMPLIANCE_RULES = {}
        return
    try:
        with open(path, encoding="utf-8") as file:
            COMPLIANCE_RULES = json.load(file)
        logger.info("Compliance rules loaded.")
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse compliance rules: %s", exc)
        COMPLIANCE_RULES = {}


def _parse_front_matter(content: str) -> Tuple[Dict[str, object], str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    _, fm_text, body = parts
    try:
        meta = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, body.lstrip("\n")


def load_markdown_kb(session: Session, kb_dir: str) -> None:
    if not os.path.isdir(kb_dir):
        logger.warning("KB markdown directory not found: %s", kb_dir)
        return
    created = 0
    updated = 0
    session.flush()
    for name in os.listdir(kb_dir):
        if not name.lower().endswith(".md"):
            continue
        path = os.path.join(kb_dir, name)
        with open(path, encoding="utf-8") as file:
            raw = file.read()
        meta, body = _parse_front_matter(raw)
        external_id = str(meta.get("id") or "") or None
        title = meta.get("title") or os.path.splitext(name)[0]
        category = meta.get("category") or "general"
        active = bool(meta.get("active", True))
        article = None
        if external_id:
            article = session.execute(
                select(KbArticle).where(KbArticle.external_id == external_id),
            ).scalar_one_or_none()
            if article is None:
                article = session.execute(
                    select(KbArticle).where(KbArticle.title == title),
                ).scalar_one_or_none()
        else:
            article = session.execute(
                select(KbArticle).where(KbArticle.title == title),
            ).scalar_one_or_none()
        if article is None:
            article = KbArticle(
                external_id=external_id,
                title=title,
                category=category,
                content=body,
                active=active,
            )
            session.add(article)
            created += 1
        else:
            article.external_id = external_id
            article.category = category
            article.content = body
            article.active = active
            article.updated_at = datetime.utcnow()
            updated += 1
    logger.info(
        "Loaded markdown KB: created=%s updated=%s (idempotent).",
        created,
        updated,
    )


def _build_embedding_for_text(text: str) -> Optional[List[float]]:
    if not settings.openai_api_key:
        return None
    try:
        import httpx

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
        }
        payload = {
            "input": text,
            "model": settings.embedding_model,
        }
        with httpx.Client(base_url=settings.openai_base_url, timeout=30.0) as client:
            response = client.post("/embeddings", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            vector = data["data"][0]["embedding"]
            return vector
    except Exception as exc:
        logger.error("Failed to build embedding: %s", exc)
        return None


def build_kb_embeddings(session: Session) -> None:
    if not settings.rag_enabled:
        logger.info("RAG is disabled; skipping embeddings.")
        return
    try:
        articles = session.execute(select(KbArticle).where(KbArticle.active.is_(True)))
        count = 0
        for article in articles.scalars():
            vector_obj = session.get(KbEmbedding, article.id)
            needs_update = False
            if vector_obj is None:
                needs_update = True
            if not needs_update:
                continue
            embedding = _build_embedding_for_text(article.content)
            if embedding is None:
                continue
            if vector_obj is None:
                vector_obj = KbEmbedding(
                    article_id=article.id,
                    embedding=embedding,
                )
                session.add(vector_obj)
            else:
                vector_obj.embedding = embedding
                vector_obj.updated_at = datetime.utcnow()
            count += 1
        logger.info("Built/updated embeddings for %s articles.", count)
    except SQLAlchemyError as exc:
        logger.error("Failed to build embeddings: %s", exc)


def run_bootstrap() -> None:
    logger.info("Starting bootstrap...")
    check_connection()
    init_pgvector_extension()
    Base.metadata.create_all(bind=engine)
    seeds_dir = "/app/seeds"
    kb_dir = settings.kb_md_dir
    with session_scope() as session:
        _ensure_lost_reasons(session)
        load_offers_seed(session, seeds_dir)
        load_kb_articles_seed(session, seeds_dir)
        load_reply_templates_seed(session, seeds_dir)
        load_markdown_kb(session, kb_dir)
        build_kb_embeddings(session)
    load_compliance_rules(seeds_dir)
    logger.info("Bootstrap finished.")

