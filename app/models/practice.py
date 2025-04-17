from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel, Base


class Practice(BaseModel, Base):
    """practice table"""

    __tablename__ = "practices"
    practice_name: Mapped[str] = mapped_column(String(128), nullable=False)
    practice_email: Mapped[str] = mapped_column(String(128), nullable=False)
    practice_phone_number: Mapped[str] = mapped_column(String(128), nullable=False)
    practice_address: Mapped[str] = mapped_column(String(128), nullable=False)
    admin_id: Mapped[str] = mapped_column(ForeignKey("admin.id"), nullable=False)

    admin = relationship("Admin", back_populates="practice")
    recall_groups = relationship("RecallGroup", back_populates="practice")
