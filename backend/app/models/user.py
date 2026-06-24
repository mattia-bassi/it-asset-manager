from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, server_default="admin")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    is_permanently_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    person_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    person = relationship("Person", backref="user", uselist=False, lazy="select")
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
