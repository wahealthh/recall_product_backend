from app.models.base_model import Base
from app.models.admin import Admin
from app.models.practice import Practice

# This ensures all models are known to SQLAlchemy
__all__ = ['Base', 'Admin', 'Practice'] 