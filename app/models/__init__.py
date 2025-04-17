from app.models.base_model import Base
from app.models.admin import Admin
from app.models.practice import Practice
from app.models.recall_group import RecallGroup
from app.models.recall_patient import RecallPatient

# This ensures all models are known to SQLAlchemy
__all__ = ['Base', 'Admin', 'Practice', 'RecallGroup', 'RecallPatient'] 