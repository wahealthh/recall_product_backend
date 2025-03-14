# """Staff table in db"""

# from sqlalchemy import ForeignKey, String
# from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.models.base_model import BaseModel, Base


# class Staff(BaseModel, Base):
#     """staff table"""

#     __tablename__ = "staff"
#     first_name: Mapped[str] = mapped_column(String(128), nullable=False)
#     last_name: Mapped[str] = mapped_column(String(128), nullable=False)
#     practice_id: Mapped[str] = mapped_column(
#         ForeignKey("practice.id", ondelete="CASCADE"), nullable=False
#     )

#     practice = relationship("Practice", back_populates="staff")
