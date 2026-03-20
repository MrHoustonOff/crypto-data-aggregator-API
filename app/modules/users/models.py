from datetime import datetime
import uuid
from sqlalchemy import String, func, DateTime, CheckConstraint
from sqlalchemy import ForeignKey, Float, Boolean, text, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import SmallInteger

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    api_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))

    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    target_price: Mapped[float] = mapped_column(
        Numeric(20, 8), CheckConstraint("target_price > 0"), nullable=False
    )
    condition: Mapped[str] = mapped_column(
        String(2), CheckConstraint("condition IN ('gt', 'lt')")
    )
    webhook_url: Mapped[str] = mapped_column(Text, nullable=False)

    triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    is_active: Mapped[bool] = mapped_column(server_default=text("true"), index=True)

    user: Mapped["User"] = relationship(back_populates="alerts")

    dispatch_logs: Mapped[list["DispatchLog"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )


class DispatchLog(Base):
    __tablename__ = "dispatch_log"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("alerts.id", ondelete="CASCADE"), index=True
    )

    attempt: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(10),
        CheckConstraint("status IN ('success', 'failed', 'pending')"),
        nullable=False,
    )

    response_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)

    dispatched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    alert: Mapped["Alert"] = relationship(back_populates="dispatch_logs")
