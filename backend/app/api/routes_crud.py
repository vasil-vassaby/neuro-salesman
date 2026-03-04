from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import KbArticle, Offer, ReplyTemplate
from ..schemas import (
    KbArticleCreate,
    KbArticleOut,
    KbArticleUpdate,
    OfferCreate,
    OfferOut,
    OfferUpdate,
    ReplyTemplateCreate,
    ReplyTemplateOut,
    ReplyTemplateUpdate,
)


router = APIRouter(prefix="/api")


def _get_db_session() -> Session:
    return SessionLocal()


# KB Articles CRUD


@router.get("/kb_articles", response_model=List[KbArticleOut])
def list_kb_articles() -> List[KbArticleOut]:
    session = _get_db_session()
    try:
        articles = session.query(KbArticle).all()
        return [KbArticleOut.from_orm(article) for article in articles]
    finally:
        session.close()


@router.post("/kb_articles", response_model=KbArticleOut)
def create_kb_article(payload: KbArticleCreate) -> KbArticleOut:
    session = _get_db_session()
    try:
        article = KbArticle(
            external_id=payload.external_id,
            title=payload.title,
            category=payload.category,
            content=payload.content,
            active=payload.active,
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        return KbArticleOut.from_orm(article)
    finally:
        session.close()


@router.get("/kb_articles/{article_id}", response_model=KbArticleOut)
def get_kb_article(article_id: str) -> KbArticleOut:
    session = _get_db_session()
    try:
        article = session.get(KbArticle, UUID(article_id))
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        return KbArticleOut.from_orm(article)
    finally:
        session.close()


@router.put("/kb_articles/{article_id}", response_model=KbArticleOut)
def update_kb_article(
    article_id: str,
    payload: KbArticleUpdate,
) -> KbArticleOut:
    session = _get_db_session()
    try:
        article = session.get(KbArticle, UUID(article_id))
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(article, field, value)
        session.commit()
        session.refresh(article)
        return KbArticleOut.from_orm(article)
    finally:
        session.close()


@router.delete("/kb_articles/{article_id}")
def delete_kb_article(article_id: str) -> dict:
    session = _get_db_session()
    try:
        article = session.get(KbArticle, UUID(article_id))
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        session.delete(article)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


# Offers CRUD


@router.get("/offers", response_model=List[OfferOut])
def list_offers() -> List[OfferOut]:
    session = _get_db_session()
    try:
        offers = session.query(Offer).all()
        return [OfferOut.from_orm(offer) for offer in offers]
    finally:
        session.close()


@router.post("/offers", response_model=OfferOut)
def create_offer(payload: OfferCreate) -> OfferOut:
    session = _get_db_session()
    try:
        offer = Offer(**payload.dict())
        session.add(offer)
        session.commit()
        session.refresh(offer)
        return OfferOut.from_orm(offer)
    finally:
        session.close()


@router.get("/offers/{offer_id}", response_model=OfferOut)
def get_offer(offer_id: str) -> OfferOut:
    session = _get_db_session()
    try:
        offer = session.get(Offer, UUID(offer_id))
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")
        return OfferOut.from_orm(offer)
    finally:
        session.close()


@router.put("/offers/{offer_id}", response_model=OfferOut)
def update_offer(
    offer_id: str,
    payload: OfferUpdate,
) -> OfferOut:
    session = _get_db_session()
    try:
        offer = session.get(Offer, UUID(offer_id))
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(offer, field, value)
        session.commit()
        session.refresh(offer)
        return OfferOut.from_orm(offer)
    finally:
        session.close()


@router.delete("/offers/{offer_id}")
def delete_offer(offer_id: str) -> dict:
    session = _get_db_session()
    try:
        offer = session.get(Offer, UUID(offer_id))
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")
        session.delete(offer)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


# Reply templates CRUD


@router.get("/reply_templates", response_model=List[ReplyTemplateOut])
def list_reply_templates() -> List[ReplyTemplateOut]:
    session = _get_db_session()
    try:
        templates = session.query(ReplyTemplate).all()
        return [ReplyTemplateOut.from_orm(tpl) for tpl in templates]
    finally:
        session.close()


@router.post("/reply_templates", response_model=ReplyTemplateOut)
def create_reply_template(payload: ReplyTemplateCreate) -> ReplyTemplateOut:
    session = _get_db_session()
    try:
        template = ReplyTemplate(**payload.dict())
        session.add(template)
        session.commit()
        session.refresh(template)
        return ReplyTemplateOut.from_orm(template)
    finally:
        session.close()


@router.get("/reply_templates/{template_id}", response_model=ReplyTemplateOut)
def get_reply_template(template_id: str) -> ReplyTemplateOut:
    session = _get_db_session()
    try:
        template = session.get(ReplyTemplate, UUID(template_id))
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")
        return ReplyTemplateOut.from_orm(template)
    finally:
        session.close()


@router.put("/reply_templates/{template_id}", response_model=ReplyTemplateOut)
def update_reply_template(
    template_id: str,
    payload: ReplyTemplateUpdate,
) -> ReplyTemplateOut:
    session = _get_db_session()
    try:
        template = session.get(ReplyTemplate, UUID(template_id))
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        session.commit()
        session.refresh(template)
        return ReplyTemplateOut.from_orm(template)
    finally:
        session.close()


@router.delete("/reply_templates/{template_id}")
def delete_reply_template(template_id: str) -> dict:
    session = _get_db_session()
    try:
        template = session.get(ReplyTemplate, UUID(template_id))
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")
        session.delete(template)
        session.commit()
        return {"ok": True}
    finally:
        session.close()

