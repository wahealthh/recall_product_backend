from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.models.base_model import BaseModel, Base


class RecallPatient(BaseModel, Base):
    """RecallPatient table to store patient details for recall groups"""

    __tablename__ = "recall_patients"
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False)
    number: Mapped[str] = mapped_column(String(128), nullable=False)
    dob: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    recall_group_id: Mapped[str] = mapped_column(ForeignKey("recall_groups.id"), nullable=False)
    
    # Relationships
    recall_group = relationship("RecallGroup", back_populates="patients") 