from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel, Base


class RecallGroup(BaseModel, Base):
    """RecallGroup table to store groups of patients for recalls"""

    __tablename__ = "recall_groups"
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    practice_id: Mapped[str] = mapped_column(ForeignKey("practices.id"), nullable=False)
    
    # Relationships
    practice = relationship("Practice", back_populates="recall_groups")
    patients = relationship("RecallPatient", back_populates="recall_group", cascade="all, delete-orphan") 