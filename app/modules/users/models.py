from datetime import datetime
from sqlalchemy import String, func, DateTime, CheckConstraint
from sqlalchemy import ForeignKey, Float, Boolean, text, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())