#!/usr/bin/env python3

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel, Base


class Admin(BaseModel, Base):
    """admin table"""

    __tablename__ = "admin"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Change to back_populates without foreign_keys
    practice = relationship("Practice", back_populates="admin")
