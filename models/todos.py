import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import Boolean
from models import base
from sqlalchemy import Column,DateTime, Integer, String,ForeignKey,Float,Enum,Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import pytz


class Todos(base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(String)
    due_date = Column(Date)
    status = Column(Enum("pending", "in_progress", "completed", name="status_enum"), default="pending")
    is_active = Column(Boolean,default=True)
    created_by = Column(String)
    modified_by = Column(String)
    created_date = Column(DateTime(timezone=False), server_default=func.now())
    modified_date = Column(DateTime(timezone=False), onupdate=func.now())
