from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from typing import List, Optional
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    key = Column(String(120), nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_pref"),)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class LLMCall(Base):
    __tablename__ = "llm_calls"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    model = Column(String(120), nullable=True)
    latency_ms = Column(Integer, nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


@dataclass
class Database:
    url: str

    def __post_init__(self) -> None:
        connect_args = {}
        if self.url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            if self.url.startswith("sqlite:///"):
                db_path = Path(self.url.replace("sqlite:///", ""))
                if db_path.parent:
                    db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(self.url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def init_db(self) -> None:
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def ensure_user(db: Database, user_id: str) -> None:
    with db.session() as session:
        existing = session.get(User, user_id)
        if not existing:
            session.add(User(id=user_id))


def save_chat_message(db: Database, user_id: str, role: str, content: str) -> None:
    with db.session() as session:
        session.add(ChatMessage(user_id=user_id, role=role, content=content))


def save_preference(db: Database, user_id: str, key: str, value: str) -> None:
    with db.session() as session:
        pref = (
            session.query(UserPreference)
            .filter(UserPreference.user_id == user_id, UserPreference.key == key)
            .one_or_none()
        )
        if pref:
            pref.value = value
        else:
            session.add(UserPreference(user_id=user_id, key=key, value=value))


def list_preferences(db: Database, user_id: str) -> List[UserPreference]:
    with db.session() as session:
        return (
            session.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .order_by(UserPreference.key.asc())
            .all()
        )


def load_recent_messages(db: Database, user_id: str, limit: int) -> List[dict]:
    if limit <= 0:
        return []
    with db.session() as session:
        rows = (
            session.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all())
    return [
        {"role": row.role, "content": row.content}
        for row in reversed(rows)]


def save_llm_call(
    db: Database,
    user_id: str,
    model: Optional[str],
    latency_ms: int,
    prompt_tokens: Optional[int],
    completion_tokens: Optional[int],
    total_tokens: Optional[int],
    status: str,
    error_message: Optional[str],) -> None:
    with db.session() as session:
        session.add(
            LLMCall(
                user_id=user_id,
                model=model,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                status=status,
                error_message=error_message,))


def get_llm_stats(db: Database) -> dict:
    with db.session() as session:
        total = session.query(LLMCall).count()
        errors = session.query(LLMCall).filter(LLMCall.status == "error").count()
        avg_latency = session.query(func.avg(LLMCall.latency_ms)).scalar() or 0
        avg_tokens = session.query(func.avg(LLMCall.total_tokens)).scalar() or 0

    return {
        "total_calls": total,
        "error_calls": errors,
        "error_rate": float(errors) / total if total else 0.0,
        "avg_latency_ms": float(avg_latency),
        "avg_total_tokens": float(avg_tokens)}
